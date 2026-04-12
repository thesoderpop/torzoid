# Torzoid

Authored by Alexis Eleanor Fagan.

Torzoid is a working prototype and product direction for **temporal tiny-pointer memory** and a future consumer background service called **Torzoid Home**.

The core idea is simple:
- keep only a bounded hot set resident in memory,
- compress, demote, or replay colder state when needed,
- use smarter scheduling to protect the foreground workload first.

## What this repo currently contains

- a working temporal tiny-pointer object-store prototype,
- tests for replay, eviction, and prefetch behavior,
- benchmark notes for synthetic memory-saving workloads,
- a predictive scheduler variant,
- product documentation for a consumer RAM-optimization service.

## What Torzoid Home aims to become

Torzoid Home is intended to be a background memory-amplification service for consumer systems.
It is designed to help under memory pressure by:
- detecting pressure early,
- protecting the foreground app or game,
- reclaiming lower-value background memory first,
- using compression, demotion, replay, and scheduling to improve effective RAM behavior.

## Honest scope

Torzoid is **not** a claim that software can create physical DRAM.
It is a claim that better memory policy, compression, replay, and scheduling can improve how far existing RAM goes on selected systems and workloads.

This project is most promising for:
- browser-heavy multitasking,
- dev and creator systems with many background apps,
- object-rich or locality-heavy stores,
- selected gaming scenarios on lower-memory machines.

This project is **not** guaranteed to improve every workload, and it should not be marketed as universal FPS magic or a replacement for buying more RAM when a system is physically underprovisioned.

## Licensing

Torzoid is free for noncommercial use.
Commercial use is not free and requires a separate commercial agreement.
Commercial terms are intended to use royalties, profit share, or a negotiated combination.

## Repo guide

- `src/torzoid/store.py` — core prototype store
- `src/torzoid/smart_store.py` — smarter scheduler variant
- `tests/` — test suite
- `docs/TORZOID_HOME_PRODUCT_SPEC.md` — product spec
- `docs/MODULES_AND_APIS.md` — module map and API shapes
- `docs/ROLLOUT_PLAN.md` — phased rollout plan
- `docs/BENCHMARK_TARGETS.md` — benchmark target matrix

## Status

Prototype and product-design stage.
Not yet a finished drag-and-drop consumer app.

## Vision

Make limited consumer RAM behave better by combining:
- pressure-aware policy,
- hierarchical scheduling,
- compression,
- replay,
- and foreground protection.
