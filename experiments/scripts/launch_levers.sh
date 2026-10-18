#!/bin/bash
# Launches the recourse-cost lever study of docs/levers_protocol_20261017.md under an idle-sleep inhibitor.
cd "$(dirname "$0")/../.."
J="julia --startup-file=no --project=experiments experiments/scripts/run_levers.jl"
mkdir -p experiments/results/levers_logs
for k in 1 2; do $J enum $k 2 > experiments/results/levers_logs/enum_w$k.log 2>&1 & done
for k in 1 2 3 4 5 6; do $J bench $k 6 > experiments/results/levers_logs/bench_w$k.log 2>&1 & done
wait
echo "LEVER STUDY DONE"
