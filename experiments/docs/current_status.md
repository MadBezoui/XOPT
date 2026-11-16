# XOPT state — version 1.0.3

**Reference release:** **1.0.3**. It contains the checks made after version 1.0.2. The manuscript targets Mathematical Programming Computation. Dated protocols and earlier revision notes remain historical records.

Version 1.0.2 contains the correction records dated 24 October, not the later outputs dated 28 October. The published versions are archived on Zenodo (https://doi.org/10.5281/zenodo.23458561) and linked to [XOPT on GitHub](https://github.com/MadBezoui/XOPT). The original [version 1.0.1, Zenodo 23472314](https://doi.org/10.5281/zenodo.23472314) does not contain the 24 October corrections.

## Correction evidence

- The pre-correction findings and reproduction evidence are in `article/audit_20261024.md` and `article/audit_20261024/`. Their statement that A01–A12 are open describes that audit snapshot.
- The correction computations are governed by [the correction protocol](correction_protocol_20261024.md). The local internal implementation plan is not part of public distributions.
- The [scientific positioning note](scientific_positioning_20261024.md) and local `article/corrections_20261024/manuscript/changes.md` document the manuscript changes. The subsequent local report `article/wang_comparison_20261024/comparison.md` records the full-text comparison with the user-supplied Wang (2013) PDF: all 16 pages, printed pages 491–506, have now been read. The earlier full-text access limitation is resolved. This comparison recognizes Wang's more general polyhedral target, editable continuous-variable costs and duality/complementarity with exact separation and branch-and-bound; it does not claim a Wang reimplementation or matched runtime experiment. The source PDF and reading dossier remain private under `article/`.
- Historical computational bytes are bound by `experiments/provenance/frozen_manifest.json`. The 2,668 historical JSONL records remain the evidence of the original campaigns; they must not be relabeled as executions of the corrected code.
- The original three targeted correction outputs under `experiments/results/corrections_20261024/` are preserved without relabelling. An audit found that their recorded protocol fingerprint differs from the protocol file distributed in version 1.0.2; the exact protocol bytes and the seven other bound source files have since been recovered and preserved in `experiments/provenance/corrections_20261024/`. This recovery is retrospective and is not proof of capture at execution time. A separately identified campaign under `experiments/results/corrections_20261028/` binds the current sources and inputs. Its saved outputs and the final gate, not this narrative, determine validation status.
- Version 1.0.3 records separate checks reconstructing a witness for each of the 94 historical one-coordinate interventions whose original witnesses were not retained. A reconstructed witness is not the original witness and this check does not prove intervention optimality. The default replay checks the supplied evidence before tests and does not rewrite correction records or regenerate historical analyses.
- The UC effective analysis combines the historical 139/140 agreement with one explicitly linked correction at `0.204387890099`; it must never silently replace the original `0.252853612595` attempt or imply 140 new executions.

The local resolution ledger `article/corrections_20261024/RESOLUTION.md` is historical. The computational gate is `experiments/scripts/validate_artifact.py`; an older saved `validation_report.json` does not certify the current working copy. This state note does not certify a test run, PDF build or archive inspection by itself. Checking saved evidence, rebuilding an admissible witness for a recorded intervention, recalculating selected radii and rerunning complete campaigns have distinct meanings.

## Editorial and release limits

The computational distribution excludes editorial files, author confirmations and exploratory work. The public releases up to 1.0.2 nevertheless contain internal documents and require separate remediation; version 1.0.3 does not remove those copies. Author declarations and journal submission remain the author's responsibility.

Version 1.0.3 is released from the author's repository. Editable manuscript sources remain local. Public distributions must be built from an explicit allowlist and checked recursively; MIT applies to experiment code as specified by its license, not to editable article sources or all third-party data.

Older notes in `article/archive/`, `article/revision_notes_20261017.md`, `article/revision_majeure_20261017.md` and the original dated protocols preserve history. They do not supersede this state or supply missing author attestations.
