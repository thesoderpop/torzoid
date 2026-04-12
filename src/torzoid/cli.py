from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from .store import TemporalTinyPointerStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="torzoid", description="Temporal tiny-pointer memory prototype")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="run a small demo workload")
    _add_common_args(demo)
    demo.add_argument("--objects", type=int, default=250)
    demo.add_argument("--steps", type=int, default=500)

    bench = subparsers.add_parser("benchmark", help="run a larger benchmark")
    _add_common_args(bench)
    bench.add_argument("--objects", type=int, default=5000)
    bench.add_argument("--degree", type=int, default=4)
    bench.add_argument("--steps", type=int, default=20000)

    inspect_parser = subparsers.add_parser("inspect", help="inspect a store")
    inspect_parser.add_argument("--db", type=Path, required=True)
    return parser


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--hot-cache", type=int, default=128)
    parser.add_argument("--checkpoint-interval", type=int, default=8)
    parser.add_argument("--seed", type=int, default=7)


def run_demo(args: argparse.Namespace) -> int:
    rng = random.Random(args.seed)
    with TemporalTinyPointerStore(
        args.db,
        max_hot_objects=args.hot_cache,
        checkpoint_interval=args.checkpoint_interval,
        enable_prefetch=True,
    ) as store:
        ids = []
        for idx in range(args.objects):
            refs = rng.sample(ids, k=min(len(ids), rng.randint(0, 3))) if ids else []
            object_id = store.create_object(
                kind="node",
                payload={"name": f"node-{idx}", "value": idx},
                refs=refs,
            )
            ids.append(object_id)

        current = ids[-1]
        for step in range(args.steps):
            node = store.get_object(current)
            if step % 7 == 0:
                updated_payload = dict(node.payload)
                updated_payload["touches"] = int(updated_payload.get("touches", 0)) + 1
                store.update_object(node.object_id, payload=updated_payload)
            if node.refs:
                current = rng.choice(node.refs)
            else:
                current = rng.choice(ids)

        print(json.dumps(store.describe(), indent=2, sort_keys=True))
    return 0


def run_benchmark(args: argparse.Namespace) -> int:
    rng = random.Random(args.seed)
    with TemporalTinyPointerStore(
        args.db,
        max_hot_objects=args.hot_cache,
        checkpoint_interval=args.checkpoint_interval,
        enable_prefetch=True,
    ) as store:
        ids: list[int] = []
        for idx in range(args.objects):
            refs = rng.sample(ids, k=min(len(ids), args.degree)) if ids else []
            ids.append(
                store.create_object(
                    kind="graph-node",
                    payload={"rank": idx, "weight": rng.random()},
                    refs=refs,
                )
            )

        current = ids[-1]
        for step in range(args.steps):
            node = store.get_object(current)
            if step % 17 == 0:
                payload = dict(node.payload)
                payload["visits"] = int(payload.get("visits", 0)) + 1
                payload["last_step"] = step
                store.update_object(node.object_id, payload=payload)
            current = rng.choice(node.refs) if node.refs else rng.choice(ids)

        print(json.dumps(store.describe(), indent=2, sort_keys=True))
    return 0


def run_inspect(args: argparse.Namespace) -> int:
    with TemporalTinyPointerStore(args.db, enable_prefetch=False) as store:
        print(json.dumps(store.describe(), indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "demo":
        return run_demo(args)
    if args.command == "benchmark":
        return run_benchmark(args)
    if args.command == "inspect":
        return run_inspect(args)
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
