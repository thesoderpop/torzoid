# Benchmark Notes

The benchmark harness compares Torzoid against a pure in-memory baseline.

## Scenarios

### 1. `knowledge_graph_walk`
Large graph-like object set with sparse references and locality-heavy traversal.
This approximates knowledge graphs, citation graphs, or long-lived agent memory stores.

### 2. `recent_session_frontier`
Large session/event corpus where reads cluster around a recent frontier.
This approximates chat histories, append-only logs, or workflow/session timelines.

### 3. `full_scan_analytics`
Sequential scans across almost the entire dataset.
This is included as a stress case because it is not a good latency fit for replay-on-demand designs.

## Snapshot results

| Scenario | Baseline peak MB | Torzoid peak MB | Peak memory reduction % | Baseline sec | Torzoid sec | Torzoid disk MB |
|---|---:|---:|---:|---:|---:|---:|
| knowledge_graph_walk | 11.588 | 1.433 | 87.63 | 0.530 | 22.741 | 6.750 |
| recent_session_frontier | 12.428 | 1.068 | 91.41 | 0.449 | 12.625 | 6.230 |
| full_scan_analytics | 7.743 | 1.171 | 84.87 | 0.212 | 12.140 | 2.938 |

## Interpretation

Torzoid improved resident Python heap usage substantially in all measured synthetic workloads because only the hot frontier stayed materialized in RAM.

The strongest practical fit is workloads where:

- the total object graph is much larger than the active working set,
- objects are pointer-rich and individually modest in size,
- historical state can be journaled and replayed,
- cold misses are acceptable, and
- storage I/O is cheaper than keeping the whole corpus hot.

The benchmark also shows the expected cost: this prototype is slower than the in-memory baseline by a large margin. That is the explicit trade: less RAM, more time.
