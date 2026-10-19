#!/bin/bash
# Usage: run_cycle.sh <name> [flag=value ...]; runs the 12 timing jobs, 6 at a time, detached-safe.
cd "$(dirname "$0")/.."
name=$1;shift
out=research/$name.log;: > $out
for j in $(seq 1 12); do
  julia --startup-file=no --project=. research/cycle_time.jl $j "$@" >> $out 2>&1 &
  [ $((j%6)) -eq 0 ] && wait
done
wait;echo "CYCLE DONE" >> $out
