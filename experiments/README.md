# XOPT computational workspace — version 1.0.2

The current integration guides are the [French root README](../README.md) and [English root README](../README.en.md). Commands below run from the **repository root**, not from this directory.

The original public artifact is [version 1.0.1, Zenodo 23472314](https://doi.org/10.5281/zenodo.23472314). Version 1.0.2 adds the corrected code, targeted reruns and current-code validation described here. See [current status](docs/current_status.md), [correction protocol](docs/correction_protocol_20261024.md) and [release state](RELEASE.md).

## Standard replay

With Julia 1.11, the lockfile and Python 3.11 dependencies installed:

```bash
PYTHON_BIN="$PWD/.venv/bin/python" bash experiments/scripts/reproduce.sh --no-pdf
```

The default path runs eight Julia suites and Python unit tests, targeted UC/radius correction work, fresh `validate_updates.jl` witness checks, six analyses and final artifact validation. Valid cached UC/radius corrections can be reused only when all producing-code, option and input hashes agree. `--no-pdf` skips local LaTeX compilation. This workflow preserves all 2,668 original JSONL records and does not rerun every campaign.

Historical identities are in `experiments/provenance/frozen_manifest.json`, with source bytes in `experiments/provenance/objects/`. This is a retrospective snapshot, not a repair of missing original execution-time provenance. Separate outputs under `experiments/results/corrections_20261024/` bind current code and inputs: `uc_correction.json`, `robustness_revalidated.jsonl` and `current_validation.json`. Fresh witness verification does not certify intervention minimality.

## New driver campaigns

```bash
XOPT_RESULTS_DIR=/tmp/xopt-recompute-20261024 XOPT_WORKERS=2 \
  PYTHON_BIN="$PWD/.venv/bin/python" \
  bash experiments/scripts/reproduce.sh --recompute --no-pdf
```

Use a new directory outside `experiments/results/`. This mode reruns driver campaigns; it does not compute radii of the new witnesses. Recalculating the 50 historical witness radii is a separate replay step. New statuses and record counts can differ; 2,668 new records are not guaranteed. Do not move or overwrite historical records. `XOPT_WORKERS` limits concurrency (positive integer, default 2) without redistributing historical shard identifiers; failed children propagate an error. `JULIA_BIN` and `PYTHON_BIN` are executable paths and may contain spaces. New timing and timeout outcomes can differ from archived measurements.

The original 300-second enumeration deadline was not enforced: 41/140 UC references exceeded it, maximum 6581.36 seconds. Their observed objectives/durations remain historical evidence; corrected enumeration APIs enforce a global deadline and retain unresolved outcomes explicitly.

## Verification entry points

```bash
python3 -m unittest discover -s experiments/test -p 'test_*.py' -v
julia --startup-file=no --project=experiments experiments/test/runtests.jl
julia --startup-file=no --project=experiments experiments/test/robustness.jl
julia --startup-file=no --project=experiments experiments/test/literature_reference.jl
julia --startup-file=no --project=experiments experiments/test/anytime.jl
julia --startup-file=no --project=experiments experiments/test/levers.jl
julia --startup-file=no --project=experiments experiments/test/uc.jl
julia --startup-file=no --project=experiments experiments/test/corrections_20261024.jl
julia --startup-file=no --project=experiments experiments/test/coordinate_cost_regression.jl
```

The root workflow supplies the correction files before invoking the fresh validation and final gate. Run `reproduce.sh` for that complete ordering. An individual passing suite is narrower evidence.

The UC analysis preserves the original 139/140 agreements and adds one identified correction to reach an effective 140/140; it does not claim a new 140-case campaign. Original weak radii equal to zero are observations about tied witnesses, not a theorem about every weak explanation. Computation remains Float64/tolerance based.

See [license scope](LICENSING.md) and [MIT](LICENSE). Editable article sources are local and excluded from any public distribution; releases must use the explicit allowlist and inspect archive contents.
