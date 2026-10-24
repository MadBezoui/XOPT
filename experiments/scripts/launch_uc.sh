#!/bin/bash
# Runs the unit commitment studies; completed keys are skipped per worker file, so the script can be resumed.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec "${PYTHON_BIN:-python3}" experiments/scripts/launch_workers.py uc
