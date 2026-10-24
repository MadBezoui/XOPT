# Research log: exact recourse-cost explanations at realistic size

Started 18 October 2026 at Madani's request. Each cycle states a hypothesis, the change, the test and the outcome, including failures.

## Success criterion (fixed before cycle 1)

Exact explanations with editable marginal costs on the RTS-GMLC unit commitment model, ten units and twelve hours, resolved within 300 seconds for a majority of queries, with agreement against the independent enumeration on small cases. No published method does this: Kurtz et al. (2026) treat linear programs, Lefebvre and Schmidt (2026) use a heuristic, and Engelhardt et al. do not edit costs of continuous variables.

## Starting point

Prespecified benchmark of 17 October: 0 of 96 runs with marginal levers resolve within 300 s. Every run stops in the second master with lower bound 0. A McCormick underestimate of the primal dispatch cost did not help on one 6-unit, 6-hour query.

Diagnosis: the master represents the foil's recourse value by the dual objective of its optimality conditions. In the LP relaxation the complementarity big-M constraints are slack, so this dual objective can fall far below the true recourse value, and a zero edit looks feasible.

## Cycle 1: price cuts and tighter reduced-cost bounds

Hypothesis: lifting the relaxed recourse value towards its true level will raise the lower bound.

Change (`src/uc2.jl`, flags `tightR` and `benders`):
- Reduced-cost bounds per segment, m_gk + B_g instead of 2 c̄, valid because an optimal dual has reduced cost max(0, m' - λ).
- For every hour and every candidate price lb in {0} ∪ {m_gk}, the multipliers min(0, m_gk - lb) - zn_gt are dual feasible for the edited costs whenever zn_gt ≥ max(0, -ζ_gt). Their dual objective is a valid lower bound on the hour's recourse value, linear in the commitment after exact linearization of zn·u. At ζ = 0 and integral commitments the cuts reproduce the exact recourse value.

Test: `research/cycle_test.jl`, tiny agreement with enumeration, then two strong queries on a 6-unit 6-hour case and on two 10-unit 12-hour days, levers M and FM.

Outcome (18 October, morning): mixed but real progress.
- Tiny cases: 14 of 14 agree with the enumeration.
- Lower bounds are no longer zero. On the 6-unit 6-hour case, one query of two is solved for both lever sets (M in 105 s, FM in 60 s), the other times out with bounds 0.31 and 0.48. On the 10-unit 12-hour cases, all eight runs still time out in the second master, now with bounds between 0.27 and 2.67 instead of 0.
- Criterion not met.

## Side finding: a solver failure in the prespecified correctness study

The correctness study finished with 140 cases. Trajectory cuts agree with the enumeration on all 140 and dual cuts on 139. In the remaining case (tiny_2020-07-06_s1_h15, strong, M) the dual-cut run returned a valid explanation of objective 0.253 instead of 0.204. Fixing the enumerated optimum in the same master shows it is feasible with objective 0.204, so HiGHS reported optimality wrongly. Bounding the cut duals to [0, cbar] and [-cbar, 0], which keeps the cut exact by the dispatch corollary, gives 0.204 in a rerun with no other change (`research/debug_dual3.jl`). The article reports this.

## Cycle 2: bounded cut duals and segment ordering

Hypothesis: free dual variables in the cuts and symmetric dispatch choices make the master numerically fragile and slow.

Change (flags `boundcut` and `order`): cut duals bounded as above, and within a unit a segment may be used only if the previous one is full (valid because segment costs increase within a unit and share the shift).

Test: `research/cycle_time.jl` through `research/run_cycle.sh` (12 jobs, six single-thread processes at a time), `research/cycle2.log`. The tiny agreement step was moved out of the timing harness because its enumeration takes over an hour.

Outcome: no improvement. The same two 6-unit queries are solved (M in 162 s, FM in 101 s, slower than cycle 1 but under parallel contention), the same two time out, and all eight 10-unit runs time out in the second master with bounds within a few percent of cycle 1. Criterion not met. Timeouts measured in a parallel batch are not final until rerun alone.

Solo reruns with 1200 s (`research/alone.log`): the two hard 6-unit queries still time out (bounds 0.66 and 0.83), and the first 10-unit query too (bound 2.66). The difficulty is real, not contention.

## Cycle 3: SCIP 10 (Apache 2.0), installed in `research/scipenv` with Madani's go-ahead

Hypothesis: native complementarity (SOS1) or a direct bilinear witness avoids the weak big-M relaxation.

- 3a, KKT with SOS1 complementarity (`research/cycle3_sos.log`): worse than HiGHS. The two 6-unit queries that HiGHS solves now time out, and most 10-unit runs end in the first master with bound 0.
- 3b, bilinear witness cost (m+ζ)'p, no optimality conditions (`research/cycle3_bil.log`): best bounds so far on the hard 6-unit query (0.93 and 0.89 in 300 s, versus 0.66 and 0.83 for HiGHS in 1200 s), but it solves nothing and its 10-unit bounds are 0.

Criterion not met.

## Cycle 4: fixed foil witness (`research/fixedwitness.jl`, `research/cycle4.log`)

Idea: fix the foil pattern and its completion (best foil plan at nominal costs). The master is then linear in the edits except for support binaries, competitors enter through exact dual cuts, and every returned explanation is valid by construction and checked by the same fresh verifier as the exact method. Optimality holds only for the fixed witness.

Outcome: 8 of 12 queries return verified explanations, each within 3.4 s, including 5 of 8 on ten units and twelve hours. On the two queries where the exact optimum is known, it finds it (0.652 and 0.516) in 0.1 s instead of 100 to 160 s. On four queries the fixed witness admits no explanation. Gaps against the exact lower bounds are large where both exist (for example 1.93 against 0.27). Fast and valid, not yet certified.

## Cycle 5: several witnesses

Change: try the 8 best foil patterns at nominal costs as witnesses and keep the best explanation (`research/cycle5.log`).

Outcome: 9 of 12 queries explained and verified (one more than cycle 4), each within 71 s, but no objective improves. The three failures are all marginal-only queries on ten units, which may simply be infeasible; the exact method never concluded on them.

## Novelty check after cycle 5 (prompted by the coordinator)

The fixed-witness method is the standard inverse-optimization move: fix the target solution and generate cuts from competitor solutions. Wang (2009, Oper. Res. Lett. 37(2):114-116) does exactly this for inverse MILP, and Bodur, Chan and Zhu (2022, INFORMS J. Comput. 34(3):1471-1488) strengthen it. So cycles 4 and 5 are not a contribution beyond the literature, only a practical baseline for our setting. Kurtz, Birbil and den Hertog (EJOR 2026) report that strong and weak counterfactuals for linear programs appear intractable while their "relative" counterfactuals are computable efficiently through a hidden convex structure. Engelhardt, Kurtz, Birbil and Ralphs (arXiv 2510.17624) show that counterfactuals for binary programs are Sigma2p-complete even with one mutable constraint. Our failure to scale exact recourse-cost explanations is consistent with these results rather than a defect peculiar to our formulation.

Status: criterion not met after five cycles. What survives is the theory already in the article and an honest negative result.

## Cycle 6: reading Kurtz, Birbil and den Hertog on relative counterfactuals

Relative counterfactuals only ask that some favoured solution be feasible with an edited cost at most α times the original optimum. There is no optimality condition, and the substitution w_j = c_j x_j of Gorissen et al. (2022) makes the problem convex for linear programs under columnwise edits and x ≥ 0.

Transfer to our setting: a relative explanation for the unit commitment model is a single MILP (binary commitments, w = ζ·X with -B X ≤ w ≤ B X), so it would scale. But it answers a weaker question, since the favoured plan need not become optimal, and the extension from LP to MILP is direct. In our weak and strong problems the same ζ also enters the competitor side, where the substitution cannot be applied, and decoupling w from ζ gives only a McCormick-type relaxation, which cycle 0 already found useless.

Conclusion: no route to a result beyond the literature in this direction after six cycles. Recommendation to Madani: stop this direction, keep the article with its negative result written plainly, and put the ambition into the separate FuturWork paper.
