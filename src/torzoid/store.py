from __future__ import annotations

import json
import math
import queue
import sqlite3
import threading
import time
from collections import OrderedDict, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ObjectRecord:
    object_id: int
    kind: str
    payload: dict[str, Any]
    refs: list[int]
    version: int
    resident: bool = True


@dataclass(slots=True)
class StoreStats:
    reads: int = 0
    writes: int = 0
    hot_hits: int = 0
    cold_rebuilds: int = 0
    journal_replays: int = 0
    evictions: int = 0
    prefetched: int = 0
    prefetch_requests: int = 0


class TemporalTinyPointerStore:
    """
    Prototype object store that trades resident RAM for replay time.

    Core ideas:
    - Tiny pointers are represented as compact integer object IDs.
    - Only hot objects stay resident in the in-memory LRU cache.
    - Cold objects are reconstructed from checkpoints + journal replay.
    - Optional background prefetch walks neighboring refs.
    """

    def __init__(
        self,
        db_path: str | Path,
        *,
        max_hot_objects: int = 256,
        checkpoint_interval: int = 8,
        prefetch_fanout: int = 2,
        enable_prefetch: bool = True,
    ) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_hot_objects = max(1, max_hot_objects)
        self.checkpoint_interval = max(1, checkpoint_interval)
        self.prefetch_fanout = max(0, prefetch_fanout)
        self.enable_prefetch = enable_prefetch

        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._hot: OrderedDict[int, ObjectRecord] = OrderedDict()
        self._stats = StoreStats()
        self._write_versions: defaultdict[int, int] = defaultdict(int)
        self._prefetch_queue: queue.Queue[int] | None = queue.Queue() if enable_prefetch else None
        self._stop_event = threading.Event()
        self._prefetch_thread: threading.Thread | None = None

        self._initialize_db()
        self._load_versions()
        if enable_prefetch:
            self._prefetch_thread = threading.Thread(target=self._prefetch_worker, name="torzoid-prefetch", daemon=True)
            self._prefetch_thread.start()

    def close(self) -> None:
        self._stop_event.set()
        if self._prefetch_queue is not None:
            self._prefetch_queue.put(-1)
        if self._prefetch_thread is not None:
            self._prefetch_thread.join(timeout=1.0)
        self._conn.close()

    def __enter__(self) -> "TemporalTinyPointerStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _initialize_db(self) -> None:
        with self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS objects (
                    object_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    latest_version INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS checkpoints (
                    object_id INTEGER NOT NULL,
                    version INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    refs_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    PRIMARY KEY (object_id, version)
                );

                CREATE TABLE IF NOT EXISTS journal (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER NOT NULL,
                    version INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    refs_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_journal_object_version ON journal(object_id, version);
                CREATE INDEX IF NOT EXISTS idx_checkpoints_object_version ON checkpoints(object_id, version);
                """
            )

    def _load_versions(self) -> None:
        rows = self._conn.execute("SELECT object_id, latest_version FROM objects").fetchall()
        for row in rows:
            self._write_versions[int(row["object_id"])] = int(row["latest_version"])

    def create_object(self, *, kind: str, payload: dict[str, Any], refs: list[int] | None = None) -> int:
        refs = list(refs or [])
        now = time.time()
        with self._lock, self._conn:
            cursor = self._conn.execute(
                "INSERT INTO objects(kind, created_at, latest_version) VALUES (?, ?, 0)",
                (kind, now),
            )
            object_id = int(cursor.lastrowid)
            self._conn.execute(
                "INSERT INTO checkpoints(object_id, version, payload_json, refs_json, created_at) VALUES (?, 0, ?, ?, ?)",
                (object_id, self._dump(payload), self._dump(refs), now),
            )
            record = ObjectRecord(object_id=object_id, kind=kind, payload=dict(payload), refs=list(refs), version=0, resident=True)
            self._remember_hot(record)
            self._stats.writes += 1
            return object_id

    def update_object(
        self,
        object_id: int,
        *,
        payload: dict[str, Any] | None = None,
        refs: list[int] | None = None,
    ) -> ObjectRecord:
        with self._lock:
            current = self.get_object(object_id)
            next_payload = dict(current.payload if payload is None else payload)
            next_refs = list(current.refs if refs is None else refs)
            next_version = current.version + 1
            now = time.time()
            with self._conn:
                self._conn.execute(
                    "INSERT INTO journal(object_id, version, payload_json, refs_json, created_at) VALUES (?, ?, ?, ?, ?)",
                    (object_id, next_version, self._dump(next_payload), self._dump(next_refs), now),
                )
                self._conn.execute(
                    "UPDATE objects SET latest_version = ? WHERE object_id = ?",
                    (next_version, object_id),
                )
            self._write_versions[object_id] = next_version
            updated = ObjectRecord(
                object_id=object_id,
                kind=current.kind,
                payload=next_payload,
                refs=next_refs,
                version=next_version,
                resident=True,
            )
            if next_version % self.checkpoint_interval == 0:
                self._write_checkpoint(updated)
            self._remember_hot(updated)
            self._stats.writes += 1
            return updated

    def get_object(self, object_id: int) -> ObjectRecord:
        with self._lock:
            self._stats.reads += 1
            hot = self._hot.get(object_id)
            if hot is not None:
                self._stats.hot_hits += 1
                self._hot.move_to_end(object_id)
                if self.enable_prefetch:
                    self._queue_prefetch(hot.refs[: self.prefetch_fanout])
                return ObjectRecord(**asdict(hot))

            record = self._rebuild_object(object_id)
            self._remember_hot(record)
            if self.enable_prefetch:
                self._queue_prefetch(record.refs[: self.prefetch_fanout])
            return ObjectRecord(**asdict(record))

    def evict_object(self, object_id: int) -> bool:
        with self._lock:
            if object_id in self._hot:
                self._hot.pop(object_id)
                self._stats.evictions += 1
                return True
            return False

    def evict_all(self) -> None:
        with self._lock:
            evicted = len(self._hot)
            self._hot.clear()
            self._stats.evictions += evicted

    def list_hot_object_ids(self) -> list[int]:
        with self._lock:
            return list(self._hot.keys())

    def describe(self) -> dict[str, Any]:
        with self._lock:
            object_count = int(self._conn.execute("SELECT COUNT(*) FROM objects").fetchone()[0])
            journal_rows = int(self._conn.execute("SELECT COUNT(*) FROM journal").fetchone()[0])
            checkpoint_rows = int(self._conn.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0])
            ref_count = self._estimate_ref_count()
            tiny_pointer_bytes = self._tiny_pointer_bytes(object_count) * ref_count
            raw_pointer_bytes = 8 * ref_count
            return {
                "db_path": str(self.db_path),
                "objects": object_count,
                "hot_objects": len(self._hot),
                "journal_rows": journal_rows,
                "checkpoint_rows": checkpoint_rows,
                "stats": asdict(self._stats),
                "pointer_model": {
                    "refs": ref_count,
                    "raw_pointer_bytes": raw_pointer_bytes,
                    "tiny_pointer_bytes": tiny_pointer_bytes,
                    "estimated_pointer_savings_bytes": raw_pointer_bytes - tiny_pointer_bytes,
                },
            }

    def _estimate_ref_count(self) -> int:
        total = 0
        for row in self._conn.execute(
            """
            SELECT c.refs_json
            FROM checkpoints c
            JOIN (
                SELECT object_id, MAX(version) AS max_version
                FROM checkpoints
                GROUP BY object_id
            ) latest
            ON c.object_id = latest.object_id AND c.version = latest.max_version
            """
        ):
            total += len(self._load(row[0]))
        return total

    def _tiny_pointer_bytes(self, object_count: int) -> int:
        if object_count <= 1:
            return 1
        bits = max(1, math.ceil(math.log2(object_count + 1)))
        return max(1, math.ceil(bits / 8))

    def _rebuild_object(self, object_id: int) -> ObjectRecord:
        kind_row = self._conn.execute("SELECT kind FROM objects WHERE object_id = ?", (object_id,)).fetchone()
        if kind_row is None:
            raise KeyError(f"unknown object id {object_id}")

        checkpoint = self._conn.execute(
            "SELECT version, payload_json, refs_json FROM checkpoints WHERE object_id = ? ORDER BY version DESC LIMIT 1",
            (object_id,),
        ).fetchone()
        if checkpoint is None:
            raise RuntimeError(f"object {object_id} has no checkpoint")

        version = int(checkpoint["version"])
        payload = self._load(checkpoint["payload_json"])
        refs = self._load(checkpoint["refs_json"])

        journal_rows = self._conn.execute(
            "SELECT version, payload_json, refs_json FROM journal WHERE object_id = ? AND version > ? ORDER BY version ASC",
            (object_id, version),
        ).fetchall()
        for row in journal_rows:
            version = int(row["version"])
            payload = self._load(row["payload_json"])
            refs = self._load(row["refs_json"])
            self._stats.journal_replays += 1

        self._stats.cold_rebuilds += 1
        return ObjectRecord(
            object_id=object_id,
            kind=str(kind_row["kind"]),
            payload=payload,
            refs=list(refs),
            version=version,
            resident=True,
        )

    def _write_checkpoint(self, record: ObjectRecord) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO checkpoints(object_id, version, payload_json, refs_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (record.object_id, record.version, self._dump(record.payload), self._dump(record.refs), time.time()),
            )

    def _remember_hot(self, record: ObjectRecord) -> None:
        self._hot[record.object_id] = record
        self._hot.move_to_end(record.object_id)
        while len(self._hot) > self.max_hot_objects:
            self._hot.popitem(last=False)
            self._stats.evictions += 1

    def _queue_prefetch(self, refs: list[int]) -> None:
        if self._prefetch_queue is None:
            return
        for ref in refs:
            if ref in self._hot:
                continue
            self._stats.prefetch_requests += 1
            self._prefetch_queue.put(ref)

    def _prefetch_worker(self) -> None:
        assert self._prefetch_queue is not None
        while not self._stop_event.is_set():
            try:
                object_id = self._prefetch_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            if object_id == -1:
                return
            with self._lock:
                if object_id in self._hot:
                    continue
                try:
                    record = self._rebuild_object(object_id)
                except KeyError:
                    continue
                self._remember_hot(record)
                self._stats.prefetched += 1

    @staticmethod
    def _dump(value: Any) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _load(value: str) -> Any:
        return json.loads(value)
