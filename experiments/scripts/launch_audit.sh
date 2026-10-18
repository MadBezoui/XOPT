#!/bin/bash
# Launches the audit-response campaign of docs/audit_protocol_20261017.md under an idle-sleep inhibitor.
cd "$(dirname "$0")/../.."
J="julia --startup-file=no --project=experiments experiments/scripts/run_audit.jl"
mkdir -p experiments/results/audit_logs
for k in 1 2 3 4 5 6; do $J long $k 6 > experiments/results/audit_logs/long_w$k.log 2>&1 & done
for k in 1 2 3; do $J sparsity $k 3 > experiments/results/audit_logs/sparsity_w$k.log 2>&1 & done
( $J bound 1 1 > experiments/results/audit_logs/bound_w1.log 2>&1; $J margin 1 1 > experiments/results/audit_logs/margin_w1.log 2>&1; $J naive 1 1 > experiments/results/audit_logs/naive_w1.log 2>&1 ) &
wait
echo "AUDIT CAMPAIGN DONE"
