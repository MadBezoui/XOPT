# Supplementary results — 17 October 2026

The original 320-run benchmark, 108 original coordinate baselines, 50 stability audits and 168 literature-comparison runs are preserved. The core `src/XOPT.jl` has not changed. The new extension is in `src/anytime.jl`.

## Design, timing audit and retained outcomes

The fixed design contains 250 query/method/budget slots: 90 initialization/deadline attempts, 128 compound-foil attempts and 32 capacity menus. Four original elapsed-time measurements were interrupted by operating-system sleep. The documented timing-only rule repeats both methods in their three paired blocks, adding six attempts. All 256 original and repeated records remain available in `results/revision_all_attempts.csv`; `revision_results.csv` uses the repeated pairs for the controlled comparison. The four interrupted records and their unresolved statuses were not deleted. The largest remaining controlled elapsed-time overrun is 0.204 seconds.

The original 90 extended attempts had 24 closed-gap explanations, 21 feasible timeouts, 27 timeouts without a retained witness and 18 coordinate baselines. The six repeats returned two closed-gap explanations, two feasible timeouts and two timeouts without a witness. After replacing complete paired blocks, the controlled 90 slots have 25 closed-gap explanations, 21 feasible timeouts, 26 timeouts without a witness and 18 baselines. The raw and controlled denominators are distinct.

## Findings

- At 20 seconds on all 18 difficult queries, the full-budget coordinate baseline validates 18 explanations; initialized CCG retains 16 and closes 3 gaps; cold CCG retains 2 and closes 2. Initializer construction and fresh validation count within the common deadline. Two short initializer allocations fail to return a witness. Initialization is conditional, not guaranteed.
- On the six predetermined seed-1 queries, both CCG variants close 4 gaps at 120 and 300 seconds. At 300 seconds, initialized CCG retains all 6 witnesses while cold CCG retains 4. The remaining initialized Retail (10,32) gaps are 6.82% (strong) and 7.71% (weak). A zero median gap does not mean every query is solved.
- The 128 compound attempts yield 85 closed gaps and 43 solver-reported infeasible intervention problems. All constructed compound foils are physically feasible. Across 57 jointly solved adjacent-budget pairs, 5 costs decrease by more than 1e-5; the largest upward difference is approximately 3.24e-14. No three-literal query is solved at K=1, so their four-budget common cost cohort is empty; coverage curves and all outcomes remain visible.
- The 32 capacity menus yield 30 closed gaps and 2 solver-infeasible menus. Six nominal foils are physically infeasible; expansion restores four (two Retail panels, each with two semantics). The ten expanded winners consist of four physical restorations and six cost improvements relative to solved nominal explanations. The other twenty winners use nominal capacity. Resource-utilization peaks span 0.55–1.00.
- The 12 cold/initialized pairs solved to numerical optimality agree within 3.71e-12 in intervention objective. This is consistency evidence, not an independent exact proof.

## Interpretation and reproducibility

Primary sensitivity plots now use identical instances across K and display feasibility coverage separately. The new compound study exhibits both within-query cost reductions and feasibility thresholds. The initialization ablation supports earlier access to a checked explanation; it does not establish a general acceleration of global optimization. Capacity restoration is separated from cost improvement.

`revision_protocol_20261017.md` and `timing_repair_protocol_20261017.md` state the protocols. Each raw record contains input parameters, a complete retained witness when available, traces, bounds, status, timing and source hashes. `revision_validation.json` records the fresh post-run witness checks; `validation_report.json` joins the original and supplementary audits. The validation uses the same floating-point solver and model, not rational certificates or independent replication.
