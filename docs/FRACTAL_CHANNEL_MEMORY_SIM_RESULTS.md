# Fractal Channel Memory Simulation Results

Authored by Alexis Eleanor Fagan.

## Method

These results come from a trace-driven simulation, not from silicon or kernel-level hardware measurements.

The simulation compared four modes:
- flat mapping baseline,
- Fractal Channel Memory alone,
- Torzoid alone,
- Fractal Channel Memory plus Torzoid.

Three workloads were used:
- `graph_walk` for locality-heavy pointer-like access,
- `game_mix` for a foreground interactive workload mixed with background noise,
- `full_scan` for a weak-fit sequential scan case.

The simulation tracked:
- average latency proxy,
- p95 latency proxy,
- row-hit proxy,
- disk-miss proxy,
- foreground latency proxy.

## Results summary

### 1. Graph-walk workload
Baseline: flat mapping.

- Fractal Channel Memory alone improved average latency by about **1.14%** and increased the row-hit proxy by about **25.36 percentage points**.
- Torzoid alone improved average latency by about **10.87%** and reduced disk-miss proxy count by about **12.49%**.
- Fractal Channel Memory plus Torzoid improved average latency by about **12.01%**, combining Torzoid's capacity benefit with Fractal Channel Memory's locality benefit.

### 2. Mixed game-style workload
Baseline: flat mapping.

- Fractal Channel Memory alone improved average latency by about **1.07%** and foreground average latency by about **1.44%**, while increasing row-hit proxy by about **21.94 percentage points**.
- Torzoid alone improved average latency by about **19.99%**, foreground average latency by about **23.49%**, and reduced disk-miss proxy count by about **23.41%**.
- Fractal Channel Memory plus Torzoid improved average latency by about **21.06%** and foreground average latency by about **24.94%**.

### 3. Full-scan workload
Baseline: flat mapping.

- Fractal Channel Memory alone improved average latency by about **0.52%**.
- Torzoid alone provided effectively **no benefit** on this scan-heavy case.
- Fractal Channel Memory plus Torzoid matched the Fractal Channel Memory result and likewise showed only a **small gain**.

## Interpretation

### What Fractal Channel Memory appears to do well
- improve locality-sensitive traffic modestly on its own,
- improve mixed interactive/background traffic modestly on its own,
- stack with Torzoid on workloads that have both locality and capacity pressure.

### What Torzoid appears to do well
- reduce pressure-driven misses,
- improve average and foreground latency on workloads where a smaller hot frontier exists,
- outperform Fractal Channel Memory alone when the main problem is capacity rather than placement.

### What the combination appears to do best
- mixed consumer workloads where both placement and pressure matter,
- graph-like or game-like hot-frontier workloads.

### What neither idea solves well
- full scans with little reuse,
- workloads where there is no meaningful hot frontier,
- cases where the system needs raw capacity and bandwidth rather than better organization.

## Practical conclusion

Fractal Channel Memory looks most promising as a multiplier on Torzoid rather than as a standalone fix for consumer RAM pressure.

The best fit is a system where:
- Torzoid reduces the amount of state that must stay resident,
- Fractal Channel Memory organizes the traffic that remains,
- foreground interactive traffic is protected from background interference.

## Caution

These are simulation-level results meant to guide architecture, not production performance claims.
