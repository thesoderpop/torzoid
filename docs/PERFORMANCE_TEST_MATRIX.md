# Performance Test Matrix

Authored by Alexis Eleanor Fagan.

## What to measure

### Core metrics
- peak resident memory,
- traced heap where applicable,
- memory-pressure stall time,
- major and minor fault rates,
- swap activity,
- p95 and p99 resume latency,
- p95 and p99 foreground frametime or interaction latency,
- CPU overhead from compression, replay, and scheduling,
- disk footprint for durable state.

## Test profiles

### Gaming multitask
Foreground game plus browser, Discord, launcher, music, and one background helper.

Success condition:
- lower background pressure,
- no worse frame pacing in safe mode,
- measurable reclaim from background apps.

### Browser stress
Large tab set with media, docs, chat, and shopping/search tabs.

Success condition:
- lower system pressure,
- active tab cluster preserved,
- dormant tabs resume acceptably.

### Creator workstation
Editor plus browser plus sync plus media plus side helpers.

Success condition:
- active editor stays smooth,
- inactive caches or helpers are demoted first.

### Dev workstation
IDE, browser, local server, containers, chat, and optional local model.

Success condition:
- active toolchain preserved,
- background tools reclaimed before foreground latency regresses.

### Local AI workstation
One active model plus browser, editor, and general background apps.

Success condition:
- live model stays protected,
- side processes contribute reclaimed memory.

## Scheduler comparison matrix

Compare at minimum:
- baseline in-memory or no intervention,
- no-prefetch replay,
- FIFO prefetch,
- predictive budgeted scheduler,
- fractal or hierarchical scheduler if implemented.

## Report format

Each benchmark report should include:
- machine spec,
- RAM size,
- storage type,
- OS and kernel or build,
- active profile,
- exact app mix,
- before/after metrics,
- regression notes,
- clear statement of whether the workload benefited.

## Anti-hype rule

Every benchmark set must include at least one bad-fit workload and must explicitly note when Torzoid does not help.
