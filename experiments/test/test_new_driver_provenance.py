"""New driver runs must reject modified producers or input bytes on resume."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
JULIA = shutil.which('julia')

@unittest.skipUnless(JULIA, 'Julia unavailable')
class DriverProvenance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for directory in ('experiments/scripts', 'experiments/src', 'experiments/docs', 'experiments/data/pglib_uc', 'data/processed', 'new_results'):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        for file in ('experiments/scripts/run_experiments.jl', 'experiments/scripts/run_uc.jl',
                     'experiments/src/XOPT.jl', 'experiments/src/uc.jl',
                     'experiments/docs/uc_protocol_20261017.md'):
            shutil.copyfile(ROOT / file, self.root / file)
        for file in (ROOT/'experiments/data/pglib_uc').glob('*.json'):
            shutil.copyfile(file, self.root/'experiments/data/pglib_uc'/file.name)
        shutil.copyfile(ROOT/'experiments/data/pglib_uc/SHA256SUMS', self.root/'experiments/data/pglib_uc/SHA256SUMS')
        for name in ('retail_weekly.csv','nhs_monthly.csv'):
            shutil.copyfile(ROOT/'data/processed'/name, self.root/'data/processed'/name)
    def tearDown(self):
        self.tmp.cleanup()
    def run_driver(self, script, *args):
        env = dict(os.environ, XOPT_RESULTS_DIR=str(self.root/'new_results'))
        return subprocess.run([JULIA, '--startup-file=no', f'--project={ROOT / "experiments"}', str(self.root/'experiments/scripts'/script), *args],
                              cwd=self.root, env=env, text=True, capture_output=True, timeout=90)
    def sha(self, path):
        return hashlib.sha256((self.root/path).read_bytes()).hexdigest()
    def prior_primary_record(self):
        sources={p:self.sha(p) for p in ('experiments/src/XOPT.jl','experiments/scripts/run_experiments.jl')}
        inputs={p:self.sha(p) for p in ('data/processed/retail_weekly.csv','data/processed/nhs_monthly.csv')}
        (self.root/'new_results/main.jsonl').write_text(json.dumps({'key':'fixture','source_sha256':sources,'input_sha256':inputs})+'\n')
    def test_primary_rejects_changed_input_on_resume(self):
        self.prior_primary_record()
        with (self.root/'data/processed/retail_weekly.csv').open('a') as f: f.write('\n')
        p=self.run_driver('run_experiments.jl','main')
        self.assertNotEqual(p.returncode,0)
        self.assertIn('Input changed',p.stderr)
    def test_primary_rejects_changed_driver_on_resume(self):
        self.prior_primary_record()
        with (self.root/'experiments/scripts/run_experiments.jl').open('a') as f: f.write('\n# changed producer\n')
        p=self.run_driver('run_experiments.jl','main')
        self.assertNotEqual(p.returncode,0)
        self.assertIn('Source changed',p.stderr)
    def test_uc_rejects_changed_input_against_published_checksum(self):
        with (self.root/'experiments/data/pglib_uc/rts_2020-07-06.json').open('ab') as f:f.write(b' ')
        p=self.run_driver('run_uc.jl','enum','1','1')
        self.assertNotEqual(p.returncode,0)
        self.assertIn('PGLib input checksum mismatch',p.stderr)

if __name__=='__main__':unittest.main()
