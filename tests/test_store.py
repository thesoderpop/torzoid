from __future__ import annotations

import time

from torzoid.store import TemporalTinyPointerStore


def test_create_update_and_rebuild(tmp_path):
    db = tmp_path / "store.db"
    with TemporalTinyPointerStore(db, max_hot_objects=2, checkpoint_interval=2, enable_prefetch=False) as store:
        a = store.create_object(kind="node", payload={"name": "a"}, refs=[])
        b = store.create_object(kind="node", payload={"name": "b"}, refs=[a])
        store.update_object(a, payload={"name": "a", "count": 1}, refs=[b])
        store.evict_all()
        rebuilt = store.get_object(a)
        assert rebuilt.payload["count"] == 1
        assert rebuilt.refs == [b]
        stats = store.describe()["stats"]
        assert stats["cold_rebuilds"] >= 1
        assert stats["journal_replays"] >= 1


def test_lru_eviction(tmp_path):
    db = tmp_path / "store.db"
    with TemporalTinyPointerStore(db, max_hot_objects=2, checkpoint_interval=3, enable_prefetch=False) as store:
        ids = [store.create_object(kind="node", payload={"i": i}, refs=[]) for i in range(4)]
        hot = store.list_hot_object_ids()
        assert len(hot) == 2
        assert hot == ids[-2:]
        stats = store.describe()["stats"]
        assert stats["evictions"] >= 2


def test_prefetch_brings_neighbors_hot(tmp_path):
    db = tmp_path / "store.db"
    with TemporalTinyPointerStore(db, max_hot_objects=4, checkpoint_interval=2, prefetch_fanout=2, enable_prefetch=True) as store:
        a = store.create_object(kind="node", payload={"name": "a"}, refs=[])
        b = store.create_object(kind="node", payload={"name": "b"}, refs=[])
        c = store.create_object(kind="node", payload={"name": "c"}, refs=[])
        root = store.create_object(kind="node", payload={"name": "root"}, refs=[a, b, c])
        store.evict_all()
        store.get_object(root)
        for _ in range(20):
            hot = set(store.list_hot_object_ids())
            if {a, b}.issubset(hot):
                break
            time.sleep(0.05)
        hot = set(store.list_hot_object_ids())
        assert {a, b}.issubset(hot)
        assert root in hot
        stats = store.describe()["stats"]
        assert stats["prefetched"] >= 1


def test_pointer_estimate_shows_savings(tmp_path):
    db = tmp_path / "store.db"
    with TemporalTinyPointerStore(db, max_hot_objects=8, checkpoint_interval=2, enable_prefetch=False) as store:
        a = store.create_object(kind="node", payload={"x": 1}, refs=[])
        b = store.create_object(kind="node", payload={"x": 2}, refs=[a])
        store.create_object(kind="node", payload={"x": 3}, refs=[a, b])
        pointer_model = store.describe()["pointer_model"]
        assert pointer_model["refs"] == 3
        assert pointer_model["estimated_pointer_savings_bytes"] > 0
