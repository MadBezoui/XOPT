"""Run the actual launchers with lightweight executable workers, never Julia campaigns."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


class LaunchWorkerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="xopt_workers_")
        self.addCleanup(self.directory.cleanup)
        self.temporary = Path(self.directory.name)
        self.root = self.temporary / "workspace with spaces"
        scripts = self.root / "experiments/scripts"
        scripts.mkdir(parents=True)
        for filename in ("launch_audit.sh", "launch_levers.sh", "launch_uc.sh",
                         "resume_levers_bench.sh", "launch_workers.py"):
            if (SCRIPTS / filename).exists():
                shutil.copy2(SCRIPTS / filename, scripts / filename)
        self.state = self.temporary / "state.json"
        self.state.write_text(json.dumps({"active": 0, "maximum": 0, "jobs": []}))
        self.worker = self.temporary / "fakejulia"
        self.worker.write_text("#!" + sys.executable + "\n" + textwrap.dedent('''\
            import fcntl
            import json
            import os
            import sys
            import time

            def update(start):
                with open(os.environ["WORKER_STATE"], "r+") as stream:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
                    state = json.load(stream)
                    state["active"] += 1 if start else -1
                    state["maximum"] = max(state["maximum"], state["active"])
                    if start:
                        state["jobs"].append(sys.argv[1:])
                    stream.seek(0)
                    json.dump(state, stream)
                    stream.truncate()

            update(True)
            try:
                time.sleep(0.15)
                if "|".join(sys.argv[-3:-1]) == os.environ.get("FAIL_WORKER"):
                    sys.exit(9)
            finally:
                update(False)
            '''))
        self.worker.chmod(0o755)

    def launch(self, filename, workers=None, fail=None, worker=None):
        env = os.environ.copy()
        env.pop("XOPT_WORKERS", None)
        env.update(JULIA_BIN=str(worker or self.worker), PYTHON_BIN=sys.executable,
                   WORKER_STATE=str(self.state),
                   XOPT_RESULTS_DIR=str(self.temporary / "saved results"))
        if workers is not None:
            env["XOPT_WORKERS"] = str(workers)
        if fail is not None:
            env["FAIL_WORKER"] = fail
        else:
            env.pop("FAIL_WORKER", None)
        result = subprocess.run(
            ["bash", str(self.root / "experiments/scripts" / filename)],
            cwd=self.temporary, env=env, text=True, capture_output=True, timeout=20,
        )
        return result, json.loads(self.state.read_text())

    def test_default_concurrency_is_bounded_without_redistributing_historical_shards(self):
        result, state = self.launch("launch_audit.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLessEqual(state["maximum"], 2)
        self.assertEqual(state["active"], 0)
        expected = {("long", str(i), "6") for i in range(1, 7)}
        expected |= {("sparsity", str(i), "3") for i in range(1, 4)}
        expected |= {("bound", "1", "1"), ("margin", "1", "1"), ("naive", "1", "1")}
        self.assertEqual({tuple(job[-3:]) for job in state["jobs"]}, expected)
        self.assertEqual(len(state["jobs"]), 12)

    def test_configured_single_worker_runs_every_uc_shard(self):
        result, state = self.launch("launch_uc.sh", workers=1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state["maximum"], 1)
        expected = {("enum", str(i), "3") for i in range(1, 4)}
        expected |= {("bench", str(i), "6") for i in range(1, 7)}
        self.assertEqual({tuple(job[-3:]) for job in state["jobs"]}, expected)
        self.assertEqual(len(state["jobs"]), 9)

    def test_executable_path_with_spaces_is_passed_as_one_argument(self):
        worker = self.temporary / "Julia executable with spaces"
        shutil.copy2(self.worker, worker)
        result, state = self.launch("launch_levers.sh", workers=2, worker=worker)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(state["jobs"]), 8)
        for job in state["jobs"]:
            self.assertEqual(job[:3], ["--startup-file=no", "--project=experiments",
                                      "experiments/scripts/run_levers.jl"])
        self.assertLessEqual(state["maximum"], 2)
        logs = self.temporary / "saved results/levers_logs"
        self.assertEqual({p.name for p in logs.glob("*.log")}, {
            "enum_w1.log", "enum_w2.log", "bench_w1.log", "bench_w2.log",
            "bench_w3.log", "bench_w4.log", "bench_w5.log", "bench_w6.log"})

    def test_resume_propagates_nonzero_child_exit(self):
        result, state = self.launch("resume_levers_bench.sh", workers=2, fail="bench|2")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(len(state["jobs"]), 6)
        self.assertEqual(state["active"], 0)
        self.assertLessEqual(state["maximum"], 2)

    def test_invalid_worker_limits_fail_before_any_worker_starts(self):
        for workers in ("0", "-1", "1.5", "abc", ""):
            with self.subTest(workers=workers):
                result, state = self.launch("launch_uc.sh", workers=workers)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("XOPT_WORKERS", result.stderr)
                self.assertEqual(state["jobs"], [])


if __name__ == "__main__":
    unittest.main()
