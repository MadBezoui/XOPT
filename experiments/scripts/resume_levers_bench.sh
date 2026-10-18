#!/bin/bash
# Resumes the benchmark part of the lever study after an interruption; completed keys are skipped per worker file.
cd "$(dirname "$0")/../.."
J="julia --startup-file=no --project=experiments experiments/scripts/run_levers.jl"
mkdir -p experiments/results/levers_logs
for k in 1 2 3 4 5 6; do $J bench $k 6 >> experiments/results/levers_logs/bench_w$k.log 2>&1 & done
wait
echo "LEVER BENCH DONE"
