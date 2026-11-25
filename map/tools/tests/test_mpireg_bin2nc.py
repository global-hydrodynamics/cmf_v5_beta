"""Numbered MPI regions use one standard definition in the s11/s12 flow."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import netCDF4
import numpy as np

from map.tools.code import convert_map_binary_to_netcdf as converter
from map.tools.tests.test_bin2nc_workflow import make_workflow_tree
from map.tools.tests.test_map_variant_conversion import ROOT, REGISTRY


class MPIRegionConversionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.scripts, self.map = make_workflow_tree(self.root, use_converter_stub=False)
        shutil.copy2(REGISTRY, self.root/'variable_table/map_variables.csv')
        (self.map/'binary').mkdir()
        self.values = np.array([[1, 0], [-9999, 12345678]], dtype='<i4')

    def run_script(self, name, *arguments):
        return subprocess.run(['sh', str(self.scripts/name), *arguments], cwd=self.scripts,
                              input='', text=True, capture_output=True)

    def verify(self, output, values, map_dir=None):
        nx, ny, _, res, west, _, _, north = converter.read_params((map_dir or self.map)/'params.txt')
        standard = next(row for row in converter.registry_rows(REGISTRY) if row['binary_filename'] == 'mpireg.bin')
        with netCDF4.Dataset(output) as ds:
            ds.set_auto_maskandscale(False)
            self.assertEqual(set(ds.variables), {'lon', 'lat', 'mpireg'})
            var = ds['mpireg']
            self.assertEqual(var.dimensions, ('lat', 'lon'))
            self.assertEqual(var.dtype, np.dtype('int32'))
            np.testing.assert_array_equal(var[:], values)
            np.testing.assert_array_equal(ds['lon'][:], west+(np.arange(nx)+.5)*res)
            np.testing.assert_array_equal(ds['lat'][:], north-(np.arange(ny)+.5)*res)
            self.assertEqual(var.missing_value, int(standard['missing_value']))
            self.assertEqual(var._FillValue, int(standard['missing_value']))
            self.assertEqual(var.long_name, standard['long_name'])
            self.assertEqual(var.filters()['complevel'], 3)
            self.assertTrue(var.filters()['zlib'])
            self.assertTrue(var.filters()['shuffle'])

    def test_candidate_names_category_order_and_existing_files_only(self):
        accepted = ['mpireg.bin', 'mpireg-1.bin', 'mpireg-4.bin', 'mpireg-8.bin',
                    'mpireg-16.bin', 'mpireg-32.bin', 'mpireg-004.bin']
        rejected = ['mpireg-test.bin', 'mpireg-0.bin', 'mpireg-000.bin', 'mpireg--4.bin',
                    'mpireg-4x.bin', 'mpireg-4.0.bin', 'mpireg-+4.bin', 'rivwth-4.bin']
        for name in accepted+rejected+['elevtn.bin', 'bifcol_mpi.bin', 'prmwat.bin']:
            (self.map/'binary'/name).write_bytes(self.values.tobytes())
        (self.map/'binary/nested').mkdir()
        (self.map/'binary/nested/mpireg-64.bin').write_bytes(self.values.tobytes())
        # A directory with the right suffix is not an actual Binary file.
        (self.map/'binary/mpireg-128.bin').mkdir()
        result = self.run_script('s11-list_bin.sh')
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        text = (self.scripts/'bin2nc_list.txt').read_text()
        listed = [line for line in text.splitlines() if line and not line.startswith('#')]
        self.assertEqual(set(listed), set(accepted+['elevtn.bin', 'bifcol_mpi.bin', 'prmwat.bin']))
        self.assertEqual(len(listed), len(set(listed)))
        self.assertLess(text.index('elevtn.bin'), text.index('# [24] MPI'))
        for name in accepted:
            self.assertGreater(text.index(name), text.index('# [24] MPI'))
            self.assertLess(text.index(name), text.index('# [25]'))
        self.assertNotIn('mpireg-64.bin\n', text)
        for name in rejected:
            self.assertEqual(converter.standard_binary_filename(name), name)
            with self.assertRaises(ValueError):
                converter.select_variables(name, converter.registry_rows(REGISTRY), None)

    def test_s11_s12_real_converter_skip_force_and_explicit_reference(self):
        for n in (4, 8, 16, 32):
            (self.map/'binary'/f'mpireg-{n}.bin').write_bytes(self.values.tobytes())
        result = self.run_script('s11-list_bin.sh')
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        # Keep user editing/commenting semantics, then convert remaining files.
        listing = self.scripts/'bin2nc_list.txt'
        listing.write_text(listing.read_text().replace('\nmpireg-32.bin\n', '\n#mpireg-32.bin\n'))
        # Probe the converter boundary to establish that s12 passes an explicit
        # reference, rather than accidentally relying on --variables fallback.
        script = self.root/'map/tools/code/convert_map_binary_to_netcdf.py'
        source = script.read_text()
        script.write_text(source.replace('    args = parser.parse_args()',
            '    args = parser.parse_args()\n    assert args.reference_binary == "mpireg.bin"'))
        result = self.run_script('s12-bin2nc.sh')
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        for n in (4, 8, 16):
            output = self.map/f'mpireg-{n}.nc'
            self.verify(output, self.values)
            self.assertEqual((self.map/'binary'/f'mpireg-{n}.bin').read_bytes(), self.values.tobytes())
        self.assertFalse((self.map/'mpireg-32.nc').exists())
        result = self.run_script('s12-bin2nc.sh')
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertIn('Converted: 3; skipped: 0', result.stdout)
        for n in (4, 8, 16):
            self.verify(self.map/f'mpireg-{n}.nc', self.values)
        listing.write_text(listing.read_text().replace('\n#mpireg-32.bin\n', '\nmpireg-32.bin\n'))
        result = self.run_script('s12-bin2nc.sh', '--force')
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.verify(self.map/'mpireg-32.nc', self.values)

    def test_direct_variables_and_reference_roles_and_missing_definition(self):
        rows = converter.registry_rows(REGISTRY)
        standard = [r for r in rows if r['name'] == 'mpireg']
        self.assertEqual(len(standard), 1)
        self.assertEqual(standard[0]['binary_filename'], 'mpireg.bin')
        for filename, requested, reference in [('mpireg-32.bin', None, None),
                ('mpireg-32.bin', ['mpireg'], None), ('arbitrary.bin', ['mpireg'], None),
                ('arbitrary.bin', None, 'mpireg.bin')]:
            with self.subTest(filename=filename, requested=requested, reference=reference):
                selected = converter.select_variables(filename, rows, requested, reference)
                self.assertEqual(len(selected), 1)
                self.assertEqual(selected[0]['_individual_name'], 'mpireg')
        (self.map/'mpireg-32.bin').write_bytes(self.values.tobytes())
        for option, value in [('--reference-binary', 'mpireg.bin'), ('--variables', 'mpireg')]:
            output = self.map/f"{option.lstrip('-')}.nc"
            result = subprocess.run([sys.executable, str(Path(converter.__file__)),
                '--map-dir', str(self.map), '--input', str(self.map/'mpireg-32.bin'),
                '--output', str(output), option, value], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.verify(output, self.values)
        with self.assertRaises(ValueError):
            converter.select_variables('mpireg-32.bin', rows, None, 'mpireg-32.bin')
        with self.assertRaises(ValueError):
            converter.select_variables('mpireg-32.bin', [r for r in rows if r['name'] != 'mpireg'], None)

    def test_existing_mekong_files_and_new_conversion_match(self):
        sample = ROOT/'map/mekong_15min'
        binary_sample = sample/'binary'
        shutil.copy2(binary_sample/'params.txt', self.map/'params.txt')
        for n in (4, 8, 16):
            source = binary_sample/f'mpireg-{n}.bin'
            shutil.copy2(source, self.map/'binary'/source.name)
            values = np.fromfile(source, dtype='<i4').reshape(120, 80)
            with netCDF4.Dataset(sample/f'mpireg-{n}.nc') as ds:
                ds.set_auto_maskandscale(False)
                np.testing.assert_array_equal(ds['mpireg'][:], values)
        result = self.run_script('s11-list_bin.sh')
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        result = self.run_script('s12-bin2nc.sh')
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        for n in (4, 8, 16):
            self.verify(self.map/f'mpireg-{n}.nc',
                        np.fromfile(binary_sample/f'mpireg-{n}.bin', dtype='<i4').reshape(120, 80))


if __name__ == '__main__':
    unittest.main()
