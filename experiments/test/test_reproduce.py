"""Exercise the public replay CLI's safety preflight before any solver starts."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/reproduce.sh'
ROOT = SCRIPT.parents[2]

class ReproduceSafetyTests(unittest.TestCase):
    def invoke(self, *args, results=None):
        env = os.environ.copy()
        env.pop('XOPT_RESULTS_DIR', None)
        env.update(JULIA_BIN='/usr/bin/false', PYTHON_BIN=sys.executable)
        if results is not None:
            env['XOPT_RESULTS_DIR'] = str(results)
        return subprocess.run(['bash', str(SCRIPT), *args], env=env,
                              capture_output=True, text=True, timeout=10)

    def test_help_is_available_without_dependencies(self):
        result = self.invoke('--help')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--recompute', result.stdout)
        self.assertIn('--no-pdf', result.stdout)

    def test_unknown_option_is_rejected_before_execution(self):
        result = self.invoke('--unknown')
        self.assertEqual(result.returncode, 2)
        self.assertIn('Unknown option', result.stderr)

    def test_recompute_requires_explicit_destination(self):
        result = self.invoke('--recompute')
        self.assertEqual(result.returncode, 2)
        self.assertIn('XOPT_RESULTS_DIR', result.stderr)

    def test_historical_destinations_and_descendants_are_rejected(self):
        for path in (ROOT / 'experiments/results', ROOT / 'experiments/results/new_run'):
            with self.subTest(path=path):
                result = self.invoke('--recompute', results=path)
                self.assertEqual(result.returncode, 2)
                self.assertIn('historical', result.stderr)

    def test_nonempty_destination_is_rejected_without_touching_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / 'keep.jsonl'
            marker.write_text('original\n')
            result = self.invoke('--recompute', results=tmp)
            self.assertEqual(result.returncode, 2)
            self.assertIn('empty', result.stderr)
            self.assertEqual(marker.read_text(), 'original\n')

if __name__ == '__main__':
    unittest.main()
