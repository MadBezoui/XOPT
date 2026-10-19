# Closest external exact method: scope and provenance

The reference is Engelhardt, Kurtz, Birbil and Ralphs, *Counterfactual Explanations for Integer Optimization Problems*, arXiv:2510.17624v2 (5 January 2026), Algorithm 1 / equation (7) for cost edits and equation (14) for outside-foil separation.

Primary sources:

- https://arxiv.org/html/2510.17624v2
- https://zenodo.org/records/18110317 — archived author software v1.1
- https://github.com/felix-engelhardt/CE4IO/tree/v1.1

The archive was downloaded and inspected on 16 October 2026. Its SHA-256 is `4ebc2cb9f334ab51bb24809bfdaaf64e6a91c2b00de6fb8acbe3e559ac18d90b`; Zenodo's advertised MD5 is `01015821de8baa1662a70f76da8a0026`. Its directory identifies revision `ce443d5`. The original code license is AGPL-3.0-only.

The released `main.py:run_cf` and `solver.py:solve_counterfactual_subproblem` implement integer constraint-coefficient changes on cover problems, enumerating target objective levels. They do not expose the paper's cost-only Algorithm 1 as an executable method. Running their default experiment against XOPT would compare different intervention domains and forward problems.

`src/literature_cg.jl` therefore implements the **published cost algorithm independently**. It is not described as a run of the author software. It constructs its own inverse master and loop, and stores full competitor trajectories; it does not call XOPT's inverse master, cut routine or explanation algorithm. Both implementations share the physical model constructor and forward oracle, use HiGHS with identical settings, and solve the same action domain. This isolates the comparison of the inverse formulations but does not provide independently coded forward-model validation.

Mapping: the favored set is our binary foil; the mutable set includes our bounded continuous cost edits and binary support constraints; the distance is weighted L1 plus support charges. The unit strictness in equation (14) is replaced by the declared positive margin 0.02. Continuous operating costs remain fixed. Thus the compared margin problem is the stated margin specialization, not unrestricted classical strongness over a continuous parameter domain.

The manuscript proves that, conditional on an optimal forward solution, its continuous cost equals the pattern recourse value. The two algorithms therefore generate mathematically identical comparisons for identical patterns. This benchmark can corroborate objective/status agreement; it cannot establish a novel algorithm or a new complexity result.

Protocol: all 60 CCG queries from the main study and all 24 two-literal queries; no feasibility-based selection. Rerun both methods in shuffled paired order, alternate first method across queries, warm up both modes, use one solver thread and 15 seconds per call. Record every status, bound, witness, trace, source hash and elapsed time. Validate every successful witness freshly. Summary reports all denominators, disagreements and jointly solved objective discrepancies. Runtime medians are descriptive implementation measurements, not a superiority test. These 168 supplementary runs are separate from the 320 primary runs.

Reproduce with `julia --startup-file=no --project=experiments experiments/scripts/run_external_reference.jl`. The comparison needs no commercial solver and no execution or import of the AGPL author code. The author code is not redistributed. `experiments/vendor/provenance.json` records the archive URL, DOI, retrieval date and SHA-256 hashes of the inspected files, so the original can be obtained and checked from Zenodo.
