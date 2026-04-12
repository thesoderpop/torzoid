from __future__ import annotations

import time

from torzoid.smart_store import PredictiveTemporalTinyPointerStore


def test_predictive_store_preserves_rebuild_semantics(tmp_path):
    db = tmp_path / "predictive.db"
    with PredictiveTemporalTinyPointerStore(db, max_hot_objects=2, checkpoint_interval=2, enable_prefetch=False) as store:
        a = store.create_object(kind="node", payload={"name": "a"}, refs=[])
        b = store.create_object(kind="node", payload={"name": "b"}, refs=[a])
        store.update_object(a, payload={"name": "a", "count": 2}, refs=[b])
        store.evict_all()
        rebuilt = store.get_object(a)
        assert rebuilt.payload["count"] == 2
        assert rebuilt.refs == [b]


def test_predictive_scheduler_deduplicates_and_prefetches(tmp_path):
    db = tmp_path / "predictive.db"
    with PredictiveTemporalTinyPointerStore(
        db,
        max_hot_objects=4,
        checkpoint_interval=2,
        prefetch_fanout=2,
        enable_prefetch=True,
        prefetch_budget_per_sec=500,
    ) as store:
        a = store.create_object(kind="node", payload={"name": "a"}, refs=[])
        b = store.create_object(kind="node", payload={"name": "b"}, refs=[])
        root = store.create_object(kind="node", payload={"name": "root"}, refs=[a, b])
        store.evict_all()
        for _ in range(3):
            store.get_object(root)
        for _ in range(30):
            hot = set(store.list_hot_object_ids())
            if {a, b}.issubset(hot):
                break
            time.sleep(0.02)
        hot = set(store.list_hot_object_ids())
        assert {a, b}.issubset(hot)
        desc = store.describe()
        assert desc["stats"]["prefetch_requests"] <= 6
        assert desc["scheduler"]["mode"] == "predictive"
