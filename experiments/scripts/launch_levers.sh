#!/bin/bash
# Launches the recourse-cost lever study of docs/levers_protocol_20261017.md.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec "${PYTHON_BIN:-python3}" experiments/scripts/launch_workers.py levers
