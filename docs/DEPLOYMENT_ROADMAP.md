# Deployment Roadmap

Authored by Alexis Eleanor Fagan.

## Phase 0: Prototype hardening

Goals:
- stabilize tests,
- verify replay correctness,
- benchmark scheduler variants,
- improve docs and safety constraints.

Exit criteria:
- clean automated tests,
- baseline benchmarks checked in,
- documentation for product boundaries complete.

## Phase 1: Linux-first consumer daemon

Scope:
- CLI + daemon,
- observe mode,
- assist mode,
- PSI-driven telemetry,
- profile selection,
- safe action logging,
- cgroup-aware foreground protection,
- compressed-memory integration where supported.

Why Linux first:
- better pressure visibility,
- safer and richer kernel-level actuation,
- clearer control over protected and reclaimable groups.

Exit criteria:
- stable daemon on major desktop distributions,
- gaming and browser profiles usable,
- measurable gains on representative systems.

## Phase 2: Linux UI and usability

Scope:
- tray application,
- app allowlist / blocklist,
- action history,
- pause / resume,
- onboarding flow,
- benchmark capture UI.

Exit criteria:
- drag-and-drop simple install story,
- profile switching without CLI,
- understandable user-facing explanations.

## Phase 3: Windows observe + assist

Scope:
- user-mode service,
- safe telemetry collection,
- foreground protection heuristics,
- background app parking recommendations,
- opt-in automatic actions for selected apps,
- action log and rollback-friendly behavior.

Constraints:
- no deep invasive unsupported process memory rewriting,
- no universal claim of optimization for every game,
- higher emphasis on cooperating apps and safe coordination.

Exit criteria:
- useful observe mode,
- clear value on low-memory multitasking systems,
- no unacceptable responsiveness regressions in safe mode.

## Phase 4: Plugin ecosystem

Scope:
- app-specific adapters,
- browser helpers,
- launcher / overlay adapters,
- creator-tool integrations,
- optional local-AI helpers.

Goal:
Move from generic safe coordination to richer app-aware memory shedding.

## Phase 5: Commercial packaging

Scope:
- installer,
- signed binaries,
- profile presets,
- licensing UI,
- update channel,
- issue reporting,
- benchmark export.

## Release channels

### Nightly
Fast iteration, benchmark and telemetry heavy.

### Preview
Stable enough for enthusiasts.

### Stable
Conservative defaults, safe mode first.

## Truthful launch messaging

Say:
- helps some systems under memory pressure,
- strongest on selected multitasking and locality-heavy workloads,
- profile-driven and reversible,
- Linux-first for deepest optimization.

Do not say:
- faster in every game,
- universal RAM multiplier,
- guaranteed FPS increase,
- safe aggressive optimization for every application.
