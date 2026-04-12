from __future__ import annotations

import argparse
import gc
import json
import random
import tempfile
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from torzoid.store import ObjectRecord, TemporalTinyPointerStore


@dataclass(slots=True)
class ScenarioConfig:
    name: str
    objects: int
    steps: int
    payload_bytes: int
    degree: int
    hot_cache: int


class InMemoryStore:
    def __init__(self, *_, **__):
        self.records: dict[int, ObjectRecord] = {}
        self.next_id = 1
        self.reads = 0
        self.writes = 0

    def __enter__(self) -> "InMemoryStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.records.clear()

    def create_object(self, *, kind: str, payload: dict[str, Any], refs: list[int] | None = None) -> int:
        object_id = self.next_id
        self.next_id += 1
        self.records[object_id] = ObjectRecord(object_id=object_id, kind=kind, payload=dict(payload), refs=list(refs or []), version=0)
        self.writes += 1
        return object_id

    def update_object(self, object_id: int, *, payload: dict[str, Any] | None = None, refs: list[int] | None = None) -> ObjectRecord:
        current = self.records[object_id]
        updated = ObjectRecord(
            object_id=object_id,
            kind=current.kind,
            payload=dict(current.payload if payload is None else payload),
            refs=list(current.refs if refs is None else refs),
            version=current.version + 1,
        )
        self.records[object_id] = updated
        self.writes += 1
        return updated

    def get_object(self, object_id: int) -> ObjectRecord:
        self.reads += 1
        record = self.records[object_id]
        return ObjectRecord(
            object_id=record.object_id,
            kind=record.kind,
            payload=dict(record.payload),
            refs=list(record.refs),
            version=record.version,
            resident=record.resident,
        )

    def describe(self) -> dict[str, Any]:
        ref_count = sum(len(record.refs) for record in self.records.values())
        return {
            "objects": len(self.records),
            "pointer_model": {
                "refs": ref_count,
                "raw_pointer_bytes": 8 * ref_count,
                "tiny_pointer_bytes": 8 * ref_count,
                "estimated_pointer_savings_bytes": 0,
            },
            "stats": {"reads": self.reads, "writes": self.writes},
        }


def make_payload(index: int, payload_bytes: int) -> dict[str, Any]:
    filler = (f"blob-{index}-" + ("x" * max(0, payload_bytes)))[:payload_bytes]
    return {
        "name": f"obj-{index}",
        "value": index,
        "blob": filler,
    }


SCENARIOS: dict[str, ScenarioConfig] = {
    "knowledge_graph_walk": ScenarioConfig(
        name="knowledge_graph_walk",
        objects=15000,
        steps=40000,
        payload_bytes=256,
        degree=4,
        hot_cache=256,
    ),
    "recent_session_frontier": ScenarioConfig(
        name="recent_session_frontier",
        objects=18000,
        steps=45000,
        payload_bytes=192,
        degree=2,
        hot_cache=192,
    ),
    "full_scan_analytics": ScenarioConfig(
        name="full_scan_analytics",
        objects=12000,
        steps=24000,
        payload_bytes=128,
        degree=1,
        hot_cache=512,
    ),
}


def run_knowledge_graph_walk(store: Any, cfg: ScenarioConfig, rng: random.Random) -> None:
    ids: list[int] = []
    for idx in range(cfg.objects):
        refs = rng.sample(ids, k=min(len(ids), cfg.degree)) if ids else []
        ids.append(store.create_object(kind="node", payload=make_payload(idx, cfg.payload_bytes), refs=refs))

    current = ids[-1]
    for step in range(cfg.steps):
        node = store.get_object(current)
        if step % 19 == 0:
            payload = dict(node.payload)
            payload["visits"] = int(payload.get("visits", 0)) + 1
            store.update_object(node.object_id, payload=payload)
        current = rng.choice(node.refs) if node.refs else ids[rng.randrange(len(ids))]


def run_recent_session_frontier(store: Any, cfg: ScenarioConfig, rng: random.Random) -> None:
    session_heads: list[int] = []
    session_window = 96
    for session_idx in range(cfg.objects):
        prev = session_heads[-1] if session_heads else None
        refs = [prev] if prev is not None else []
        object_id = store.create_object(kind="session", payload=make_payload(session_idx, cfg.payload_bytes), refs=refs)
        session_heads.append(object_id)

    for step in range(cfg.steps):
        base = max(0, len(session_heads) - session_window)
        current = session_heads[base + rng.randrange(len(session_heads) - base)]
        node = store.get_object(current)
        if step % 23 == 0:
            payload = dict(node.payload)
            payload["touches"] = int(payload.get("touches", 0)) + 1
            store.update_object(node.object_id, payload=payload)


def run_full_scan_analytics(store: Any, cfg: ScenarioConfig, rng: random.Random) -> None:
    ids: list[int] = []
    prev = None
    for idx in range(cfg.objects):
        refs = [prev] if prev is not None else []
        prev = store.create_object(kind="row", payload=make_payload(idx, cfg.payload_bytes), refs=refs)
        ids.append(prev)

    for step in range(cfg.steps):
        object_id = ids[step % len(ids)]
        node = store.get_object(object_id)
        if step % 257 == 0:
            payload = dict(node.payload)
            payload["aggregated"] = True
            store.update_object(node.object_id, payload=payload)


RUNNERS: dict[str, Callable[[Any, ScenarioConfig, random.Random], None]] = {
    "knowledge_graph_walk": run_knowledge_graph_walk,
    "recent_session_frontier": run_recent_session_frontier,
    "full_scan_analytics": run_full_scan_analytics,
}


def run_case(store_kind: str, scenario_name: str, seed: int) -> dict[str, Any]:
    cfg = SCENARIOS[scenario_name]
    rng = random.Random(seed)
    gc.collect()
    tracemalloc.start()
    t0 = time.perf_counter()

    db_size = 0
    if store_kind == "torzoid":
        with tempfile.TemporaryDirectory(prefix="torzoid-bench-") as tmpdir:
            db_path = Path(tmpdir) / f"{scenario_name}.db"
            with TemporalTinyPointerStore(
                db_path,
                max_hot_objects=cfg.hot_cache,
                checkpoint_interval=8,
                prefetch_fanout=2,
                enable_prefetch=True,
            ) as store:
                RUNNERS[scenario_name](store, cfg, rng)
                summary = store.describe()
            db_size = db_path.stat().st_size if db_path.exists() else 0
    elif store_kind == "baseline":
        with InMemoryStore() as store:
            RUNNERS[scenario_name](store, cfg, rng)
            summary = store.describe()
    else:
        raise ValueError(store_kind)

    elapsed_s = time.perf_counter() - t0
    current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    gc.collect()

    return {
        "store": store_kind,
        "scenario": scenario_name,
        "objects": cfg.objects,
        "steps": cfg.steps,
        "payload_bytes": cfg.payload_bytes,
        "elapsed_s": elapsed_s,
        "peak_traced_mb": peak_bytes / (1024 * 1024),
        "current_traced_mb": current_bytes / (1024 * 1024),
        "disk_mb": db_size / (1024 * 1024),
        "summary": summary,
    }


def summarize(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_scenario: dict[str, dict[str, dict[str, Any]]] = {}
    for result in results:
        by_scenario.setdefault(result["scenario"], {})[result["store"]] = result

    rows: list[dict[str, Any]] = []
    for scenario, pair in by_scenario.items():
        baseline = pair["baseline"]
        torzoid = pair["torzoid"]
        baseline_peak = baseline["peak_traced_mb"]
        torzoid_peak = torzoid["peak_traced_mb"]
        rows.append(
            {
                "scenario": scenario,
                "baseline_peak_mb": round(baseline_peak, 3),
                "torzoid_peak_mb": round(torzoid_peak, 3),
                "peak_memory_reduction_pct": round(100.0 * (baseline_peak - torzoid_peak) / baseline_peak, 2),
                "baseline_elapsed_s": round(baseline["elapsed_s"], 3),
                "torzoid_elapsed_s": round(torzoid["elapsed_s"], 3),
                "torzoid_disk_mb": round(torzoid["disk_mb"], 3),
            }
        )
    return rows


def render_markdown(summary_rows: list[dict[str, Any]]) -> str:
    headers = [
        "Scenario",
        "Baseline peak MB",
        "Torzoid peak MB",
        "Peak memory reduction %",
        "Baseline sec",
        "Torzoid sec",
        "Torzoid disk MB",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for row in summary_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["scenario"],
                    str(row["baseline_peak_mb"]),
                    str(row["torzoid_peak_mb"]),
                    str(row["peak_memory_reduction_pct"]),
                    str(row["baseline_elapsed_s"]),
                    str(row["torzoid_elapsed_s"]),
                    str(row["torzoid_disk_mb"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Torzoid against an in-memory baseline")
    parser.add_argument("--scenario", action="append", choices=sorted(SCENARIOS), help="Limit to one or more scenarios")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    scenarios = args.scenario or list(SCENARIOS)
    results: list[dict[str, Any]] = []
    for scenario in scenarios:
        for store_kind in ("baseline", "torzoid"):
            results.append(run_case(store_kind, scenario, args.seed))

    summary_rows = summarize(results)
    if args.json:
        print(json.dumps({"results": results, "summary": summary_rows}, indent=2, sort_keys=True))
    else:
        print(render_markdown(summary_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
