"""The original correction evidence must remain immutable and independently resolvable."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))

class CorrectionHistoryTests(unittest.TestCase):
    def test_frozen_correction_evidence_and_sources_are_verified(self):
        from correction_history import verify_correction_history
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            old = b'original protocol\n'; digest = hashlib.sha256(old).hexdigest()
            record = (json.dumps({'source_sha256': {'experiments/docs/correction_protocol_20261024.md': digest}})+'\n').encode()
            record_digest = hashlib.sha256(record).hexdigest()
            base = root/'experiments/provenance/corrections_20261024'
            (base/'objects').mkdir(parents=True)
            (base/'objects'/digest).write_bytes(old)
            names = ('uc_correction.json', 'robustness_revalidated.jsonl', 'current_validation.json')
            records = {}
            for name in names:
                rel = 'experiments/results/corrections_20261024/' + name
                path = root/rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(record)
                records[rel] = record_digest
            (base/'manifest.json').write_text(json.dumps({'sources': {'experiments/docs/correction_protocol_20261024.md': digest}, 'records': records}))
            self.assertEqual(verify_correction_history(root)['records_verified'], 3)
            (base/'objects'/digest).write_bytes(b'bad')
            with self.assertRaises(ValueError):
                verify_correction_history(root)

    def test_correction_history_rejects_omitted_original_record(self):
        from correction_history import verify_correction_history
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); base = root/'experiments/provenance/corrections_20261024'
            base.mkdir(parents=True)
            (base/'manifest.json').write_text(json.dumps({'sources': {'a': '0'*64}, 'records': {'b': '0'*64}}))
            with self.assertRaisesRegex(ValueError, 'correction record set'):
                verify_correction_history(root)

    def test_current_corrections_are_separate_from_historical_outputs(self):
        from record_io import CORRECTIONS
        self.assertNotEqual(CORRECTIONS, 'experiments/results/corrections_20261024')

if __name__ == '__main__':
    unittest.main()
