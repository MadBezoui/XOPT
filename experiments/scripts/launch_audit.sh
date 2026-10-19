#!/bin/bash
# Launches the audit-response campaign of docs/audit_protocol_20261017.md.
cd "$(dirname "$0")/../.."
pids=()
J="${JULIA_BIN:-julia} --startup-file=no --project=experiments experiments/scripts/run_audit.jl"
mkdir -p experiments/results/audit_logs
for k in 1 2 3 4 5 6; do $J long $k 6 >> experiments/results/audit_logs/long_w$k.log 2>&1 & pids+=($!); done
for k in 1 2 3; do $J sparsity $k 3 >> experiments/results/audit_logs/sparsity_w$k.log 2>&1 & pids+=($!); done
( s=0; $J bound 1 1 >> experiments/results/audit_logs/bound_w1.log 2>&1 || s=1; $J margin 1 1 >> experiments/results/audit_logs/margin_w1.log 2>&1 || s=1; $J naive 1 1 >> experiments/results/audit_logs/naive_w1.log 2>&1 || s=1; exit $s ) & pids+=($!)
status=0; for p in "${pids[@]}"; do wait "$p" || status=1; done
[ "$status" -eq 0 ] || { echo "a worker failed" >&2; exit 1; }
echo "AUDIT CAMPAIGN DONE"
