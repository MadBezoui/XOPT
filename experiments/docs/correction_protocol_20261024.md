# Audit correction and validation protocol — 24 October 2026

This addendum is fixed before the correction computations. It does not rewrite the dated original protocols or claim a new execution of all campaigns.

## Preserved evidence

The 43 original JSONL files (2,668 records) remain byte-identical. Their SHA-256 identities and 47 computational source identities are bound by `experiments/provenance/frozen_manifest.json`; the original code bytes are in `experiments/provenance/objects/`. This snapshot was captured retrospectively, before corrections. It establishes the preserved bytes, not previously missing execution-time provenance. No manuscript source is in this snapshot.

## UC correction

Re-solve only `tiny_2020-07-06_s1_h15|[(3, 2, 1)]|strong|M` with the corrected supported dual-cut implementation, the saved instance/foil/margin, one solver thread and 120 seconds. Check the returned physical witness and cost comparison freshly. Its intervention objective must agree within 1e-6 with the separately enumerated historical optimum 0.20438789009860472. Save the new result, oracle validation, current producing-source hashes, timestamp and original file/line hashes as `experiments/results/corrections_20261024/uc_correction.json`. A timeout or disagreement is unresolved and blocks final validation. Preserve the original 0.25285361259450123 attempt. Analysis applies the correction explicitly and reports the historical 139/140 agreement alongside effective 140/140; these are not 140 new solves.

## Radius provenance

Recompute the fixed-witness radii for the same 50 successful main-study CCG witnesses, without replacing `robustness.jsonl`. Use rho_max 0.25, radius resolution 1e-5 and sign tolerance of the implementation, with 60 seconds per radius and one solver thread. Save all outcomes in `robustness_revalidated.jsonl` under the correction directory. Each row binds the core, radius module, driver, this protocol and the complete main input file plus the individual original record. Reuse is allowed only if every producing source, option and input fingerprint matches. Unresolved outcomes remain unresolved and block the completed numerical summary.

## Current witness validation

Run the corrected validators on every retained successful witness from the primary, external, revision, audit, lever and UC studies. Check integrality and the intervention objective directly as well as the fresh follower comparison. For the deliberately naive-capacity variant, retain and reproduce the original invalid-witness expectations instead of treating these negative controls as valid explanations. Each check receives at most 60 seconds per forward call; any inability to establish the expected result is reported and blocks the gate. Save `current_validation.json`, including exact input identities and current source identities. This is same-model, same-solver Float64 validation, not an independently coded model or exact proof certificate. It does not establish minimality of every intervention.

## Deadlines and concurrency

The historical UC enumeration reference did not enforce its stated 300-second deadline: 41 of 140 cases exceeded it, with maximum 6581.360868930817 seconds. These full reference solutions and their actual durations are retained as a documented protocol deviation. Corrected enumeration APIs enforce one global deadline covering preprocessing and inner solves; interrupted enumeration is never classified as infeasible. Future campaign launchers cap total child processes through XOPT_WORKERS (default 2) while preserving shard identities. Historical timing records are not relabelled as measurements under the new launch policy.

## Reproduction and publication

Default reproduction replays archived attempts, regenerates their analyses, computes the explicit corrections and performs current-code numerical checks. Recomputing a campaign uses a new separate result directory and must never overwrite the frozen originals. These corrections are published as version 1.0.2. The DOI of version 1.0.1 identifies the original archive, without them. Public packaging uses the explicit computational allowlist, validates archives and reachable history, and excludes all editable manuscript material. No upload or public Git mutation is part of this correction protocol.
