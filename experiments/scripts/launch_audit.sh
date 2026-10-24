#!/bin/bash
# Launches the audit-response campaign of docs/audit_protocol_20261017.md.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec "${PYTHON_BIN:-python3}" experiments/scripts/launch_workers.py audit
