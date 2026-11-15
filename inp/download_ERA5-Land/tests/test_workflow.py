"""Offline checks of dataset paths, CDS request plans and NetCDF wrapper handoff."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd
import xarray as xr

TOOLS = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.inp = Path(self.temp.name) / 'inp'
        self.tools = self.inp / 'download_ERA5-Land'
        self.tools.mkdir(parents=True)
        for p in TOOLS.iterdir():
            if p.suffix in ('.sh', '.py'):
                shutil.copy2(p, self.tools / p.name)
        self.env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}

    def run_wrapper(self, name, *args):
        stage_settings = []
        if name in ('s01-download.sh', 's02-convert_CMF_nc.sh'):
            stage_settings = ['--start-date', '2000-01-01', '--end-date', '2000-01-31',
                              '--west', '122', '--east', '154', '--south', '24', '--north', '46',
                              '--tstep', '24', '--download-unit', 'monthly', '--output-unit', 'monthly']
        return subprocess.run(
            ['/bin/bash', str(self.tools / name), *stage_settings, '--python', sys.executable, *args],
            cwd=self.temp.name, capture_output=True, text=True, env=self.env,
        )

    def test_samples_dry_run_without_outputs_or_network(self):
        for script, dataset, last in [
            ('sample-global_2day.sh', 'ERA5land-glb_2day', '02'),
            ('sample-japan_1month.sh', 'ERA5land-jpn_1month', '31'),
        ]:
            result = self.run_wrapper(script, '--dry-run')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Dry run. CDS request:', result.stdout)
            self.assertIn(f"'{last}'", result.stdout)
            self.assertIn(f'{dataset}/original/ERA5-Land_runoff_200001.nc', result.stdout)
            self.assertIn(f'{dataset}/runoff_200001.nc', result.stdout)
            self.assertFalse((self.inp / dataset).exists())

    def test_product_calls_both_stage_shells_and_stops_on_failure(self):
        calls = self.inp / 'calls.txt'
        for name in ('s01-download.sh', 's02-convert_CMF_nc.sh'):
            (self.tools / name).write_text(
                '#!/bin/bash\nprintf "%s\\n" "' + name + ' $*" >> "' + str(calls) + '"\n'
            )
        result = self.run_wrapper('sample-japan_1month.sh', '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = calls.read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith('s01-download.sh '))
        self.assertTrue(lines[1].startswith('s02-convert_CMF_nc.sh '))
        for line in lines:
            self.assertIn('--dataset ERA5land-jpn_1month', line)
            self.assertIn('--start-date 2000-01-01 --end-date 2000-01-31', line)
            self.assertIn('--format netcdf', line)
            self.assertIn('--dry-run', line)
        calls.unlink()
        (self.tools / 's01-download.sh').write_text('#!/bin/bash\nexit 7\n')
        result = self.run_wrapper('sample-japan_1month.sh', '--dry-run')
        self.assertEqual(result.returncode, 7)
        self.assertFalse(calls.exists())

    def test_destination_and_failed_jobs(self):
        for name in ('../escape', '/tmp/escape', 'download_ERA5-Land'):
            result = self.run_wrapper('s01-download.sh', '--dataset', name, '--dry-run')
            self.assertNotEqual(result.returncode, 0)
        result = self.run_wrapper('s02-convert_CMF_nc.sh', '--dataset', 'ERA5land-missing', '--ncpus', '2', '--end-date', '2000-02-01')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('convert 200001', result.stderr)
        self.assertIn('convert 200002', result.stderr)
        self.assertEqual(len(list((self.inp / 'ERA5land-missing/logs').glob('convert.*/*.log'))), 2)

    def test_tiny_conversion_skip_and_explicit_overwrite(self):
        dataset = self.inp / 'ERA5land-dummy'
        original = dataset / 'original'
        original.mkdir(parents=True)
        source = original / 'ERA5-Land_runoff_200001.nc'
        values = np.array([[[.1, .2], [.3, np.nan]], [[.2, .4], [.1, np.nan]]], dtype='f4')
        raw = xr.Dataset({'ro': (('valid_time', 'latitude', 'longitude'), values, {'units': 'm'})},
                         coords={'valid_time': pd.to_datetime(['2000-01-01T00', '2000-01-01T12']),
                                 'latitude': [24., 24.1], 'longitude': [122., 122.1]})
        raw.to_netcdf(source)
        source_bytes = source.read_bytes()
        args = ('--dataset', 'ERA5land-dummy', '--end-date', '2000-01-01', '--tstep', '12')
        result = self.run_wrapper('s02-convert_CMF_nc.sh', *args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        target = dataset / 'runoff_200001.nc'
        with xr.open_dataset(target) as ds:
            self.assertEqual(ds.runoff.dims, ('time', 'lat', 'lon'))
            self.assertEqual(ds.runoff.attrs['units'], 'mm')
            # Preserve first-step, within-day differencing and negative-reset behavior.
            expected = np.array([[[300., np.nan], [100., 200.]], [[100., np.nan], [100., 200.]]], dtype='f4')
            np.testing.assert_allclose(ds.runoff.values, expected, rtol=1e-6, equal_nan=True)
            self.assertEqual(ds.runoff.encoding['complevel'], 3)
            self.assertTrue(ds.runoff.encoding['shuffle'])
        report = dataset / 'runoff_info_CaMaFlood.txt'
        self.assertIn('DROFUNIT="43200000"', report.read_text())
        before = target.read_bytes(), report.read_bytes()
        result = self.run_wrapper('s02-convert_CMF_nc.sh', *args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Skip existing:', result.stdout)
        self.assertEqual((target.read_bytes(), report.read_bytes()), before)
        result = self.run_wrapper('s02-convert_CMF_nc.sh', *args, '--overwrite')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(source.read_bytes(), source_bytes)
        self.assertFalse(list(self.tools.glob('*.nc')))


if __name__ == '__main__':
    unittest.main()
