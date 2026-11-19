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

    def test_global_sample_dry_run_without_outputs_or_network(self):
        result = self.run_wrapper('sample-global_2day.sh', '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Dry run. CDS request:', result.stdout)
        self.assertIn("'02'", result.stdout)
        self.assertIn('repo-ERA5land-glb_2day/original/ERA5-Land_runoff_200001.nc', result.stdout)
        self.assertIn('repo-ERA5land-glb_2day/runoff_200001.nc', result.stdout)
        self.assertFalse((self.inp / 'repo-ERA5land-glb_2day').exists())

    def test_japan_hourly_dry_run_has_ten_daily_requests(self):
        import ast
        result = self.run_wrapper('sample-japan_hourly.sh', '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        requests = [ast.literal_eval(line) for line in result.stdout.splitlines() if line.startswith("{'variable':")]
        self.assertEqual(len(requests), 10)
        for day, request in enumerate(requests, 1):
            self.assertEqual(request['year'], '2007')
            self.assertEqual(request['month'], '09')
            self.assertEqual(request['day'], [f'{day:02d}'])
            self.assertEqual(request['time'], [f'{hour:02d}:00' for hour in range(24)])
            self.assertEqual(request['area'], [50., 120., 20., 150.])
            self.assertIn(f'original/ERA5-Land_runoff_200709{day:02d}.nc', result.stdout)
            self.assertIn(f'/runoff_200709{day:02d}.nc', result.stdout)
        self.assertFalse((self.inp / 'repo-ERA5land-jpn_hourly').exists())

    def test_product_calls_both_stage_shells_and_stops_on_failure(self):
        calls = self.inp / 'calls.txt'
        for name in ('s01-download.sh', 's02-convert_CMF_nc.sh'):
            (self.tools / name).write_text(
                '#!/bin/bash\nprintf "%s\\n" "' + name + ' $*" >> "' + str(calls) + '"\n'
            )
        result = self.run_wrapper('sample-japan_hourly.sh', '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = calls.read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith('s01-download.sh '))
        self.assertTrue(lines[1].startswith('s02-convert_CMF_nc.sh '))
        for line in lines:
            self.assertIn('--dataset repo-ERA5land-jpn_hourly', line)
            self.assertIn('--start-date 2007-09-01 --end-date 2007-09-10', line)
            self.assertIn('--format netcdf', line)
            self.assertIn('--dry-run', line)
        calls.unlink()
        (self.tools / 's01-download.sh').write_text('#!/bin/bash\nexit 7\n')
        result = self.run_wrapper('sample-japan_hourly.sh', '--dry-run')
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

    def test_hourly_daily_output_and_monthly_yearly_regrouping(self):
        dataset = self.inp / 'repo-ERA5land-jpn_hourly'
        original = dataset / 'original'
        original.mkdir(parents=True)
        expected_times = pd.date_range('2007-09-01', periods=48, freq='h')
        values = np.arange(1, 25, dtype='f4')[:, None, None] * np.ones((1, 2, 2), dtype='f4') * .001
        values[:, 0, 1] = np.nan
        # Two tiny daily cumulative fields; no real CDS data are read.
        for day in (1, 2):
            ds = xr.Dataset({'ro': (('valid_time', 'latitude', 'longitude'), values, {'units': 'm'})},
                            coords={'valid_time': expected_times[(day-1)*24:day*24],
                                    'latitude': [20., 20.1], 'longitude': [120., 120.1]})
            ds.to_netcdf(original / f'ERA5-Land_runoff_200709{day:02d}.nc')
        args = ('--dataset', dataset.name, '--start-date', '2007-09-01', '--end-date', '2007-09-02',
                '--tstep', '1', '--download-unit', 'daily', '--ncpus', '2')
        daily_values = []
        times = []
        result = self.run_wrapper('s02-convert_CMF_nc.sh', *args, '--output-unit', 'daily')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for day in (1, 2):
            path = dataset / f'runoff_200709{day:02d}.nc'
            self.assertIn(str(path), result.stdout)
            with xr.open_dataset(path) as ds:
                self.assertEqual(ds.runoff.shape, (24, 2, 2))
                self.assertEqual(ds.runoff.dims, ('time', 'lat', 'lon'))
                self.assertEqual(ds.runoff.dtype, np.dtype('f4'))
                self.assertEqual(ds.runoff.attrs['units'], 'mm')
                self.assertEqual(ds.runoff.encoding['complevel'], 3)
                self.assertTrue(ds.runoff.encoding['shuffle'])
                daily_values.append(ds.runoff.values)
                times.extend(ds.time.values)
        np.testing.assert_array_equal(np.array(times), expected_times.values)
        expected = np.ones((48, 2, 2), dtype='f4')
        expected[:, 1, 1] = np.nan  # Latitude is reversed to N-to-S.
        np.testing.assert_allclose(np.concatenate(daily_values), expected, atol=3e-6, equal_nan=True)
        report = dataset / 'runoff_info_CaMaFlood.txt'
        self.assertIn('CROFFREQ="DAY"', report.read_text())
        self.assertIn('runoff_YYYYMMDD.nc', report.read_text())
        self.assertIn('DROFUNIT="3600000"', report.read_text())
        for unit, name in [('monthly', 'runoff_200709.nc'), ('yearly', 'runoff_2007.nc')]:
            result = self.run_wrapper('s02-convert_CMF_nc.sh', *args, '--output-unit', unit, '--overwrite')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with xr.open_dataset(dataset / name) as ds:
                np.testing.assert_array_equal(ds.time.values, expected_times.values)
                np.testing.assert_array_equal(ds.runoff.values, np.concatenate(daily_values))
        # Missing or duplicate hours must fail rather than silently truncate/pad a daily file.
        source = original / 'ERA5-Land_runoff_20070901.nc'
        with xr.open_dataset(source) as ds:
            raw = ds.load()
        for bad_times in [list(expected_times[:23]), list(expected_times[:23]) + [expected_times[22]]]:
            malformed = raw.isel(valid_time=slice(0, len(bad_times))).assign_coords(valid_time=bad_times)
            malformed.to_netcdf(source)
            result = self.run_wrapper('s02-convert_CMF_nc.sh', *args, '--output-unit', 'daily', '--overwrite')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Incomplete or duplicate daily time records', result.stdout)



if __name__ == '__main__':
    unittest.main()
