# Recourse-cost lever study, protocol fixed before execution (17 October 2026)

This third supplementary study evaluates explanations that may edit continuous recourse costs, as in Section "Editing continuous recourse costs" of the manuscript. It adds new records and replaces none. Records go to `results/levers_<profile>_w<k>.jsonl`, one file per worker, with SHA-256 hashes of `src/XOPT.jl`, `src/levers.jl`, `src/enumerate_levers.jl`, `scripts/run_levers.jl` and this protocol. Every attempt is kept.

## Scope and levers

Retail lot-sizing model only, because its recourse is a minimum-cost flow and Lemma (dual bounds) applies with N = 1 + T + I T nodes. The hospital model has gains on inventory arcs and is not covered. Lever sets: F (activation costs only, as in the primary study), PH (unit production costs p and holding costs h only, activation costs fixed), FPH (all three). Continuous edits are bounded by 80 % of the nominal value and normalized by it, like activation edits. Holding costs of the last period are not levers because final inventory is zero. Edits of p_it and h_it count toward period t. Margin 0.02 in strong mode, lambda_T = 0.01, lambda_P = 0, period budget and other options as in the primary record of each query.

## Profile `enum` (correctness against an independent method)

Instances: the five (1,4) retail panels of the main study with their main-study foils, and five (1,5) instances derived from the five (2,6) retail panels (item 1, periods 1 to 5, costs regenerated with the panel seed as in `make_instance`) with the foil that inverts the nominal activation of period 3. Both semantics and lever sets PH and FPH: 40 cases. Each case is solved by dual-cut CCG, trajectory-cut CCG and an independent enumeration that lists every binary pattern, every vertex of its recourse polytope by basis enumeration, and solves one linear model per foil vertex without LP duality or optimality conditions. Agreement is required within 1e-6 in objective and in status. Any disagreement is reported as such.

## Profile `bench` (benchmark)

Queries: every retail CCG query of the main study ((1,4), (2,6), (3,8), five seeds, weak and strong: 30 queries) and of the scale study with (I,T) in {(5,8),(5,11)} (three seeds, weak and strong: 12 queries), with their recorded foils. Methods: F with dual cuts, PH and FPH each with dual cuts and with trajectory cuts. That is 42 x 5 = 210 runs, 300 s each, jobs shuffled with seed 20261017 and dealt to workers round-robin. Up to six single-thread workers run concurrently, so times are descriptive.

Reported: status counts; paired objective changes from F to FPH (the FPH optimum can never exceed the F optimum, and any violation beyond 1e-5 is reported); the number of queries that F cannot explain but FPH or PH can; how often continuous levers appear in FPH optima; paired iterations and times of dual and trajectory cuts; fresh validation results, the KKT consistency gap and the dual-bound diagnostic of every validated explanation.
