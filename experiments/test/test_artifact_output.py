"""Exercise the real artifact CLI's output writes against isolated input files."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/validate_artifact.py"

# Scientific verification is covered by separate regressions. Give the actual CLI
# a successful verification precondition so these small fixtures reach its writer.
# Argument parsing, destination checks and filesystem writes are the real code.
BOOTSTRAP = """
import importlib.util
from pathlib import Path
import sys
script = sys.argv.pop(1)
sys.path.insert(0, str(Path(script).parent))
spec = importlib.util.spec_from_file_location('artifact_output_cli', script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.validate = lambda root: {'passed': True, 'fixture': True}
module.main()
"""


class ArtifactOutputTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="xopt_output_")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        self.inputs = ["experiments/results/main.jsonl", "experiments/src/XOPT.jl",
                       "experiments/results/corrections_20261024/current_validation.json",
                       "experiments/provenance/frozen_manifest.json",
                       "experiments/provenance/objects/" + "a" * 64, "README.md",
                       "article/main.pdf"]
        for name in self.inputs:
            self.put(name, b"preserved input\n")
        self.manifest = "experiments/docs/publication_allowlist.json"
        self.put(self.manifest, json.dumps({
            "schema": 1,
            "files": self.inputs[:-1] + [self.manifest,
                                         "experiments/results/validation_report.json"],
            "optional_pdf": ["article/main.pdf"],
        }).encode())
        self.inputs.append(self.manifest)
        self.before = {name: self.digest(self.root / name) for name in self.inputs}

    def put(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    @staticmethod
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def invoke(self, output=None):
        command = [sys.executable, "-c", BOOTSTRAP, str(SCRIPT), "--root", str(self.root)]
        if output is not None:
            command += ["--output", str(output)]
        return subprocess.run(command, cwd=self.root, text=True,
                              capture_output=True, timeout=15)

    def assert_inputs_preserved(self):
        self.assertEqual({name: self.digest(self.root / name) for name in self.inputs},
                         self.before)

    def test_cli_rejects_every_allowlisted_input_and_preserves_its_bytes(self):
        for name in self.inputs:
            with self.subTest(name=name):
                result = self.invoke(self.root / name)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("output", result.stderr.lower())
                self.assert_inputs_preserved()

    def test_relative_parent_alias_cannot_overwrite_historical_input(self):
        result = self.invoke("experiments/results/../results/main.jsonl")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assert_inputs_preserved()

    def test_symlink_output_cannot_overwrite_input(self):
        alias = self.root / "report.json"
        alias.symlink_to(self.root / self.inputs[0])
        result = self.invoke(alias)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assert_inputs_preserved()

    def test_symlink_parent_cannot_bypass_protection(self):
        alias = self.root / "linked_results"
        alias.symlink_to(self.root / "experiments/results", target_is_directory=True)
        result = self.invoke(alias / "main.jsonl")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assert_inputs_preserved()

    def test_hardlink_alias_cannot_overwrite_input(self):
        alias = self.root / "report.json"
        os.link(self.root / self.inputs[0], alias)
        result = self.invoke(alias)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assert_inputs_preserved()

    def test_default_report_is_not_exempt_when_hardlinked_to_an_input(self):
        report = self.root / "experiments/results/validation_report.json"
        os.link(self.root / self.inputs[0], report)
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assert_inputs_preserved()

    def test_normal_default_report_can_be_refreshed(self):
        report = self.put("experiments/results/validation_report.json", b"old report\n")
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(report.read_text()), {"passed": True, "fixture": True})
        self.assert_inputs_preserved()

    def test_custom_report_cannot_replace_unlisted_private_or_working_input(self):
        for name in ("article/main.tex", "article/references.bib", "experiments/local_input.json"):
            with self.subTest(name=name):
                path = self.put(name, b"private working input\n")
                result = self.invoke(path)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertEqual(path.read_bytes(), b"private working input\n")

    def test_new_custom_report_can_be_written_without_touching_inputs(self):
        report = self.root / "reports/final.json"
        result = self.invoke(report)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(report.read_text())["passed"])
        self.assert_inputs_preserved()


if __name__ == "__main__":
    unittest.main()
