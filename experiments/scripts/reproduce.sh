#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$TASK_ROOT"
PYTHON_BIN="${PYTHON_BIN:-python3}"
JULIA_BIN="${JULIA_BIN:-julia}"
"$JULIA_BIN" --startup-file=no --project=experiments -e 'using Pkg; Pkg.instantiate()'
"$PYTHON_BIN" experiments/test/publication_policy.py
"$PYTHON_BIN" experiments/scripts/prepare_data.py
"$JULIA_BIN" --startup-file=no --project=experiments experiments/test/runtests.jl
"$JULIA_BIN" --startup-file=no --project=experiments experiments/test/robustness.jl
"$JULIA_BIN" --startup-file=no --project=experiments experiments/test/literature_reference.jl
"$JULIA_BIN" --startup-file=no --project=experiments experiments/test/anytime.jl
for profile in correctness main sensitivity scale capacity long multifoil; do
    "$JULIA_BIN" --startup-file=no --project=experiments experiments/scripts/run_experiments.jl "$profile"
done
"$JULIA_BIN" --startup-file=no --project=experiments experiments/scripts/run_robustness.jl
"$JULIA_BIN" --startup-file=no --project=experiments experiments/scripts/run_single_lever.jl
"$JULIA_BIN" --startup-file=no --project=experiments experiments/scripts/validate_saved.jl
"$JULIA_BIN" --startup-file=no --project=experiments experiments/scripts/run_external_reference.jl
"$PYTHON_BIN" experiments/scripts/analyze_external.py
"$PYTHON_BIN" experiments/scripts/analyze.py
for profile in extended compound capacity_stress; do
    "$JULIA_BIN" --startup-file=no --project=experiments experiments/scripts/run_revision.jl "$profile"
done
"$JULIA_BIN" --startup-file=no --project=experiments experiments/scripts/run_timing_repairs.jl
"$JULIA_BIN" --startup-file=no --project=experiments experiments/scripts/validate_revision.jl
"$PYTHON_BIN" experiments/scripts/analyze_revision.py
"$PYTHON_BIN" experiments/scripts/validate_artifact.py
if [[ -f article/main.tex ]]; then
    cd article
    latexmk -g -pdf -interaction=nonstopmode -halt-on-error main.tex
else
    printf '%s\n' 'Computational artifact reproduced. Manuscript sources remain local to the author; the public distribution includes the PDF only.'
fi
