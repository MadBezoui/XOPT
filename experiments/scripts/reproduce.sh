#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$TASK_ROOT"
PYTHON_BIN="${PYTHON_BIN:-python3}"
JULIA_BIN="${JULIA_BIN:-julia}"
MODE=replay
BUILD_PDF=1
for arg in "$@"; do
    case "$arg" in
        --recompute) MODE=recompute ;;
        --no-pdf) BUILD_PDF=0 ;;
        --help|-h)
            printf '%s\n' 'Usage: reproduce.sh [--no-pdf] [--recompute]' \
                'Default: verify frozen attempts, run tests, targeted corrections, fresh witness checks and analyses.' \
                '--recompute: run full campaigns in a new/empty XOPT_RESULTS_DIR outside historical results.' \
                'New campaign records are separate; archived paper analyses are not silently replaced.'
            exit 0 ;;
        *) printf 'Unknown option: %s\n' "$arg" >&2; exit 2 ;;
    esac
done
if [[ "$MODE" == recompute ]]; then
    if [[ -z "${XOPT_RESULTS_DIR:-}" ]]; then
        printf '%s\n' 'Set XOPT_RESULTS_DIR to a new/empty separate directory.' >&2; exit 2
    fi
    # Resolve symlinks and .. before checking containment, without creating files.
    if ! DESTINATION="$("$PYTHON_BIN" - "$TASK_ROOT" "$XOPT_RESULTS_DIR" <<'PY'
from pathlib import Path
import sys
root, output = (Path(x).resolve() for x in sys.argv[1:])
history = root / 'experiments/results'
if output == history or history in output.parents:
    sys.exit('Destination must be outside historical results.')
if output.exists() and (not output.is_dir() or any(output.iterdir())):
    sys.exit('Destination must be a new/empty directory.')
print(output)
PY
    )"; then exit 2; fi
    export XOPT_RESULTS_DIR="$DESTINATION"
fi
"$JULIA_BIN" --startup-file=no --project=experiments -e 'using Pkg; Pkg.instantiate()'
"$PYTHON_BIN" experiments/scripts/prepare_data.py
"$PYTHON_BIN" -m unittest discover -s experiments/test -p 'test_*.py'
for suite in runtests robustness literature_reference anytime levers uc corrections_20261024 coordinate_cost_regression; do
    "$JULIA_BIN" --startup-file=no --project=experiments "experiments/test/$suite.jl"
done
if [[ "$MODE" == recompute ]]; then
    mkdir -p "$XOPT_RESULTS_DIR"
    for profile in correctness main sensitivity scale capacity long multifoil; do
        "$JULIA_BIN" --startup-file=no --project=experiments experiments/scripts/run_experiments.jl "$profile"
    done
    "$JULIA_BIN" --startup-file=no --project=experiments experiments/scripts/run_single_lever.jl
    "$JULIA_BIN" --startup-file=no --project=experiments experiments/scripts/run_external_reference.jl
    for profile in extended compound capacity_stress; do
        "$JULIA_BIN" --startup-file=no --project=experiments experiments/scripts/run_revision.jl "$profile"
    done
    "$JULIA_BIN" --startup-file=no --project=experiments experiments/scripts/run_timing_repairs.jl
    for campaign in audit levers uc; do
        "$PYTHON_BIN" experiments/scripts/launch_workers.py "$campaign"
    done
    printf 'New campaigns written separately to %s\n' "$XOPT_RESULTS_DIR"
    printf '%s\n' 'These records do not replace the frozen paper campaigns. Run the default replay to verify archived analyses.'
    exit 0
fi
"$JULIA_BIN" --startup-file=no --project=experiments experiments/scripts/run_corrections.jl
"$JULIA_BIN" --startup-file=no --project=experiments experiments/scripts/validate_updates.jl
for analyzer in analyze_external analyze analyze_revision analyze_audit analyze_levers analyze_uc; do
    "$PYTHON_BIN" "experiments/scripts/$analyzer.py"
done
"$PYTHON_BIN" experiments/scripts/validate_artifact.py
if [[ "$BUILD_PDF" == 1 && -f article/main.tex ]]; then
    (cd article && latexmk -g -pdf -interaction=nonstopmode -halt-on-error main.tex)
fi
printf '%s\n' 'Frozen evidence replay, targeted corrections and current witness checks passed.'
