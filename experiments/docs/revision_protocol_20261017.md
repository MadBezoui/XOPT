# Protocol fixed before the supplementary runs — 17 October 2026

This extension preserves the 320 primary runs, 108 original coordinate baselines, 50 radius audits and 168 literature-comparison runs without relabelling or replacing them. `XOPT.jl` remains unchanged; `anytime.jl` adds incumbent retention, bounded initialization and gap reporting using the same physical model and cuts. The source hashes of all new scripts and the protocol are stored with each run. All failures and time limits are retained.

## Incumbents and longer budgets

The full difficult cohort is defined by size, not observed success: all 18 weak/strong queries with seeds 1–3 for Hospital (10,11), Retail (5,24) and Retail (10,32). Compare cold and initialized CCG at 20 seconds on all 18, and run a separately timed coordinate baseline on each. To bound the additional compute, extend both CCG methods to 60, 120 and 300 seconds for seed 1 in each of these three size groups and both modes (six predetermined queries). This is 72 CCG runs plus 18 baselines. Conclusions about longer budgets apply only to these six queries.

A baseline initialization receives at most min(20 seconds, one quarter of the total budget); its model construction, two forward solves and fresh validation all consume the common deadline. The same independent verification is required for candidates found by either CCG mode. The baseline-only comparator gets the full 20-second deadline. Compilation warmup covers both modes and all three entry points; one HiGHS thread is used. Method order alternates within each paired query and budget. No concurrent solver jobs are used for the timed extended comparison. Machine load can still vary; runtimes are descriptive, without iid significance claims.

Report time to first validated incumbent, best intervention objective UB, valid master lower bound LB, absolute and relative gaps, method-wide elapsed time, iterations, cuts and validation results. A validated incumbent returned at a limit is not labelled globally optimal. Failure to obtain an incumbent is retained. Bounds concern the same action domain. A menu lower bound includes all unvisited and unresolved scenarios. MILP bounds and validations remain numerical, not exact certificates.

## Compound-foil temporal sensitivity

Use the eight existing I=2,T=6 demand panels (two families, seeds 1–4). Construct foils by inverting nominal activation bits on distinct deterministic periods: two literals at periods 2 and 4, or three at 2,4,6; item indices cycle from the seed. For each, run weak and strong margin 0.02 at K in {1,2,3,6}, with 15 seconds per run and no coordinate initialization (not applicable to conjunctions). Total: 128 attempted queries. Record physical foil feasibility separately and retain physically impossible requests. Compare costs within the same panel, foil and mode; show feasibility counts separately from costs on common solved instances. Multiple literals do not guarantee multiple edited periods.

## Capacity stress

Use the same eight observed-demand panels and nominal capacity multipliers 1.05 and 1.4. Solve the nominal forward problem, then choose the first nominally active coordinate in period-major order among periods 2,...,T, and request that it be off. This excludes the structurally impossible first-period-off example but does not filter on foil feasibility or expansion success. If no such coordinate exists, record the skipped construction explicitly. For each panel/factor, evaluate weak and strong modes (32 attempted menus). Menu: nominal and +25% in each single period, K=3, 30 seconds for the entire menu. Also record the physical feasibility of the foil under every scenario, nominal resource utilization and whether an expansion restores physical feasibility or merely reduces explanation cost. Pre-menu physical diagnostics are reported separately and are not charged to the explanation algorithm.

A deterministic two-period analytical control uses demand (1,0.25), capacity (1.05,1.05), zero initial/final stock and foil y2=0. The nominal foil is infeasible; +25% in period 1 permits q1=1.25. This control demonstrates the mechanism only and is explicitly distinct from observed-demand instances.

## Publication

Only experimental code, permitted data and the manuscript PDF may be public. Manuscript sources, bibliography, templates and writing files stay local. Release archives and all reachable Git trees must pass `validate_publication.py`; no journal submission or author signoff is implied.
