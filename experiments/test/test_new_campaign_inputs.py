"""New runs must bind comparisons to the new input records, not frozen runs."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]

class NewCampaignInputs(unittest.TestCase):
    def test_single_lever_uses_new_inputs_and_binds_them(self):
        original = next(json.loads(x) for x in (ROOT/'experiments/results/main.jsonl').read_text().splitlines()
                        if json.loads(x)['job']['method'] == 'ccg')
        original['status'] = 'NEW_CAMPAIGN_MARKER'
        original['result']['objective'] = 12345.6789
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for profile in ('main', 'scale', 'long'):
                (root / (profile+'.jsonl')).write_text(json.dumps(original)+'\n')
            env = dict(os.environ, XOPT_RESULTS_DIR=tmp, XOPT_RECOMPUTE='1')
            proc = subprocess.run(['julia','--startup-file=no','--project=experiments',
                                   'experiments/scripts/run_single_lever.jl'], cwd=ROOT,
                                  env=env,capture_output=True,text=True,timeout=120)
            self.assertEqual(proc.returncode,0,proc.stdout+'\n'+proc.stderr)
            rows = [json.loads(x) for x in (root/'single_lever.jsonl').read_text().splitlines()]
            self.assertEqual(len(rows),3)
            self.assertTrue(any(row['status'] == 'RESTRICTED_VALIDATED' for row in rows),
                            'fixture must exercise the saved validated witness')
            for row in rows:
                self.assertEqual(row['global_status'],'NEW_CAMPAIGN_MARKER')
                self.assertEqual(row['global_objective'],12345.6789)
                source = root / (row['profile']+'.jsonl')
                self.assertEqual(row['input_file_sha256'],hashlib.sha256(source.read_bytes()).hexdigest())
                self.assertEqual(row['input_origin'],'new_campaign')
                for name in ('experiments/src/XOPT.jl', 'experiments/scripts/run_single_lever.jl'):
                    self.assertEqual(row['source_sha256'][name], hashlib.sha256((ROOT/name).read_bytes()).hexdigest())
                if row['status']=='RESTRICTED_VALIDATED':
                    self.assertTrue(row['verification']['valid'])
                    self.assertEqual(row['witness']['status'],'FEASIBLE_VALIDATED')
                    self.assertIn('delta',row['witness'])
                    self.assertIn('y',row['witness'])

if __name__ == '__main__': unittest.main()
