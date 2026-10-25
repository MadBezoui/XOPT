# XOPT: constraint generation for temporal counterfactuals in mixed-integer planning

XOPT studies bounded parameter changes that make a preferred property optimal in plans with binary activations and continuous recourse. Cost levers and a finite capacity menu share period and parameter budgets.

**Version 1.0.2**, which includes the corrections of 24 October 2026. All versions are archived on Zenodo, https://doi.org/10.5281/zenodo.23458561, which resolves to the latest. The original [version 1.0.1, DOI 10.5281/zenodo.23472314](https://doi.org/10.5281/zenodo.23472314) does not contain these corrections. See [current status](experiments/docs/current_status.md), [the correction addendum](experiments/docs/correction_protocol_20261024.md) and [the French guide](README.md).

## Environment and layout

Use Julia 1.11 with `experiments/Manifest.toml` and Python 3.11 with the direct versions pinned in [requirements.txt](experiments/requirements.txt). HiGHS is installed through the Julia environment and needs no commercial license.

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r experiments/requirements.txt
```

Run subsequent commands from the repository root. `JULIA_BIN` and `PYTHON_BIN` each name an executable and support paths containing spaces. Optional local manuscript compilation needs LaTeX and `latexmk`; editable manuscript sources are absent from the public computational artifact.

`experiments/src/` contains the Julia models, oracles and algorithms; `scripts/` the drivers, bounded launchers, analyses and validators; `test/` eight Julia suites and Python behavioral tests; `docs/` the protocols and current state. `uc.jl` is the supported UC implementation and `uc2.jl` holds exploratory variants. The literature comparator is an internal matched reimplementation using XOPT's models and solver, not an independent execution of the authors' software.

Raw UCI/NHS observations and processed series are in `data/`; UC inputs are in `experiments/data/pglib_uc/`. Historical records are in `experiments/results/`. Retrospectively preserved source objects are in `experiments/provenance/objects/`, bound by `frozen_manifest.json`; separate corrections and current-code checks are in `experiments/results/corrections_20261024/`.

## Replay and current-code validation

```bash
PYTHON_BIN="$PWD/.venv/bin/python" bash experiments/scripts/reproduce.sh --no-pdf
```

The default workflow preserves the **43 historical JSONL files and 2,668 records**. It instantiates the environment, runs eight Julia suites and Python unit tests, obtains the targeted UC correction and 50 radius recalculations, freshly checks retained witnesses with corrected validators, regenerates six analyses and runs the complete final gate. Targeted UC/radius outputs may be reused only when their code, options and input fingerprints match. `validate_updates.jl` performs separate current-code witness checks; `current_validation.json` records their actual count and outcome.

Replaying analyses is not rerunning the campaigns. The original source objects were captured retrospectively before correction: they preserve and identify bytes, without creating missing execution-time provenance. The 108 original coordinate-baseline records and 50 original radius records retain their initial provenance limitations.

The erroneous historical UC attempt at `0.252853612595` remains intact. A separate correction reaches `0.204387890099`; analysis reports 139/140 historical agreements and 140/140 after the one identified correction, not 140 new solves. Recalculated radii do not replace `robustness.jsonl`. Current witness checks establish admissibility and cost comparisons, not the global optimality of every intervention.

Without `--no-pdf`, the script may compile the manuscript if its local sources are present. Passing tests or building a PDF is not author approval, an editorial attestation or an exact rational certificate.

## Rerunning driver campaigns in a separate directory

Select a **new result directory outside the historical result tree**:

```bash
XOPT_RESULTS_DIR=/tmp/xopt-recompute-20261024 XOPT_WORKERS=2 \
  PYTHON_BIN="$PWD/.venv/bin/python" \
  bash experiments/scripts/reproduce.sh --recompute --no-pdf
```

This reruns the driver campaigns and produces new attempts in a distinct directory. It does not compute radii for the new witnesses: the 50 historical witness radii belong to the separate targeted replay step. The number and statuses of new attempts may differ; no total of 2,668 new records is promised. Do not move, overwrite or relabel the historical JSONL files. Solver paths, time-limited outcomes and timings may change with corrected code, hardware and load. Driver campaigns can take substantial time and are separate from standard replay.

`XOPT_WORKERS` is a positive integer, default 2, limiting concurrent launcher children. Historical shard identifiers and counts are preserved. Any child failure makes its launcher fail, including resume. Corrected enumeration uses a global deadline. Historically 41/140 UC enumeration runs exceeded the intended 300 seconds, with maximum 6581.36 seconds; these timings remain a documented protocol deviation and cannot support an equal-deadline comparison.

## Scope, interpretation and distribution

Retail and NHS observations are real but their planning costs, capacities and foils are constructed. NHS data are workload profiles, not patient trajectories. UC is a scaled single-node subset, and marginal-cost levers require dispatch without ramps. The 96 unresolved marginal-lever UC runs remain negative results. Shared windows support descriptive rather than independent-sample inference.

`SOLVER_VALIDATED` is a numerical master/oracle-bound acceptance status. `FEASIBLE_*` retains an admissible explanation without established optimality. `TIME_LIMIT` is unresolved and may retain an explicitly reported incumbent; it never proves infeasibility. `SOLVER_INFEASIBLE` is the solver's numerical infeasibility conclusion. All checks use Float64 and tolerances, with no rational MILP proof certificate exported.

The [positioning note](experiments/docs/scientific_positioning_20261024.md) acknowledges prior partial inverse MILP, including Wang (2013), and partial inverse combinatorial work by Ley–Merkert (2025). The user-supplied Wang PDF has now been read in full: 16 pages, printed pages 491–506. The formal comparison recognizes Wang's more general polyhedral target, editable continuous-variable costs, and combination of duality, complementarity, separation and branch-and-bound. XOPT studies temporal sparsity, aggregation by binary pattern and proved constants for the specified recourse structures; no first exact general partial inverse MILP method or general superiority claim is made. No Wang implementation or matched runtime experiment was run, and the author must still assess scientific originality. The detailed local report is `article/wang_comparison_20261024/comparison.md`; the supplied PDF and reading dossier remain private and outside computational distributions.

See [MIT code license](experiments/LICENSE), [license scope](experiments/LICENSING.md), [citation](CITATION.cff) and [release state](experiments/RELEASE.md). Inputs retain their own licenses. Editable manuscript material, including LaTeX, bibliography, templates and Word sources, stays local across Git history, branches, tags, releases and archives. Public packaging requires an explicit allowlist and archive inspection; this local correction work does not publish a new artifact.
