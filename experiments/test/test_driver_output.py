"""Run destructive-output preflights against isolated historical sentinels."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
JULIA = shutil.which('julia')
DRIVERS = {'run_single_lever.jl': 'single_lever.jsonl',
           'run_external_reference.jl': 'external_reference.jsonl'}


@unittest.skipUnless(JULIA, 'Julia is needed to exercise the real driver preflights')
class DriverOutputTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='xopt-driver-test-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.history = self.root / 'experiments/results'
        self.history.mkdir(parents=True)
        scripts = self.root / 'experiments/scripts'
        scripts.mkdir()
        for driver, name in DRIVERS.items():
            shutil.copyfile(ROOT / 'experiments/scripts' / driver, scripts / driver)
            (self.history / name).write_bytes(b'IMMUTABLE HISTORICAL SENTINEL\n')
        source = self.root / 'experiments/src'
        source.mkdir()
        # A forbidden path must fail before loading the numerical model. This
        # import barrier prevents tests from running any solver or touching data.
        (source / 'XOPT.jl').write_text('error("MODEL_IMPORT_REACHED")\n')

    def invoke(self, driver, destination, *, recompute=True):
        env = os.environ.copy()
        env.update(XOPT_RECOMPUTE='1', XOPT_RESULTS_DIR=str(destination))
        if not recompute:
            env.pop('XOPT_RECOMPUTE', None)
        return subprocess.run(
            [JULIA, '--startup-file=no', '--history-file=no',
             '--project=' + str(ROOT / 'experiments'),
             str(self.root / 'experiments/scripts' / driver)],
            cwd=self.root, env=env, capture_output=True, text=True, timeout=30)

    def assert_historical_rejected(self, destination):
        for driver, name in DRIVERS.items():
            with self.subTest(driver=driver, destination=destination):
                result = self.invoke(driver, destination)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('historical', result.stderr)
                self.assertNotIn('MODEL_IMPORT_REACHED', result.stderr)
                self.assertEqual((self.history / name).read_bytes(),
                                 b'IMMUTABLE HISTORICAL SENTINEL\n')

    def test_relative_historical_directory_is_rejected_before_model_import(self):
        self.assert_historical_rejected('experiments/results')

    def test_absolute_and_dotdot_historical_aliases_are_rejected(self):
        self.assert_historical_rejected(self.history)
        self.assert_historical_rejected('experiments/results/../results')

    def test_symlinked_historical_directory_and_new_descendant_are_rejected(self):
        (self.root / 'alias').symlink_to(self.history, target_is_directory=True)
        self.assert_historical_rejected(self.root / 'alias')
        self.assert_historical_rejected(self.root / 'alias/not-created')
        self.assertFalse((self.history / 'not-created').exists())

    def test_dangling_symlink_towards_new_historical_descendant_is_rejected(self):
        (self.root / 'dangling').symlink_to('experiments/results/not-created')
        self.assert_historical_rejected(self.root / 'dangling')
        self.assertFalse((self.history / 'not-created').exists())

    def test_empty_destination_is_rejected_before_model_import(self):
        self.assert_historical_rejected('')

    def test_default_reuse_preserves_archives_without_loading_model(self):
        for driver, name in DRIVERS.items():
            with self.subTest(driver=driver):
                result = self.invoke(driver, self.history, recompute=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('Existing records kept', result.stdout)
                self.assertEqual((self.history / name).read_bytes(),
                                 b'IMMUTABLE HISTORICAL SENTINEL\n')

    def test_output_file_symlink_cannot_overwrite_historical_attempt(self):
        destination = self.root / 'separate'
        destination.mkdir()
        for name in DRIVERS.values():
            (destination / name).symlink_to(self.history / name)
        self.assert_historical_rejected(destination)

    def test_separate_nonexistent_directory_passes_the_output_preflight(self):
        for driver in DRIVERS:
            with self.subTest(driver=driver):
                result = self.invoke(driver, self.root / 'new/isolated')
                self.assertNotIn('outside historical', result.stderr)
                self.assertIn('MODEL_IMPORT_REACHED', result.stderr)
        for name in DRIVERS.values():
            self.assertEqual((self.history / name).read_bytes(),
                             b'IMMUTABLE HISTORICAL SENTINEL\n')


if __name__ == '__main__':
    unittest.main()
