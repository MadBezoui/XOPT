# XOPT v1.0.0 — Research Artifact

[Repository](https://github.com/MadBezoui/XOPT) · [Release](https://github.com/MadBezoui/XOPT/releases/tag/v1.0.0) · [README](README.md)

Software, datasets, and complete numerical experiments accompanying research on sparse temporal counterfactual explanations for mixed-integer optimization with fixed continuous recourse.

## Contents

- **Core implementation** (`experiments/src/`): exact CCG algorithm, multicut, enumeration, anytime bounds, stability radius, cost levers, and unit commitment models.
- **Data** (`data/`): raw and processed datasets (hospital attendance, retail operations, and PGLib-UC instances) with provenance metadata and SHA-256 checksums.
- **Results** (`experiments/results/`): complete result records, summaries, and verification traces.
- **Reproduction**: reproducible execution scripts (`experiments/scripts/reproduce.sh`) and automated tests (`experiments/test/`).

All original code is available under the MIT License.
