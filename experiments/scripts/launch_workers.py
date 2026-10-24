#!/usr/bin/env python3
"""Bound Julia concurrency without changing historical study/shard identities."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGNS = {
    "audit": ("run_audit.jl", "audit_logs",
              (("long", 6), ("sparsity", 3), ("bound", 1),
               ("margin", 1), ("naive", 1)), "AUDIT CAMPAIGN DONE"),
    "levers": ("run_levers.jl", "levers_logs",
               (("enum", 2), ("bench", 6)), "LEVER STUDY DONE"),
    "uc": ("run_uc.jl", "uc_logs",
           (("enum", 3), ("bench", 6)), "UC DONE"),
    "levers-bench": ("run_levers.jl", "levers_logs",
                     (("bench", 6),), "LEVER BENCH DONE"),
}


def worker_limit():
    value = os.environ.get("XOPT_WORKERS", "2")
    if not value.isascii() or not value.isdecimal() or int(value) < 1:
        raise ValueError("XOPT_WORKERS must be a positive integer")
    return int(value)


def run_job(job):
    command, logfile = job
    label = " ".join(command[-3:])
    try:
        logfile.parent.mkdir(parents=True, exist_ok=True)
        with logfile.open("ab") as output:
            result = subprocess.run(command, cwd=ROOT, stdout=output,
                                    stderr=subprocess.STDOUT, check=False)
        if result.returncode:
            print(f"Worker {label} failed with exit {result.returncode}; log: {logfile}",
                  file=sys.stderr, flush=True)
        return result.returncode
    except OSError as error:
        print(f"Worker {label} could not run: {error}", file=sys.stderr, flush=True)
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", choices=CAMPAIGNS)
    args = parser.parse_args(argv)
    try:
        limit = worker_limit()
    except ValueError as error:
        parser.error(str(error))
    driver, logdir, shards, completed = CAMPAIGNS[args.campaign]
    results = Path(os.environ.get("XOPT_RESULTS_DIR", "experiments/results"))
    if not results.is_absolute():
        results = ROOT / results
    julia = os.environ.get("JULIA_BIN") or "julia"
    jobs = [
        ([julia, "--startup-file=no", "--project=experiments",
          f"experiments/scripts/{driver}", study, str(index), str(count)],
         results / logdir / f"{study}_w{index}.log")
        for study, count in shards for index in range(1, count + 1)
    ]
    # The configured pool changes concurrency, never the driver's shard count.
    # Run all independent shards even after a failure, then propagate any failure.
    with ThreadPoolExecutor(max_workers=min(limit, len(jobs))) as pool:
        statuses = list(pool.map(run_job, jobs))
    if any(statuses):
        return 1
    print(completed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
