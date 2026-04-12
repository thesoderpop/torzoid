# Benchmark Targets

Authored by Alexis Eleanor Fagan.

## Goal
Measure whether Torzoid Home improves effective RAM behavior under realistic consumer pressure without causing unacceptable regressions.

## Metrics

### Memory
- peak resident memory,
- active working-set pressure,
- compressed-memory usage,
- reclaimed memory estimate,
- fault rate,
- swap activity,
- cold replay count,
- hot-hit rate.

### Latency / responsiveness
- frame pacing,
- application input delay,
- foreground resume latency,
- app switch latency,
- background app resume latency.

### Cost
- CPU overhead,
- disk I/O overhead,
- battery / power impact where measurable,
- wasted prefetch count,
- avoided reclaim count.

## Workload matrix

### Gaming multitask profile
Foreground game + browser + Discord + launcher + media app.

Questions:
- does Torzoid reduce pressure on 8 GB to 16 GB systems,
- does it avoid hurting frame pacing,
- does it reclaim background memory before touching the game.

### Browser overload profile
20 to 100 tabs plus chat, music, and office apps.

Questions:
- can Torzoid preserve the active tab cluster,
- can it reduce background browser footprint,
- what is the tab resume penalty.

### Creator profile
Editor + large project + browser + sync clients + media helper apps.

Questions:
- does the active editing workload remain responsive,
- can inactive helpers be demoted safely,
- what is the resume cost for previews and side tools.

### Dev profile
IDE + browser + containers + local AI tool + chat app.

Questions:
- can Torzoid preserve the active coding path,
- can it reclaim stale background tools,
- how much CPU budget does replay consume.

### Local AI profile
One active model plus browsers, editor, and helper apps.

Questions:
- can Torzoid stop side apps from stealing the model working set,
- can it reduce overall memory pressure without destabilizing inference.

## Benchmark tiers

### Tier A: Synthetic
Graph walk, frontier-locality, and full-scan workloads.
Used for regression and scheduler experiments.

### Tier B: Scripted consumer scenarios
Repeatable desktop workflows and game-launch sequences.

### Tier C: Real-user pilot captures
Opt-in traces from early testers.

## Success thresholds

### Safe mode
- no meaningful foreground responsiveness regression,
- measurable reduction in pressure or background footprint,
- clear action logging.

### Assist mode
- improved pressure behavior on representative low-RAM systems,
- acceptable resume latency for parked apps,
- limited CPU overhead.

### Aggressive mode
- larger memory wins,
- user-visible risk explained and controlled,
- no silent destructive actions.
