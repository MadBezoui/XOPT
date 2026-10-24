#!/bin/bash
# Resumes the benchmark part of the lever study after an interruption; completed keys are skipped per worker file.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec "${PYTHON_BIN:-python3}" experiments/scripts/launch_workers.py levers-bench
