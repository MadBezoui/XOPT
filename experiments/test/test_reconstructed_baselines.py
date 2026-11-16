"""Reject missing or altered separately reconstructed baseline witnesses."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments/scripts"))
from validate_single_lever_revalidation import validate


class ReconstructedBaselineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in (
            "experiments/results/main.jsonl", "experiments/results/scale.jsonl",
            "experiments/results/long.jsonl", "experiments/results/single_lever.jsonl",
            "experiments/results/corrections_20261028/single_lever_revalidated.jsonl",
            "experiments/src/XOPT.jl", "experiments/src/anytime.jl",
            "experiments/scripts/revalidate_single_lever_20261028.jl",
        ):
            dest = self.root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, dest)

    def tearDown(self):
        self.tmp.cleanup()

    def test_complete_reconstructions_are_bound_to_original_interventions(self):
        self.assertEqual(validate(self.root)["validated"], 94)

    def test_tampered_witness_is_rejected(self):
        path = self.root / "experiments/results/corrections_20261028/single_lever_revalidated.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[0]["witness"]["delta"][0] += 1.0
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        with self.assertRaisesRegex(ValueError, "witness intervention differs"):
            validate(self.root)

    def test_missing_revalidation_is_rejected(self):
        path = self.root / "experiments/results/corrections_20261028/single_lever_revalidated.jsonl"
        lines = path.read_text().splitlines(keepends=True)
        path.write_text("".join(lines[1:]))
        with self.assertRaisesRegex(ValueError, "missing baseline intervention revalidations"):
            validate(self.root)

    def test_changed_producing_source_is_rejected(self):
        path = self.root / "experiments/src/anytime.jl"
        path.write_bytes(path.read_bytes() + b"\n# changed after validation\n")
        with self.assertRaisesRegex(ValueError, "Source identity mismatch"):
            validate(self.root)


if __name__ == "__main__":
    unittest.main()
