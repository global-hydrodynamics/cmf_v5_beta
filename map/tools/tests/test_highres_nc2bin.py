"""Focused byte-contract tests for high-resolution NetCDF to Binary restoration."""
import csv
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from map.tools.code import convert_highres_binary_to_netcdf as forward
from map.tools.code import convert_highres_netcdf_to_binary as reverse

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / 'variable_table/map_variables.csv'


def sha(data):
    return hashlib.sha256(data).hexdigest()


class RestorationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.map = Path(self.temp.name)
        self.nc = self.map / '1min'
        self.binary = self.map / 'binary' / '1min'
        self.nc.mkdir()
        self.binary.mkdir(parents=True)
        # Width crosses the production 256-cell chunk boundary; the two record planes differ.
        self.nx, self.ny = 259, 3
        text = ('2 narea\niarea carea west east south north nx ny csize\n'
                '1 a 0 25.9 9.7 10 259 3 0.1\n2 b 30 55.9 9.7 10 259 3 0.1\n')
        (self.nc / 'location.txt').write_text(text)
        areas = forward.read_location(self.nc / 'location.txt')
        rows = forward.registry_rows(REGISTRY)
        self.variables = ['visual', 'catmxy', 'fixture_int32', 'elevtn']
        selected = []
        for variable in ('visual', 'catmxy', 'elevtn'):
            selected.extend(forward.rows_for_tile(rows, '1min', 'a', variable))
        integer = dict(forward.rows_for_tile(rows, '1min', 'a', 'catmz100')[0])
        integer.update(name='fixture_int32', dtype='int32', missing_value='-2147483648',
                       binary_filename='<HIRES>/<AREA>.fixture_int32.bin')
        selected.append(integer)
        self.registry = self.map / 'registry.csv'
        with self.registry.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(selected[0]))
            writer.writeheader()
            writer.writerows(selected)
        self.expected = {}
        count = self.nx * self.ny
        # IEEE-754 sentinels, signed zeros, infinities and both quiet/signaling NaN payloads.
        float_bits = [0, 0x80000000, 0x3f800000, 0xbf800000, 0x7f800000,
                      0xff800000, 0x7fc00001, 0x7fa12345, 0xffc05678, 0xc61c3c00]
        for area in areas:
            for variable in self.variables:
                records = reverse.tile_rows(selected, '1min', area, variable)
                dtype = records[0]['dtype'].strip().lower()
                data = bytearray()
                for record in range(len(records)):
                    for i in range(count):
                        if dtype == 'int8':
                            data.extend(struct.pack('<b', [-128, -9, 0, 127][i % 4]))
                        elif dtype == 'int16':
                            data.extend(struct.pack('<h', [-32768, -9999, 0, 32767][(i+record) % 4]))
                        elif dtype == 'int32':
                            data.extend(struct.pack('<i', [-2147483648, -9999, 0, 2147483647][i % 4]))
                        else:
                            data.extend(struct.pack('<I', float_bits[i % len(float_bits)]))
                source = self.binary / f"{area['carea']}.{variable}.bin"
                source.write_bytes(data)
                records = forward.validate_tile(source, area, records)
                forward.write_netcdf(source, self.nc / f"{area['carea']}.{variable}.nc", area, records, 3)
                self.expected[source.name] = bytes(data)
                source.unlink()
        self.source_hashes = {p.name: sha(p.read_bytes()) for p in self.nc.iterdir()}

    def test_cli_accepts_multiple_tags_with_parallel_workers(self):
        shutil.copytree(self.nc, self.map / '3sec')
        result = subprocess.run([
            sys.executable, str(ROOT / 'map/tools/code/convert_highres_netcdf_to_binary.py'),
            '--map-dir', str(self.map), '--hires', '1min 3sec 1min',
            '--variables', ' '.join(self.variables), '--registry', str(self.registry),
            '--jobs', '2',
        ], text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for tag in ('1min', '3sec'):
            for name, original in self.expected.items():
                self.assertEqual((self.map / 'binary' / tag / name).read_bytes(), original)

    def test_exact_sha_roundtrip_jobs_skip_force_and_location(self):
        converted, skipped = reverse.restore(self.map, '1min', self.variables, self.registry, jobs=1)
        self.assertEqual((converted, skipped), (8, 0))
        for name, original in self.expected.items():
            self.assertEqual(sha((self.binary / name).read_bytes()), sha(original), name)
        self.assertEqual((self.binary / 'location.txt').read_bytes(), (self.nc / 'location.txt').read_bytes())
        modified = self.binary / 'a.visual.bin'
        modified.write_bytes(b'user-existing')
        self.assertEqual(reverse.restore(self.map, '1min', self.variables, self.registry, jobs=2, force=False), (0, 8))
        self.assertEqual(modified.read_bytes(), b'user-existing')
        self.assertEqual(reverse.restore(self.map, '1min', self.variables, self.registry, jobs=2), (8, 0))
        for name, original in self.expected.items():
            self.assertEqual(sha((self.binary / name).read_bytes()), sha(original), name)
        self.assertEqual(self.source_hashes, {p.name: sha(p.read_bytes()) for p in self.nc.iterdir()})

    def test_all_overwrites_existing_outputs_and_skips_missing_products(self):
        # One registered product is absent in one area, another in every area.
        (self.nc / 'b.visual.nc').unlink()
        rows = forward.registry_rows(self.registry)
        rows.extend(forward.rows_for_tile(forward.registry_rows(REGISTRY), '1min', 'a', 'grdare'))
        with self.registry.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        existing = self.binary / 'a.visual.bin'
        existing.write_bytes(b'user-existing')
        self.assertEqual(reverse.restore(self.map, '1min', ['all'], self.registry), (7, 0))
        self.assertEqual(existing.read_bytes(), self.expected['a.visual.bin'])
        existing.write_bytes(b'keep')
        self.assertEqual(reverse.restore(self.map, '1min', ['all'], self.registry, force=False), (0, 7))
        self.assertEqual(existing.read_bytes(), b'keep')
        for name, original in self.expected.items():
            if name not in ('a.visual.bin', 'b.visual.bin'):
                self.assertEqual((self.binary / name).read_bytes(), original, name)
        self.assertFalse((self.binary / 'b.visual.bin').exists())
        self.assertFalse(list(self.binary.glob('*.grdare.bin')))
        with self.assertRaisesRegex(ValueError, 'missing input tile'):
            reverse.restore(self.map, '1min', ['visual'], self.registry)

    def test_wrong_type_and_coordinates_fail_before_publication(self):
        rows = forward.registry_rows(self.registry)
        bad = [dict(r) for r in rows]
        for row in bad:
            if row['name'] == 'fixture_int32':
                row['dtype'] = 'int16'
        with self.registry.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(bad[0]))
            writer.writeheader()
            writer.writerows(bad)
        with self.assertRaisesRegex(ValueError, 'type, dimensions or order'):
            reverse.restore(self.map, '1min', ['fixture_int32'], self.registry)
        self.assertFalse(list(self.binary.glob('*.bin')))
        # Restore valid registry, then alter geometry while keeping a valid location file.
        (self.nc / 'location.txt').write_text((self.nc / 'location.txt').read_text().replace('1 a 0 25.9', '1 a 1 26.9'))
        with self.assertRaisesRegex(ValueError, 'conflicts with location.txt center'):
            reverse.restore(self.map, '1min', ['visual'], self.registry)
        self.assertFalse(list(self.binary.glob('*.bin')))

    def test_failed_chunk_preserves_existing_output_and_removes_temporary(self):
        area = forward.read_location(self.nc / 'location.txt')[0]
        rows = reverse.tile_rows(forward.registry_rows(self.registry), '1min', area, 'catmxy')
        source, output = self.nc / 'a.catmxy.nc', self.binary / 'a.catmxy.bin'
        output.write_bytes(b'previous-complete-output')
        lib = reverse.read_api()
        reader = lib.nc_get_vara
        calls = 0

        def fail_second(*args):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError('injected chunk read failure')
            return reader(*args)

        lib.nc_get_vara = fail_second
        with patch.object(reverse, 'read_api', return_value=lib):
            with self.assertRaisesRegex(RuntimeError, 'injected chunk'):
                reverse.restore_tile((source, output, area, rows, True))
        self.assertEqual(output.read_bytes(), b'previous-complete-output')
        self.assertFalse(list(self.binary.glob('*.tmp')))
        self.assertFalse(list(self.binary.glob('.*.tmp')))

    def test_conflicting_location_is_preserved_even_with_force(self):
        text = (self.nc / 'location.txt').read_text().replace('1 a 0 25.9', '1 a 1 26.9')
        target = self.binary / 'location.txt'
        target.write_text(text)
        with self.assertRaisesRegex(ValueError, 'conflicts with NetCDF geometry'):
            reverse.restore(self.map, '1min', self.variables, self.registry, force=True)
        self.assertEqual(target.read_text(), text)
        self.assertFalse(list(self.binary.glob('*.bin')))


if __name__ == '__main__':
    unittest.main()
