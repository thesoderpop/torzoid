# Fractal Channel Memory

Authored by Alexis Eleanor Fagan.

## Summary

Fractal Channel Memory is a proposed memory-placement and scheduling model in which traffic is organized recursively across multiple locality scales rather than using only a flat channel-interleaving policy.

The repeating hierarchy is:
- channel,
- subchannel or pseudo-channel,
- rank,
- bank group,
- bank,
- row region,
- object or page family.

At each level, the scheduler repeats the same core decisions:
- what should stay local,
- what should be striped for bandwidth,
- what should be isolated from noisy traffic,
- what should be treated as replay or compression traffic,
- what should be deprioritized relative to foreground interactive work.

## Core idea

Flat memory policies often optimize primarily for broad distribution or simple fairness.
Fractal Channel Memory instead tries to preserve locality where locality exists and isolate interference where mixed traffic exists.

The model is especially relevant when:
- the workload has clustered hot regions,
- the workload mixes interactive and bulk/background traffic,
- some memory traffic is replay or compressed-tier traffic,
- the system is under pressure and placement choices matter more.

## Relationship to Torzoid

Torzoid reduces pressure by shrinking the resident hot frontier and replaying colder state.
Fractal Channel Memory does not create capacity directly. Instead, it tries to make the memory system behave better for the traffic that remains resident.

The two ideas are complementary:
- Torzoid addresses capacity pressure and cold-state replay.
- Fractal Channel Memory addresses placement, locality, and interference within the active memory traffic.

## Hypothesis

Used alone, Fractal Channel Memory should provide modest gains on locality-heavy or mixed workloads by improving placement and reducing foreground interference.

Used together with Torzoid, the gains should stack on workloads where:
- a bounded hot frontier exists,
- cold-state replay is acceptable,
- mixed traffic would otherwise interfere with the foreground.

## Expected strong-fit workloads

- game plus browser/chat/launcher multitasking,
- browser-heavy desktops,
- graph- and pointer-heavy interactive systems,
- local AI or dev systems where one active workload should stay protected while others are demoted.

## Expected weak-fit workloads

- full scans across large datasets,
- workloads with little locality,
- workloads dominated by dense sequential bandwidth and near-zero reuse,
- scenarios where capacity is not the problem and the controller is already underloaded.

## Truthfulness constraint

Fractal Channel Memory should be described as a controller and placement innovation, not as a claim that it creates physical RAM.
