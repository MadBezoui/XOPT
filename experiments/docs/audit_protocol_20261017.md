# Audit-response study, protocol fixed before execution (17 October 2026)

This second supplementary study answers six substantive objections raised in the editorial audit of the manuscript. It adds new records and never replaces the primary benchmark (320 runs) or the first supplementary study (250 attempts, 256 retained). All records go to `results/audit_<profile>_w<k>.jsonl`, one file per worker, with SHA-256 hashes of `src/XOPT.jl`, `src/anytime.jl`, `src/robustness.jl`, `src/audit.jl`, `scripts/run_audit.jl` and this protocol. Every attempt is kept, including timeouts and unresolved outcomes.

## Execution environment

Apple M1 Pro, 10 cores, 16 GB, Julia 1.11.6, HiGHS with one thread per solve. Unlike the earlier studies, several single-thread jobs run concurrently: six workers for the `long` profile and up to three workers for the auxiliary profiles. Timings are therefore descriptive, and the manuscript states this concurrency. A process-scoped idle-sleep inhibitor (`caffeinate -i`) covers the whole campaign. Jobs whose elapsed time exceeds the budget by more than max(1 s, 5 %) are flagged in the analysis, not silently rerun.

## Profile `long` (objection 3: scale and time limits)

Cohort: the same 18 weak and strong queries as the first supplementary study (Hospital (10,11), Retail (5,24), Retail (10,32), seeds 1 to 3), same foils and options. Methods: cold CCG and initialized CCG from `anytime.jl`. Budgets: 600 s for all 18 queries, and 1800 s for the six seed-1 queries. That is 48 runs. Jobs are sorted by decreasing budget and dealt round-robin to workers.

## Profile `sparsity` (objection 2: an active support budget)

Panels: the ten (I,T)=(3,8) demand panels of the main study (five seeds, two families). Foils: k in {2,3,4} literals inverting the nominal activation of item 1+mod(seed+l-2, I) in period 2l, l=1..k (the construction of the first supplementary study, extended to four literals). Options: weak and strong (margin 0.02), K_T in {1,2,3,4,8}, edit bound factor in {0.8, 0.4}, lambda_T = 0 and lambda_P = 0 so that the objective is the pure normalized edit cost, 30 s per attempt, cold anytime CCG. That is 600 attempts. Physical foil feasibility is recorded separately. The primary summary is the paired cost curve on queries solved at every K_T, and the count of adjacent K_T pairs with a strict decrease above 1e-5. The 0.4 bound is included because a single coordinate then cannot absorb a large edit, which is the regime where spreading the intervention over periods can lower its cost.

## Profile `margin` (objection 4: margin calibration)

Queries: the 30 strong-mode CCG queries of the main study (all sizes), same foils. Margins gamma in {0.01, 0.02, 0.05, 0.1, 0.2, 0.5}, primary CCG, 15 s. For every validated witness, the fixed-witness radius is computed with rho_max = 0.5, bisection resolution 1e-5 and 30 s. The nominal optimal value is recorded so that gamma can be reported relative to it. That is 180 attempts.

## Profile `naive` (objection 1: what scenario separation buys)

Queries: the 16 primary capacity menus and the 32 capacity-stress menus. For every expanded scenario of each menu, two primary CCG solves with 30 s each are compared. The correct one solves master and oracle under the expanded capacity. The naive one solves the master under the expanded capacity but separates competitors under the nominal capacity, which is what reusing a nominal competitor pool amounts to. Every naive explanation is then validated by a fresh full-horizon oracle under the expanded capacity. Reported: number of naive explanations that fail this validation, and the understatement of intervention cost relative to the correct solve.

## Profile `bound` (objection 5: a lower bound for the coordinate baseline)

For every distinct (instance, foil) pair of the main, scale, long, compound and sparsity queries, two forward solves with a 120 s limit each give a lower bound on the best foil cost alpha and an upper bound on the best nonfoil cost beta. The analytical bound is

    Psi >= max(0, alpha_LB - beta_UB + s) / max_k a_k + (lambda_T + lambda_P) * [that maximum > 0],

with s = gamma in margin mode and s = -epsilon in additive mode. Reported: the number of validated global optima below this bound (any such case falsifies the derivation or reveals a numerical issue, and is reported as such), the ratio between the bound and the validated optimum, and the bound-based gap of the coordinate baseline. In the anytime comparison the reported lower bound becomes the maximum of the master bound and this bound, computed after the fact and labeled as such.

## Not changed

Objection 6 (AI disclosure) is a manuscript change only. No primary or first-supplementary record is edited or deleted.
