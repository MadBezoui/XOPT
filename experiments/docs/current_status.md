# XOPT current state — 24 October 2026

**Version:** **1.0.2**. **Target:** Mathematical Programming Computation. This is the current state entry point; dated protocols and earlier revision notes remain historical records.

Version 1.0.2 publishes the corrections described here. All versions are archived on Zenodo (https://doi.org/10.5281/zenodo.23458561) and linked to [XOPT on GitHub](https://github.com/MadBezoui/XOPT). The original [version 1.0.1, Zenodo 23472314](https://doi.org/10.5281/zenodo.23472314) does not contain these corrections.

## Correction evidence

- The pre-correction findings and reproduction evidence are in `article/audit_20261024.md` and `article/audit_20261024/`. Their statement that A01–A12 are open describes that audit snapshot.
- The scope and integration work are governed by [the correction plan](correction_plan_20261024.md) and [the correction protocol](correction_protocol_20261024.md).
- The [scientific positioning note](scientific_positioning_20261024.md) and local `article/corrections_20261024/manuscript/changes.md` document the manuscript changes. The subsequent local report `article/wang_comparison_20261024/comparison.md` records the full-text comparison with the user-supplied Wang (2013) PDF: all 16 pages, printed pages 491–506, have now been read. The earlier full-text access limitation is resolved. This comparison recognizes Wang's more general polyhedral target, editable continuous-variable costs and duality/complementarity with exact separation and branch-and-bound; it does not claim a Wang reimplementation or matched runtime experiment. The source PDF and reading dossier remain private under `article/`.
- Historical computational bytes are bound by `experiments/provenance/frozen_manifest.json`. The 2,668 historical JSONL records remain the evidence of the original campaigns; they must not be relabeled as executions of the corrected code.
- Targeted results and current-code checks are separate under `experiments/results/corrections_20261024/`: `uc_correction.json`, `robustness_revalidated.jsonl` and `current_validation.json`. Their presence and successful validation, rather than this narrative, determine the numerical correction status.
- The UC effective analysis combines the historical 139/140 agreement with one explicitly linked correction at `0.204387890099`; it must never silently replace the original `0.252853612595` attempt or imply 140 new executions.

The local resolution ledger `article/corrections_20261024/RESOLUTION.md` and final verification evidence record the checks actually completed. The public computational gate is `experiments/results/validation_report.json`. This state note does not certify a test run, PDF build or archive inspection by itself. Replaying saved analyses, checking old witnesses with current code, recalculating selected radii and rerunning complete campaigns have distinct meanings.

## Editorial and release limits

The editorial entry point is the private local file `article/submission_readiness.md`; it is absent from computational distributions. [Author confirmations](author_signoff.md) record the declarations confirmed by the author: identity and ORCID, no funding, no competing interests, and no other submission.

Version 1.0.2 is released from the author's repository. Editable manuscript sources remain local. Public distributions must be built from an explicit allowlist and checked recursively; MIT applies to experiment code as specified by its license, not to editable article sources or all third-party data.

Older notes in `article/archive/`, `article/revision_notes_20261017.md`, `article/revision_majeure_20261017.md` and the original dated protocols preserve history. They do not supersede this state or supply missing author attestations.
