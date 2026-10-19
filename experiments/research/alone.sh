#!/bin/bash
# Reruns selected timing jobs one at a time with a longer limit, to separate contention from hardness.
cd "$(dirname "$0")/.."
out=research/alone.log;: > $out
for j in 1 2 5; do LIMIT=1200 julia --startup-file=no --project=. research/cycle_time.jl $j >> $out 2>&1; done
echo "ALONE DONE" >> $out
