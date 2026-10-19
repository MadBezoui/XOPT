# XOPT v1.0.1 — Research Artifact

[Repository](https://github.com/MadBezoui/XOPT) · [Release](https://github.com/MadBezoui/XOPT/releases/tag/v1.0.1) · [README](README.md)

Software, datasets, and complete numerical experiments accompanying research on sparse temporal counterfactual explanations for mixed-integer planning with continuous recourse, including editable recourse costs.

## Contents

- **Core implementation** (`experiments/src/`): exact CCG algorithm, multicut, enumeration, anytime bounds, stability radius, cost levers, and unit commitment models.
- **Data**: raw and processed hospital and retail datasets in `data/`, and PGLib-UC instances in `experiments/data/pglib_uc/`, with provenance metadata and SHA-256 checksums.
- **Results** (`experiments/results/`): complete result records, summaries, and verification traces.
- **Reproduction**: reproducible execution scripts (`experiments/scripts/reproduce.sh`) and automated tests (`experiments/test/`).

All original code is available under the MIT License. Release v1.0.0 also contained an unmodified copy of the CE4IO v1.1 author code under AGPL-3.0-only, which v1.0.1 no longer distributes. Version 1.0.1 also completes `reproduce.sh` for all studies and restores the analysis scripts that produce the published figures.
