"""Behavioral regressions for the final artifact gate and frozen provenance."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))


class ArtifactGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = None
        spec = importlib.util.spec_from_file_location("artifact_gate", SCRIPTS / "validate_artifact.py")
        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            cls.gate = module
        except (AssertionError, SystemExit):
            pass  # The old script executes its incomplete global validation on import.

    def require_gate(self):
        self.assertIsNotNone(self.gate, "artifact validation must expose side-effect-free checks")
        self.assertTrue(hasattr(self.gate, "validate_enum_cases"), "missing complete study validation")
        return self.gate

    @staticmethod
    def case(key="case1"):
        return {"key": key, "enumeration": {"status": "OPTIMAL", "objective": .2},
                "dual": {"status": "SOLVER_VALIDATED", "objective": .2, "lower_bound": .2},
                "trajectory": {"status": "SOLVER_VALIDATED", "objective": .2, "lower_bound": .2},
                "dual_verification": {"valid": True}, "trajectory_verification": {"valid": True}}

    def test_external_profiles_have_distinct_validation_identities(self):
        gate = self.require_gate()
        a = {"key": "shared-case", "profile": "main"}
        b = {"key": "shared-case", "profile": "multifoil"}
        self.assertNotEqual(gate.validation_id("external_reference.jsonl", a, "xopt"),
                            gate.validation_id("external_reference.jsonl", b, "xopt"))

    def test_current_report_rejects_contradictory_verification_flags(self):
        from provenance import sha256
        from record_io import CORRECTIONS
        gate = self.require_gate()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            sources = {}
            for name in ("experiments/src/XOPT.jl", "experiments/src/levers.jl", "experiments/src/uc.jl",
                         "experiments/scripts/validate_updates.jl", "experiments/docs/correction_protocol_20261024.md"):
                path = root/name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("code\n"); sources[name] = sha256(path)
            files = {"main.jsonl": [{"key": "case1", "status": "SOLVER_VALIDATED"}]}
            path = root/"experiments/results/main.jsonl"; path.parent.mkdir(parents=True)
            path.write_text(json.dumps(files["main.jsonl"][0])+"\n")
            inputs = {"experiments/results/main.jsonl": sha256(path)}
            for name in ("uc_correction.json", "robustness_revalidated.jsonl"):
                path = root/CORRECTIONS/name; path.parent.mkdir(exist_ok=True)
                path.write_text("{}\n"); inputs[CORRECTIONS+"/"+name] = sha256(path)
            report = {"source_sha256": sources, "input_sha256": inputs, "all_passed": True,
                      "checks": [{"id": "main.jsonl|case1|result", "valid": True, "expected_valid": True,
                                  "passed": True, "verification": {"valid": False}, "binary": True,
                                  "objective_residual": 0.}]}
            (root/CORRECTIONS/"current_validation.json").write_text(json.dumps(report))
            with self.assertRaises(ValueError):
                gate.validate_current_report(root, files)

    def test_final_enum_gate_rejects_missing_case(self):
        gate = self.require_gate()
        with self.assertRaises(ValueError):
            gate.validate_enum_cases([self.case()], "UC", expected=2)

    def test_final_enum_gate_rejects_failed_witness_validation(self):
        gate = self.require_gate()
        bad = self.case(); bad["dual_verification"]["valid"] = False
        with self.assertRaises(ValueError):
            gate.validate_enum_cases([bad], "UC", expected=1)

    def test_final_enum_gate_rejects_false_optimality(self):
        gate = self.require_gate()
        bad = self.case(); bad["dual"]["objective"] = .25
        with self.assertRaises(ValueError):
            gate.validate_enum_cases([bad], "UC", expected=1)

    def test_final_enum_gate_accepts_complete_agreeing_cases(self):
        gate = self.require_gate()
        self.assertEqual(gate.validate_enum_cases([self.case()], "UC", expected=1)["cases"], 1)

    def test_final_gate_rejects_upper_bound_below_lower_bound(self):
        gate = self.require_gate()
        r = {"status": "SOLVER_VALIDATED", "objective": .2, "lower_bound": .3}
        with self.assertRaises(ValueError):
            gate.validate_success(r, {"valid": True}, "contradiction")


class CorrectionBindingTests(unittest.TestCase):
    def radius_fixture(self, td):
        from record_io import CORRECTIONS
        from provenance import sha256
        root = Path(td).resolve()
        names = ("experiments/src/XOPT.jl", "experiments/src/uc.jl", "experiments/src/robustness.jl",
                 "experiments/scripts/run_corrections.jl", "experiments/scripts/run_robustness.jl",
                 "experiments/docs/correction_protocol_20261024.md")
        hashes = {}
        for name in names:
            path = root/name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("producing code\n"); hashes[name] = sha256(path)
        path = root/"experiments/results/main.jsonl"; path.parent.mkdir(parents=True)
        line = json.dumps({"key": "case1", "job": {"method": "ccg"}, "status": "SOLVER_VALIDATED"})
        path.write_text(line+"\n")
        out = root/CORRECTIONS/"robustness_revalidated.jsonl"; out.parent.mkdir()
        row = {"key": "case1", "source_sha256": hashes, "input_file": "experiments/results/main.jsonl",
               "input_sha256": sha256(path), "input_record_sha256": hashlib.sha256(line.encode()).hexdigest(),
               "options": {"rho_max": .25, "atol": 1e-5, "time_limit": 60.}}
        return root, out, row

    def test_current_radius_accepts_complete_correct_binding(self):
        from record_io import current_radii
        with tempfile.TemporaryDirectory() as td:
            root, out, row = self.radius_fixture(td)
            out.write_text(json.dumps(row)+"\n")
            self.assertEqual(current_radii(root)[0]["key"], "case1")

    def test_current_radius_rejects_missing_algorithm_binding(self):
        from record_io import current_radii
        with tempfile.TemporaryDirectory() as td:
            root, out, row = self.radius_fixture(td)
            del row["source_sha256"]["experiments/src/robustness.jl"]
            out.write_text(json.dumps(row)+"\n")
            with self.assertRaises(ValueError):
                current_radii(root)

    def test_current_radius_rejects_wrong_individual_input_identity(self):
        from record_io import current_radii
        with tempfile.TemporaryDirectory() as td:
            root, out, row = self.radius_fixture(td)
            row["input_record_sha256"] = "0"*64
            out.write_text(json.dumps(row)+"\n")
            with self.assertRaises(ValueError):
                current_radii(root)


class ProvenanceTests(unittest.TestCase):
    def module(self):
        self.assertTrue((SCRIPTS / "provenance.py").exists(), "frozen source resolver is missing")
        import provenance
        return provenance

    def fixture(self, directory):
        root = Path(directory); source = root / "experiments/src/core.jl"; source.parent.mkdir(parents=True)
        old = b"old scientific code\n"; digest = hashlib.sha256(old).hexdigest()
        source.write_bytes(b"corrected scientific code\n")
        store = root / "experiments/provenance/objects"; store.mkdir(parents=True)
        (store / digest).write_bytes(old)
        (store.parent / "frozen_manifest.json").write_text(json.dumps({"sources": {"experiments/src/core.jl": digest}, "historical_records": {}}))
        return root, digest

    def test_frozen_source_is_explicitly_historical(self):
        p = self.module()
        with tempfile.TemporaryDirectory() as td:
            root, digest = self.fixture(td)
            self.assertEqual(p.verify_source(root, "experiments/src/core.jl", digest), "historical")

    def test_corrupted_frozen_source_is_rejected(self):
        p = self.module()
        with tempfile.TemporaryDirectory() as td:
            root, digest = self.fixture(td)
            (root / "experiments/provenance/objects" / digest).write_text("corrupted")
            with self.assertRaises(ValueError):
                p.verify_source(root, "experiments/src/core.jl", digest)

    def test_frozen_manifest_cannot_authorize_path_traversal(self):
        p = self.module()
        with tempfile.TemporaryDirectory() as td:
            root, digest = self.fixture(td)
            with self.assertRaises(ValueError):
                p.verify_source(root, "../../private.tex", digest)


if __name__ == "__main__":
    unittest.main()
