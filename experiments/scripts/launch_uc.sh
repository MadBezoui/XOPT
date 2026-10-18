#!/bin/bash
# Runs the unit commitment studies; completed keys are skipped per worker file, so the script can be resumed.
cd "$(dirname "$0")/../.."
J="julia --startup-file=no --project=experiments experiments/scripts/run_uc.jl"
mkdir -p experiments/results/uc_logs
for k in 1 2 3; do $J enum $k 3 >> experiments/results/uc_logs/enum_w$k.log 2>&1 & done
for k in 1 2 3 4 5 6; do $J bench $k 6 >> experiments/results/uc_logs/bench_w$k.log 2>&1 & done
wait
echo "UC DONE"
