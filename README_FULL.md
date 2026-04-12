# Torzoid

Torzoid is a working prototype of temporal tiny-pointer memory: a storage layer that cuts resident RAM by keeping only a bounded hot set in memory and reconstructing cold objects from durable checkpoints plus a journal.

It explores the idea of trading space for time:

- use compact integer handles as tiny pointers,
- keep only a small hot frontier resident,
- store the rest durably on disk,
- rebuild cold state on demand, and
- optionally prefetch likely neighbors.

## Repo contents

- `src/torzoid/store.py` — core store
- `src/torzoid/cli.py` — demo and inspect CLI
- `tests/test_store.py` — automated tests
- `scripts/benchmark_memory.py` — benchmark harness
- `BENCHMARKS.md` — measured results and interpretation
- `.github/workflows/ci.yml` — CI

## Install

```bash
python -m pip install -e .
```

## Test

```bash
python -m pytest -q
```

## Demo

```bash
torzoid demo --db /tmp/torzoid.db --objects 300 --steps 800
```

## Benchmark

```bash
PYTHONPATH=src python scripts/benchmark_memory.py
```

## Licensing

Torzoid is free for noncommercial use.
Commercial use is not free and requires a separate commercial agreement.
Commercial terms are intended to use royalties, profit share, or a negotiated combination.

## Authorship

Authored by Alexis Eleanor Fagan.
