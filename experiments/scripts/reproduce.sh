#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$TASK_ROOT"
PYTHON_BIN="${PYTHON_BIN:-python3}"
JULIA_BIN="${JULIA_BIN:-julia}"
"$JULIA_BIN" --startup-file=no --project=experiments -e 'using Pkg; Pkg.instantiate()'
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
# Studies 2 to 4 (audit, recourse levers, unit commitment). The launchers run several
# single-thread jobs at once and resume from existing worker files.
"$JULIA_BIN" --startup-file=no --project=experiments experiments/test/levers.jl
"$JULIA_BIN" --startup-file=no --project=experiments experiments/test/uc.jl
bash experiments/scripts/launch_audit.sh
"$PYTHON_BIN" experiments/scripts/analyze_audit.py --final
bash experiments/scripts/launch_levers.sh
"$PYTHON_BIN" experiments/scripts/analyze_levers.py --final
bash experiments/scripts/launch_uc.sh
"$PYTHON_BIN" experiments/scripts/analyze_uc.py --final
"$PYTHON_BIN" experiments/scripts/validate_artifact.py
if [[ -f article/main.tex ]]; then
    cd article
    latexmk -g -pdf -interaction=nonstopmode -halt-on-error main.tex
else
    printf '%s\n' 'Computational artifact reproduced.'
fi
