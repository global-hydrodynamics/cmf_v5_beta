"""Variant input names must not change registry layouts or stored values."""
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import netCDF4
import numpy as np

from map.tools.code import convert_map_binary_to_netcdf as converter
from map.tools.code import mod_map_io

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / 'variable_table/map_variables.csv'
SCRIPT = ROOT / 'map/tools/script_format_conv/s18-sample_bin2nc.sh'
NC2BIN_SCRIPT = ROOT / 'map/tools/script_format_conv/s08-sample_nc2bin.sh'
GENERIC_NC2BIN = ROOT / 'map/tools/script_format_conv/conv_nc2bin.sh'
GENERIC_BIN2NC = ROOT / 'map/tools/script_format_conv/conv_bin2nc.sh'


class VariantConversionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.map = self.root / 'map with spaces'
        self.map.mkdir()
        (self.map / 'params.txt').write_text('3\n2\n2\n1\n10\n13\n18\n20\n')

    def args(self, source='experiment.bin', reference='nextxy.bin', variables=None, force=False):
        return argparse.Namespace(map_dir=self.map, registry=REGISTRY, input=self.map/source,
                                  output=self.map/f'{Path(source).stem}.nc',
                                  reference_binary=reference, variables=variables, force=force,
                                  no_overwrite=False, byte_order='little')

    def check_data(self, output, arrays):
        with netCDF4.Dataset(output) as ds:
            ds.set_auto_maskandscale(False)
            self.assertEqual(set(ds.variables), {'lon', 'lat'} | set(arrays))
            np.testing.assert_array_equal(ds['lon'][:], [10.5, 11.5, 12.5])
            np.testing.assert_array_equal(ds['lat'][:], [19.5, 18.5])
            for name, values in arrays.items():
                var = ds[name]
                np.testing.assert_array_equal(var[:], values)
                self.assertEqual(var.dimensions, ('layer', 'lat', 'lon') if values.ndim == 3 else ('lat', 'lon'))
                self.assertEqual(var.dtype, values.dtype)
                self.assertEqual(var.missing_value, -9999)
                self.assertEqual(var._FillValue, -9999)
                self.assertTrue(var.filters()['zlib'])
                self.assertTrue(var.filters()['shuffle'])
                self.assertEqual(var.filters()['complevel'], 3)

    def test_renamed_multirecord_and_partial_selection_preserve_record_offsets(self):
        x = np.array([[2, -9, -10], [0, -9999, 3]], dtype='<i4')
        y = np.array([[1, -9, -10], [0, -9999, 2]], dtype='<i4')
        args = self.args()
        args.input.write_bytes(x.tobytes() + y.tobytes())
        before = args.input.read_bytes()
        converter.convert(args)
        self.check_data(args.output, {'nextx': x, 'nexty': y})
        args.variables, args.force = ['nexty'], True
        converter.convert(args)
        self.check_data(args.output, {'nexty': y})
        self.assertEqual(args.input.read_bytes(), before)
        # The original --variables fallback also supports an unknown input stem.
        args.reference_binary, args.variables = None, ['nextx']
        converter.convert(args)
        self.check_data(args.output, {'nextx': x})

    def test_standard_single_paired_layered_and_legacy_variable_fallback(self):
        for filename, reference, dtype, shape, names in [
            ('elevtn.bin', None, '<f4', (2, 3), ['elevtn']),
            ('nextxy.bin', None, '<i4', (2, 2, 3), ['nextx', 'nexty']),
            ('nextxy_noedge.bin', None, '<i4', (2, 2, 3), ['nextx_noedge', 'nexty_noedge']),
            ('fldhgt.bin', None, '<f4', (2, 2, 3), ['fldhgt']),
            ('profile-experiment.bin', 'fldhgt.bin', '<f4', (2, 2, 3), ['fldhgt']),
            ('legacy.bin', None, '<i4', (2, 3), ['subcol']),
        ]:
            with self.subTest(filename=filename):
                args = self.args(filename, reference, ['subcol'] if filename == 'legacy.bin' else None)
                values = np.arange(np.prod(shape), dtype=dtype).reshape(shape)
                args.input.write_bytes(values.tobytes())
                converter.convert(args)
                expected = {name: values[i] for i, name in enumerate(names)} if len(names) == 2 else {names[0]: values}
                self.check_data(args.output, expected)
        # A one-layer profile must retain its rank and its sole layer.
        (self.map/'params.txt').write_text('3\n2\n1\n1\n10\n13\n18\n20\n')
        args = self.args('one-layer.bin', 'fldhgt.bin')
        values = np.arange(6, dtype='<f4').reshape(1, 2, 3)
        args.input.write_bytes(values.tobytes())
        converter.convert(args)
        self.check_data(args.output, {'fldhgt': values})

    def test_sample_variants_keep_categories_and_registry_metadata(self):
        values = np.array([[-9999, 0, 1], [2, 10, 3]], dtype='<i4')
        for name in ('subbsn', 'subcol'):
            args = self.args(f'{name}-sample.bin', f'{name}.bin')
            args.input.write_bytes(values.tobytes())
            converter.convert(args)
            self.check_data(args.output, {name: values})
            row = next(r for r in converter.registry_rows(REGISTRY) if r['filename'] == f'{name}.nc')
            with netCDF4.Dataset(args.output) as ds:
                self.assertEqual(ds[name].long_name, row['long_name'])
                self.assertEqual(ds[name].units, row['units'])

    def test_reference_is_exact_and_cannot_fall_back_to_variables(self):
        rows = converter.registry_rows(REGISTRY)
        for reference in ('nextxy', 'next', '/tmp/nextxy.bin', 'missing.bin', 'nextxy.bin '):
            with self.subTest(reference=reference), self.assertRaisesRegex(ValueError, 'exact base filename'):
                converter.select_variables('custom.bin', rows, ['nextx'], reference)
        with self.assertRaisesRegex(ValueError, 'variables not registered'):
            converter.select_variables('custom.bin', rows, ['subcol'], 'nextxy.bin')

    def test_generic_input_matrix_names_keep_binary_record_contract(self):
        rows = converter.registry_rows(REGISTRY)
        matrix = [row for row in rows if row['filename'] == 'inpmat_<ROFFTAG>.nc']
        self.assertEqual([row['name'] for row in matrix], ['inpx', 'inpy', 'inpa'])
        self.assertEqual([row['record_index'] for row in matrix], ['1', '2', '3'])
        self.assertEqual([row['dtype'] for row in matrix], ['int32', 'int32', 'float32'])
        self.assertTrue(all(converter.registered_binary_match('inpmat_test-runoff.bin', row)
                            for row in matrix))
        mapped = converter.registered_binary_rows('inpmat_test-1deg.bin', rows)
        self.assertEqual({row['category_id'] for row in mapped}, {'23'})
        self.assertEqual([row['name'] for row in mapped], ['inpx', 'inpy', 'inpa'])
        generic = converter.registered_binary_rows('inpmat_custom-runoff.bin', rows)
        self.assertEqual({row['category_id'] for row in generic}, {'23'})

    def test_invalid_record_definitions_are_rejected_before_partial_selection(self):
        rows = [dict(r) for r in converter.registry_rows(REGISTRY) if r['filename'] == 'nextxy.nc']
        cases = [rows[:1], [rows[0], rows[0]], [rows[0], dict(rows[1], record_count='3')],
                 [rows[0], dict(rows[1], record_index='0')],
                 [rows[0], dict(rows[1], dimensions='NX,NY,INPN')],
                 [rows[0], dict(rows[1], dtype='int16')]]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                converter.select_variables('anything.bin', case, ['nextx'], 'nextxy.bin')
        other = [dict(r, filename='pair.bin', name='same') for r in rows]
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            converter.select_variables('anything.bin', other, None, 'pair.bin')

    def test_mixed_record_dtypes_and_registry_order(self):
        rows = [dict(r) for r in converter.registry_rows(REGISTRY) if r['filename'] == 'nextxy.nc']
        rows[0].update(filename='mixed.bin', name='code')
        rows[1].update(filename='mixed.bin', name='height', dtype='float32')
        registry = self.root/'mixed.csv'
        with registry.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows[::-1])
        args = self.args(reference='mixed.bin')
        args.registry = registry
        codes = np.arange(6, dtype='<i4').reshape(2, 3)
        heights = np.arange(6, dtype='<f4').reshape(2, 3) + .5
        args.input.write_bytes(codes.tobytes()+heights.tobytes())
        converter.convert(args)
        self.check_data(args.output, {'code': codes, 'height': heights})

    def test_missing_size_overwrite_and_midwrite_failure_protect_outputs(self):
        args = self.args()
        with self.assertRaises(FileNotFoundError):
            converter.convert(args)
        args.input.write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError, 'require 48'):
            converter.convert(args)
        self.assertFalse(args.output.exists())
        args.input.write_bytes(np.arange(12, dtype='<i4').tobytes())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(b'prior-output')
        args.no_overwrite = True
        with self.assertRaises(FileExistsError):
            converter.convert(args)
        args.no_overwrite = False
        converter.convert(args)
        self.assertNotEqual(args.output.read_bytes(), b'prior-output')
        args.output.write_bytes(b'prior-output')
        original = converter.put_text
        def fail_after_create(*a):
            if a[3] == 'long_name':
                raise RuntimeError('injected metadata write failure')
            original(*a)
        for existing in (True, False):
            if not existing:
                args.output.unlink()
            with mock.patch.object(converter, 'put_text', side_effect=fail_after_create):
                with self.assertRaisesRegex(RuntimeError, 'injected'):
                    converter.convert(args)
            if existing:
                self.assertEqual(args.output.read_bytes(), b'prior-output')
            else:
                self.assertFalse(args.output.exists())
            self.assertEqual(list(args.output.parent.glob('.*.tmp')), [])

    def test_generate_list_excludes_variants_and_rejects_reference_option(self):
        for name in ('subcol.bin', 'subcol-sample.bin'):
            (self.map/name).write_bytes(b'\0'*24)
        target = self.root/'list.txt'
        converter.generate_conversion_list(self.map, REGISTRY, target)
        self.assertIn('\nsubcol.bin\n', target.read_text())
        self.assertNotIn('\nsubcol-sample.bin\n', target.read_text())
        result = subprocess.run([sys.executable, str(Path(converter.__file__)), '--map-dir', str(self.map),
                                 '--generate-list', '--reference-binary', 'subcol.bin'], capture_output=True)
        self.assertEqual(result.returncode, 2)

    def test_generic_converters_keep_custom_filename_and_registered_multivariable_layout(self):
        script_dir = self.map/'script_format_conv'
        script_dir.mkdir()
        for source in (GENERIC_NC2BIN, GENERIC_BIN2NC):
            shutil.copy2(source, script_dir/source.name)
        binary_dir = self.map/'binary'
        binary_dir.mkdir()
        values = {
            'nextx': np.array([[2, -9, -10], [0, -9999, 3]], dtype='int32'),
            'nexty': np.array([[1, -9, -10], [0, -9999, 2]], dtype='int32'),
        }
        source = self.map/'nextxy-test.nc'
        with netCDF4.Dataset(source, 'w') as dataset:
            dataset.createDimension('lat', 2)
            dataset.createDimension('lon', 3)
            for name, data in values.items():
                dataset.createVariable(name, 'i4', ('lat', 'lon'))[:] = data

        env = dict(os.environ, CMF_V50_ROOT=str(ROOT))
        nc2bin = subprocess.run(['/bin/sh', str(script_dir/'conv_nc2bin.sh'), source.name, 'nextxy'],
                                cwd=script_dir, env=env, capture_output=True, text=True)
        self.assertEqual(nc2bin.returncode, 0, nc2bin.stdout+nc2bin.stderr)
        self.assertIn('Reference: nextxy', nc2bin.stdout)
        binary = binary_dir/'nextxy-test.bin'
        self.assertEqual(binary.read_bytes(), b''.join(data.astype('<i4').tobytes() for data in values.values()))

        bin2nc = subprocess.run(['/bin/sh', str(script_dir/'conv_bin2nc.sh'), binary.name, 'nextxy'],
                                cwd=script_dir, env=env, capture_output=True, text=True)
        self.assertEqual(bin2nc.returncode, 0, bin2nc.stdout+bin2nc.stderr)
        self.assertIn('Output:    ../nextxy-test.nc', bin2nc.stdout)
        self.check_data(source, values)

        bad = subprocess.run(['/bin/sh', str(script_dir/'conv_nc2bin.sh'), source.name],
                             cwd=script_dir, env=env, capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)
        self.assertIn('Usage:', bad.stderr)

    def test_sample_producer_uses_registered_internal_variable_names(self):
        previous_format, previous_root, previous_registry = (
            mod_map_io._MAP_FORMAT, mod_map_io._MAP_ROOT, mod_map_io._REGISTRY,
        )
        grid = mod_map_io.Grid.read(self.map/'params.txt')
        mod_map_io._MAP_FORMAT = 'netcdf'
        mod_map_io._REGISTRY = None
        try:
            for name in ('subbsn', 'subcol'):
                values = np.array([[-9999, 0, 1], [2, 10, 3]], dtype='int32')
                mod_map_io.write_raster(self.map/f'{name}-sample.bin', values, '<i4', grid=grid)
                with netCDF4.Dataset(self.map/f'{name}-sample.nc') as dataset:
                    self.assertIn(name, dataset.variables)
                    self.assertNotIn(f'{name}-sample', dataset.variables)
        finally:
            mod_map_io._MAP_FORMAT = previous_format
            mod_map_io._MAP_ROOT = previous_root
            mod_map_io._REGISTRY = previous_registry

    def test_s08_and_s18_run_the_generic_sample_conversions(self):
        binary_dir = self.map/'binary'
        binary_dir.mkdir()
        arrays = {
            'subbsn': np.array([[-9999, 0, 1], [2, 10, 3]], dtype='int32'),
            'subcol': np.array([[-9999, 0, 5], [4, 10, 2]], dtype='int32'),
        }
        original_sources = {}
        for name, values in arrays.items():
            source = self.map/f'{name}-sample.nc'
            with netCDF4.Dataset(source, 'w') as dataset:
                dataset.createDimension('lat', 2)
                dataset.createDimension('lon', 3)
                variable = dataset.createVariable(name, 'i4', ('lat', 'lon'))
                variable[:] = values
            original_sources[source.name] = source.read_bytes()
            (binary_dir/f'{name}-sample.bin').write_bytes(b'preserve-'+name.encode())

        script_dir = self.map/'script_format_conv'
        script_dir.mkdir()
        script = script_dir/NC2BIN_SCRIPT.name
        shutil.copy2(NC2BIN_SCRIPT, script)
        shutil.copy2(SCRIPT, script_dir/SCRIPT.name)
        shutil.copy2(GENERIC_NC2BIN, script_dir/GENERIC_NC2BIN.name)
        shutil.copy2(GENERIC_BIN2NC, script_dir/GENERIC_BIN2NC.name)
        def run(*arguments):
            return subprocess.run(['bash', str(script), *arguments], cwd=script_dir,
                                  env=dict(os.environ, CMF_V50_ROOT=str(ROOT),
                                           PATH=f"{ROOT/'.venv/bin'}:{os.environ['PATH']}"),
                                  capture_output=True, text=True)

        result = run()
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertIn('Usage: ./conv_nc2bin.sh INPUT.nc REFERENCE', result.stdout)
        self.assertEqual(result.stdout.count('NetCDF -> Binary'), 2)
        for name, values in arrays.items():
            self.assertEqual((binary_dir/f'{name}-sample.bin').read_bytes(), values.astype('<i4').tobytes())
            self.assertEqual((self.map/f'{name}-sample.nc').read_bytes(), original_sources[f'{name}-sample.nc'])
        result = subprocess.run(['/bin/sh', str(script_dir/'s18-sample_bin2nc.sh')], cwd=script_dir,
                                env=dict(os.environ, CMF_V50_ROOT=str(ROOT)),
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertIn('Usage: ./conv_bin2nc.sh INPUT.bin REFERENCE', result.stdout)
        self.assertEqual(result.stdout.count('Binary -> NetCDF'), 2)
        for name, values in arrays.items():
            with netCDF4.Dataset(self.map/f'{name}-sample.nc') as ds:
                ds.set_auto_maskandscale(False)
                np.testing.assert_array_equal(ds[name][:], values)
                self.assertEqual(ds[name].dtype, values.dtype)
        self.assertEqual(list(binary_dir.glob('.*.tmp')), [])

    def test_shell_no_overwrite_preserves_existing_outputs(self):
        fixture = self.root/'fixture repository'
        map_root = fixture/'map/sample'
        local_script_dir = map_root/'script_format_conv'
        local_script_dir.mkdir(parents=True)
        script = local_script_dir/SCRIPT.name
        shutil.copy2(SCRIPT, script)
        shell_functions = fixture/'tools/shell_functions'
        shell_functions.mkdir(parents=True)
        shutil.copy2(ROOT/'tools/cmf_shell_functions.sh', fixture/'tools/cmf_shell_functions.sh')
        for name in ('cmf_check_shell_error.sh', 'cmf_select_hires_tag.sh'):
            shutil.copy2(ROOT/'tools/shell_functions'/name, shell_functions/name)
        fake = fixture/'map/tools/code/convert_map_binary_to_netcdf.py'
        fake.parent.mkdir(parents=True)
        fake.write_text("""import argparse
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--map-dir');p.add_argument('--input');p.add_argument('--output')
p.add_argument('--reference-binary');p.add_argument('--registry');p.add_argument('--force',action='store_true')
p.add_argument('--no-overwrite',action='store_true')
a=p.parse_args();target=Path(a.output)
if target.exists() and a.no_overwrite: raise SystemExit('no-overwrite violated')
target.parent.mkdir(parents=True,exist_ok=True)
target.write_bytes(Path(a.input).read_bytes())
print('copied',Path(a.input).name,'force='+str(a.force))
""")
        output = map_root
        shutil.copy2(self.map/'params.txt', map_root/'params.txt')
        binary_dir = map_root/'binary'
        binary_dir.mkdir()
        for name in ('subbsn','subcol'):
            (binary_dir/f'{name}-sample.bin').write_bytes(b'new-'+name.encode())
        for name in ('subbsn','subcol'):
            (binary_dir/f'{name}-sample.bin').write_bytes(b'new-'+name.encode())
            (output/f'{name}-sample.nc').write_bytes(b'old-'+name.encode())
        env = dict(os.environ, CMF_V50_ROOT=str(fixture))
        result = subprocess.run(['bash',str(script)],cwd=local_script_dir,env=env,
                                input='',capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('Converted: 2; skipped: 0',result.stdout)
        self.assertNotIn('Overwrite?',result.stdout)
        for name in ('subbsn','subcol'):
            self.assertEqual((output/f'{name}-sample.nc').read_bytes(),b'new-'+name.encode())
            (output/f'{name}-sample.nc').write_bytes(b'preserve-'+name.encode())
        result = subprocess.run(['bash',str(script),'--no-overwrite'],cwd=local_script_dir,env=env,
                                input='',capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('Converted: 0; skipped: 2',result.stdout)
        for name in ('subbsn','subcol'):
            self.assertEqual((output/f'{name}-sample.nc').read_bytes(),b'preserve-'+name.encode())

    def test_actual_mekong_pair_under_arbitrary_input_name(self):
        source = ROOT/'map/mekong_15min/binary/nextxy.bin'
        shutil.copy2(source.parent/'params.txt', self.map/'params.txt')
        args = self.args('unrelated-name.bin')
        shutil.copy2(source, args.input)
        converter.convert(args)
        nx, ny, *_ = converter.read_params(self.map/'params.txt')
        records = np.fromfile(source, dtype='<i4').reshape(2, ny, nx)
        with netCDF4.Dataset(args.output) as ds:
            ds.set_auto_maskandscale(False)
            for name, values in zip(('nextx', 'nexty'), records):
                self.assertEqual(ds[name].dtype, np.dtype('int32'))
                np.testing.assert_array_equal(ds[name][:], values)


if __name__ == '__main__':
    unittest.main()
