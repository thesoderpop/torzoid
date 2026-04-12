from __future__ import annotations

import queue
import time
from dataclasses import asdict
from typing import Any

from .store import ObjectRecord, TemporalTinyPointerStore


class PredictiveTemporalTinyPointerStore(TemporalTinyPointerStore):
    """
    Leaner scheduler that improves the baseline FIFO prefetcher without adding much RAM overhead.

    Improvements over the baseline scheduler:
    - deduplicated queued objects
    - priority queue instead of FIFO
    - replay budget to avoid saturating CPU / I/O
    - simple rank-based priority to favor the most likely next refs first
    """

    def __init__(
        self,
        db_path: str,
        *,
        max_hot_objects: int = 256,
        checkpoint_interval: int = 8,
        prefetch_fanout: int = 2,
        enable_prefetch: bool = True,
        prefetch_budget_per_sec: float = 150.0,
        prefetch_queue_limit: int = 1024,
    ) -> None:
        self.prefetch_budget_per_sec = max(1.0, float(prefetch_budget_per_sec))
        self.prefetch_queue_limit = max(8, int(prefetch_queue_limit))
        self._tokens = self.prefetch_budget_per_sec
        self._last_budget_ts = time.monotonic()
        self._pending: set[int] = set()
        super().__init__(
            db_path,
            max_hot_objects=max_hot_objects,
            checkpoint_interval=checkpoint_interval,
            prefetch_fanout=prefetch_fanout,
            enable_prefetch=enable_prefetch,
        )

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

    def _queue_prefetch(self, refs: list[int]) -> None:
        if self._prefetch_queue is None:
            return
        for rank, ref in enumerate(refs):
            if ref in self._hot or ref in self._pending:
                continue
            if len(self._pending) >= self.prefetch_queue_limit:
                break
            priority = rank
            self._pending.add(ref)
            self._stats.prefetch_requests += 1
            self._prefetch_queue.put((priority, time.monotonic(), ref))

    def _replenish_budget(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_budget_ts
        if elapsed <= 0:
            return
        self._tokens = min(self.prefetch_budget_per_sec, self._tokens + (elapsed * self.prefetch_budget_per_sec))
        self._last_budget_ts = now

    def _prefetch_worker(self) -> None:
        assert self._prefetch_queue is not None
        while not self._stop_event.is_set():
            self._replenish_budget()
            if self._tokens < 1.0:
                time.sleep(0.002)
                continue
            try:
                item = self._prefetch_queue.get(timeout=0.05)
            except queue.Empty:
                continue
            if item == -1:
                return
            _priority, _queued_at, object_id = item
            with self._lock:
                self._pending.discard(object_id)
                if object_id in self._hot:
                    continue
                try:
                    record = self._rebuild_object(object_id)
                except KeyError:
                    continue
                self._remember_hot(record)
                self._stats.prefetched += 1
                self._tokens = max(0.0, self._tokens - 1.0)

    def describe(self) -> dict[str, Any]:
        description = super().describe()
        description["scheduler"] = {
            "mode": "predictive",
            "pending_queue": len(self._pending),
            "prefetch_budget_per_sec": self.prefetch_budget_per_sec,
        }
        return description
