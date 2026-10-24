# Scientific positioning after the 24 October 2026 audit

This is the current positioning note for version 1.0.2. It replaces claims of a first exact method for partial inverse MILP. A citation inventory cannot establish originality or editorial suitability.

## Primary comparisons and evidence boundaries

| Work | Established overlap with XOPT | What this revision claims | Evidence limit |
|---|---|---|---|
| [Wang (2013), JGO 55(3), 491–506](https://link.springer.com/article/10.1007/s10898-013-0036-3) | Existential partial inverse MILP with editable integer/continuous costs and general polyhedral targets; LPCC, strong duality, extreme-point oracle separation and target branching ((24)–(26), (48)–(57), Lemmas 1–4, Theorem 2; L∞ adaptation in §3.2) | Aggregate continuous completions by competing binary pattern, prove bounds for specified flow/dispatch recourse, and study shared intervention supports, margins and stability | Full 16-page user-supplied copy read, including pp. 497–501 and the 33-instance experiment on pp. 503–504. No Wang implementation or matched timing experiment was run. The source PDF stays private. |
| [Ley and Merkert (2025), JGO 93(1), 263–298](https://link.springer.com/article/10.1007/s10898-025-01529-x) | Required/forbidden follower elements; LP-representable combinatorial follower; weight increases; KKT/duality, decomposition, branch-and-bound and pessimistic semantics | Mixed binary/continuous recourse represented pattern by pattern, proved constants for the recourse structures treated, and budgets shared by lever types and periods | Open full text read, especially sections 2.1, 2.6, 2.7, 3 and 4. No implementation or performance replication was run. |
| [Engelhardt et al., arXiv:2510.17624v2](https://arxiv.org/html/2510.17624v2) | Weak/strong integer counterfactuals, cost constraint generation and outside-foil comparisons | Fixed-recourse reduction and its identity with established trajectory comparisons; editable-recourse pattern duals | Existing matched comparison is an internal reimplementation with XOPT's oracle and solver. |
| [Kurtz et al., DOI 10.1016/j.ejor.2025.06.016](https://doi.org/10.1016/j.ejor.2025.06.016) and [Lefebvre–Schmidt, DOI 10.1016/j.ejor.2026.02.007](https://doi.org/10.1016/j.ejor.2026.02.007) | Counterfactual semantics and mutable objective coefficients for LPs | Structured mixed-integer recourse study, with explicit computational limitations | Metadata and comparisons were verified in the retained audit; this note does not claim a new numerical comparison. |

The private local comparison is `article/wang_comparison_20261024/comparison.md`; its source identity is recorded alongside the user-supplied PDF. That file and the PDF are absent from computational distributions. Earlier public-page retrieval notes remain historical. The previous full-text access limitation is resolved; neither author approval nor permission to redistribute the supplied paper is inferred.

## Consequences of the full Wang comparison

For a fixed capacity scenario and fixed admissible costs, changing max/min sign and concatenating binary and continuous variables maps XOPT's exact weak witness condition to Wang's existential optimality condition. His target polyhedron can also constrain continuous variables, so partial binary foils do not enlarge that target class. His general forward matrices can already contain temporal balances.

The complete intervention programs differ: XOPT imposes edit boxes, parameter/period support budgets and penalties, and selects a finite capacity scenario. Wang's published objective is a weighted L1 or L∞ norm. He assumes a feasible target and permits the initial edit Δc = −c (pp. 493, 498), while XOPT's admissible edits can exclude it. Prescribed positive gaps against nonfoils and additive approximate optimality are not explicitly formulated in his studied model; no general priority on counterfactual semantics is inferred.

Wang already replaces a continuous cost–witness product by a dual expression (p. 499, (53)); duality and complementarity alone are inherited tools. His LPCC node problems and extreme-point cuts differ from XOPT's pattern dual blocks and bounded MILP representation. Both methods still use complementarity and branching. Wang also discusses the possible nonexistence of finite big-M values and cites a parameter-free method (p. 495), so no blanket big-M advantage is asserted.

Theorem 2 and its L∞ adaptation require global subproblem solves; they are distinct from the reported TOMLAB/KNITRO implementation. The 33 modified MIPLIB experiments use different targets, intervention objectives, hardware and solvers. Their timings are reported evidence, not an XOPT benchmark. The actual matched comparator remains Engelhardt's scheme for fixed recourse costs.

## Defensible scope

XOPT studies binary activation patterns with continuous linear recourse, bounded cost edits and a finite capacity menu. For editable recourse, each competitor pattern contributes a dual cut and the preferred pattern uses optimality conditions. The paper proves usable constants for its specified flow and no-ramp dispatch structures. It does not assert that KKT reformulation, partial foils, weak/strong semantics, finite partial inverse algorithms, or hardness with an easy forward model originated here.

The temporal result concerns the number of edited periods: the reduction preserves hitting-set approximation ratios. It is more specific than the already established observation that partial inverse problems can be hard with an easy follower. Grouped supports and shared budgets are modeled explicitly across distinct cost classes and capacity edits.

The computational contribution consists of reproducible comparisons and limits: exhaustive small cases, scenario-specific competitors, temporal budgets, radius calibration, and failure to resolve the 96 marginal-lever UC benchmark runs within 300 seconds. Retail and hospital costs and capacities are constructed; the NHS observations are workload profiles, not patient trajectories. UC is a scaled single-node subset, and marginal-cost studies remove ramps as required by the dispatch argument.

## Mathematical and numerical qualifications

Weak semantics alone does not imply zero radius. A fixed weak witness tied with a nonfoil has radius zero; one strictly dominating every nonfoil has positive radius. In the analytical example the nominal foil `y₂=0` has radius `2/3`. The 25 zero weak radii in the main study describe its observed witnesses. A multiplicative margin gives a positive relative gap only on a strictly positive witness-cost domain. Empty foil/nonfoil sets are handled before subtracting their nominal costs in the coordinate bound.

The original UC dual count is 139/140. Its incorrect objective `0.252853612595` is retained; one separately identified correction reaches `0.204387890099` and makes the effective count 140/140. A feasible witness does not by itself certify the master lower bound or optimality. Historical enumeration exceeded the intended 300-second budget in 41/140 UC cases (maximum 6581.36 seconds), so these timings cannot support equal-budget comparisons. Future deadlines and targeted corrections are governed by `correction_protocol_20261024.md`.

Original records, replayed analyses, current-code witness checks and targeted recomputations are different evidence classes. No complete rerun, exact rational certificate, author approval, corrected public archive, new DOI or journal submission is claimed.
