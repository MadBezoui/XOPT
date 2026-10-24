#!/bin/bash
# Runs the unit commitment studies; completed keys are skipped per worker file, so the script can be resumed.
cd "$(dirname "$0")/../.."
pids=()
J="${JULIA_BIN:-julia} --startup-file=no --project=experiments experiments/scripts/run_uc.jl"
mkdir -p experiments/results/uc_logs
for k in 1 2 3; do $J enum $k 3 >> experiments/results/uc_logs/enum_w$k.log 2>&1 & pids+=($!); done
for k in 1 2 3 4 5 6; do $J bench $k 6 >> experiments/results/uc_logs/bench_w$k.log 2>&1 & pids+=($!); done
status=0; for p in "${pids[@]}"; do wait "$p" || status=1; done
[ "$status" -eq 0 ] || { echo "a worker failed" >&2; exit 1; }
echo "UC DONE"
