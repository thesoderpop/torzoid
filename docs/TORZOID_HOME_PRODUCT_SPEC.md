# Torzoid Home Product Spec

Authored by Alexis Eleanor Fagan.

## Product summary

Torzoid Home is a background memory-amplification service for consumer systems.
Its job is to improve effective RAM usage by detecting pressure early, protecting the foreground workload, and reducing the resident footprint of lower-value background state through a mix of compression, demotion, replay, and scheduling.

Torzoid Home should be presented as a practical memory-pressure optimizer, not as a claim that it increases physical DRAM.

## Product goals

1. Improve responsiveness on low-to-mid RAM consumer systems.
2. Protect the foreground app or game during pressure spikes.
3. Reduce memory waste from idle background apps and cold state.
4. Provide profiles for gaming, browser-heavy use, creator workflows, development, and local AI workloads.
5. Make the system simple enough to run as a background service with minimal user interaction.

## Non-goals

1. Rewriting arbitrary third-party game memory layouts.
2. Claiming universal performance gains across all games or workloads.
3. Replacing operating-system memory management.
4. Beating a true in-memory baseline on latency for every workload.

## Product modes

### Observe mode
Read-only analysis of memory pressure, background offenders, and likely reclaim opportunities.

### Assist mode
Safe automated actions.
Examples:
- protect foreground processes,
- park user-approved background apps,
- tune OS-level compressed memory features where supported,
- surface reclaim recommendations.

### Aggressive mode
Pressure-triggered reclaim orchestration for users who explicitly opt in.
Examples:
- stronger app parking,
- tighter budget enforcement,
- more aggressive compression / replay behavior,
- pressure-aware scheduling.

## Target users

### Primary
- gamers on 8 GB to 16 GB systems,
- laptop users with many background apps,
- users running browsers, Discord, launchers, media apps, and games simultaneously.

### Secondary
- creators with large projects and many helper apps,
- developers running IDEs, browsers, containers, and local AI tools,
- local AI hobbyists on limited-memory machines.

## System architecture

### Plane 1: Telemetry
Collect memory, CPU, and I/O pressure signals.

#### Windows
- low-frequency counters and memory APIs for baseline status,
- burst-mode ETW tracing when pressure or stutter rises,
- per-process scoring for footprint, faults, backgroundness, and reclaim risk.

#### Linux
- PSI-driven pressure detection,
- per-cgroup memory observation,
- swap, reclaim, and stall-rate monitoring.

### Plane 2: Policy
A hierarchical policy engine makes reclaim and protection decisions.

#### Fractal scheduling model
The same policy repeats at each level:
- system budget,
- class budget,
- application budget,
- region budget,
- object/page budget.

At each level the engine decides:
- what must stay hot,
- what may be compressed,
- what may be replayed,
- what may be throttled,
- what may be parked or suspended.

### Plane 3: Actuation
Apply the least disruptive action that relieves pressure.

Examples:
- foreground protection,
- background parking,
- compressed-memory tuning,
- replay-budget scheduling,
- cache demotion,
- user-approved app suspension.

## Consumer profiles

### Gaming
Protect the foreground game first, reclaim launchers, browsers, chat apps, media apps, and other idle helpers before touching the game.

### Browser
Park dormant tabs and background browser processes sooner while keeping the active tab cluster warm.

### Creator
Protect the active editing app and downshift inactive previews, background sync, and sidecar helpers.

### Dev
Protect the active IDE, compiler, or serving model while reclaiming stale browsers, chat apps, or idle containers.

### Local AI
Keep the live model hot, compress or park noncritical helpers, and avoid letting side apps steal the active working set.

## UX requirements

1. Must be installable and runnable as a background service.
2. Must expose simple profiles and a clear on/off state.
3. Must show what it changed and why.
4. Must provide allowlists / blocklists for apps.
5. Must avoid hidden destructive behavior.

## Product truthfulness constraints

Torzoid Home may truthfully claim:
- improved effective RAM usage on some systems,
- lower resident footprint on some workloads,
- better behavior under memory pressure in selected profiles.

Torzoid Home should not claim:
- faster performance in every game,
- universal FPS improvements,
- that it creates physical memory,
- that it can safely optimize every application without workload-specific limits.

## Risks

1. Added CPU time from compression / replay may harm latency-sensitive apps.
2. Over-aggressive background reclaim can increase resume latency.
3. Workloads with low locality may see little benefit.
4. Windows support is more constrained than Linux for safe deep actuation.

## Success criteria

1. Reduced memory-pressure stalls under representative consumer multitasking loads.
2. No regression in user-visible responsiveness in safe mode.
3. Clear benefits on at least browser-heavy, dev-heavy, and selected gaming scenarios.
4. Transparent, reversible actions.
