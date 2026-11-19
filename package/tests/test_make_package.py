"""Package assembly contracts using small sources/stores; never copy real datasets."""
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import make_package as builder
import package_data as data


class AssemblyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cmf assembly 日本 ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.package = self.base / "development checkout/package"
        self.package.mkdir(parents=True)
        for name in ('make_package.sh', 'make_package.py', 'package_data.py', 'archive_clean_repo.py', 'package_data.csv'):
            shutil.copy2(builder.PACKAGE / name, self.package / name)
        self.version = 'v5b01_20261119'
        self.clean = self.package / ('repo_clean_' + self.version)
        self.clean.mkdir()
        self.source = self.base / 'cmf_v5_package_data'
        self.source.mkdir()
        self.output = self.package / ('cmf_' + self.version + '_pkg')
        for directory in builder.MAJOR_DIRS:
            self.put(self.clean, directory + '/retained.txt', b'clean source')
        self.put(self.clean, 'AGENTS.md', b'guidelines')
        self.put(self.clean, 'CONTRIBUTING.md', b'contributing')
        self.put(self.clean, 'tools/run.sh', b'#!/bin/sh\nexit 0\n').chmod(0o755)
        (self.clean / 'tools/link').symlink_to('../src_main')
        self.put(self.clean, 'PACKAGE_BUILD_INFO.txt',
            ('Package version: ' + self.version + '\nSource repository: cmf_v5_beta\nSource commit: ' + 'a'*40 +
             '\nSource branch: feature/package-builder\nArchive date: 2026-11-19T00:00:00+0900\n'
             'Archive tool: package/archive_clean_repo.sh\nPackage stage: Clean Git source extraction\n').encode())
        self.put(self.source, 'inp/ELSE_GPCC/runoff2000.nc', b'runoff')
        self.put(self.source, 'inp/ELSE_GPCC/convert.py', b'not selected')
        for name, resolution in [('glb_15min','1min'), ('TE-Japan_01min','15sec')]:
            for path in ('netcdf/map.nc', resolution+'_nc/tile.nc', 'COG/'+resolution+'/tile.tif', 'script_params/run.sh'):
                f = self.put(self.source, 'map/'+name+'/'+path, b'dataset content')
                if path.endswith('.sh'):
                    f.chmod(0o755)
            for path in (resolution+'/raw.bin', '__pycache__/cached.pyc', 'build.o', 'run.log'):
                self.put(self.source, 'map/'+name+'/'+path, b'excluded')

    @staticmethod
    def put(root, name, content):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def plan(self, source='../../cmf_v5_package_data'):
        with redirect_stdout(io.StringIO()):
            return builder.plan(self.package, self.version, source)

    def assemble(self, plan=None):
        with redirect_stdout(io.StringIO()):
            return builder.assemble(plan or self.plan())

    @staticmethod
    def snapshot(root):
        return {str(p.relative_to(root)): (builder.token(p), os.readlink(p) if p.is_symlink() else
                hashlib.sha256(p.read_bytes()).hexdigest()) for p in root.rglob('*') if p.is_symlink() or p.is_file()}

    def test_complete_assembly_manifest_and_readonly_inputs(self):
        before_clean, before_source = self.snapshot(self.clean), self.snapshot(self.source)
        manifest = self.assemble()
        self.assertEqual(self.snapshot(self.clean), before_clean)
        self.assertEqual(self.snapshot(self.source), before_source)
        self.assertEqual((self.output/'tools/run.sh').read_bytes(), (self.clean/'tools/run.sh').read_bytes())
        self.assertTrue(os.access(self.output/'tools/run.sh', os.X_OK))
        self.assertTrue(os.access(self.output/'map/glb_15min/script_params/run.sh', os.X_OK))
        self.assertEqual(os.readlink(self.output/'tools/link'), '../src_main')
        self.assertTrue((self.output/'map/glb_15min/COG/1min/tile.tif').is_file())
        self.assertTrue((self.output/'map/TE-Japan_01min/COG/15sec/tile.tif').is_file())
        for path in ('map/glb_15min/1min', 'map/TE-Japan_01min/15sec', 'inp/ELSE_GPCC/convert.py', '.git', 'research'):
            self.assertFalse((self.output/path).exists(), path)
        on_disk = json.loads((self.output/builder.MANIFEST).read_text())
        self.assertEqual(manifest, on_disk)
        self.assertEqual(on_disk['source_git_commit'], 'a'*40)
        self.assertEqual(on_disk['additional_data_source']['path'], '../../cmf_v5_package_data')
        self.assertIsNone(on_disk['additional_data_source']['version'])
        self.assertEqual([x['file_count'] for x in on_disk['datasets']], [1,4,4])
        self.assertEqual(on_disk['package_totals']['file_count'], len(self.snapshot(self.output)))
        self.assertEqual(on_disk['package_totals']['bytes'], sum(p.lstat().st_size for p in self.output.rglob('*') if p.is_file() or p.is_symlink()))
        for row in on_disk['files']:
            p = self.output/row['path']
            payload = os.fsencode(os.readlink(p)) if p.is_symlink() else p.read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(), row['sha256'])
        for p in self.output.rglob('*'):
            if p.is_symlink():
                self.assertTrue(data.within(p.resolve(), self.output.resolve()))

    def test_cli_default_is_package_relative_from_multiple_cwds_and_dry_writes_nothing(self):
        before = self.snapshot(self.base)
        for cwd in (self.package, self.package.parent, Path('/private/tmp')):
            result = subprocess.run(['bash', str(self.package/'make_package.sh'), '--dry-run'],
                                    cwd=cwd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(self.source), result.stdout)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.snapshot(self.base), before)

    def test_absolute_and_symlinked_store_roots_use_same_selection(self):
        default = self.plan()
        linked = self.base/'linked store'
        linked.symlink_to(self.source, target_is_directory=True)
        self.assertEqual(self.plan(str(linked))['selected'], default['selected'])
        self.assertEqual(self.plan(str(self.source))['selected'], default['selected'])
        script = self.package/'make_package.sh'
        script.write_text(script.read_text().replace('../../cmf_v5_package_data', str(linked)))
        result = subprocess.run(['bash', str(script)], cwd='/private/tmp', capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((self.output/builder.MANIFEST).read_text())['additional_data_source']['path'], 'linked store')

    def test_missing_inputs_and_version_errors_do_not_create_output(self):
        shutil.rmtree(self.source/'inp/ELSE_GPCC')
        with self.assertRaisesRegex(data.DataError, 'missing'):
            self.plan()
        self.assertFalse(self.output.exists())
        self.source.rename(self.base/'elsewhere')
        with self.assertRaisesRegex(data.DataError, 'missing'):
            self.plan()
        (self.base/'elsewhere').rename(self.source)
        (self.clean/'PACKAGE_BUILD_INFO.txt').write_text('Package version: wrong\n')
        with self.assertRaisesRegex(data.DataError, 'version'):
            self.plan()
        shutil.rmtree(self.clean)
        with self.assertRaisesRegex(data.DataError, 'Clean Repository'):
            self.plan()

    def test_clean_source_cannot_force_excluded_binary_into_distribution(self):
        self.put(self.clean, 'map/glb_15min/1min/raw.bin', b'not distributable')
        with self.assertRaisesRegex(data.DataError, 'catalog exclusion'):
            self.plan()
        self.assertFalse(self.output.exists())

    def test_existing_output_and_containment_are_rejected(self):
        self.output.mkdir()
        (self.output/'keep').write_text('retain')
        with self.assertRaisesRegex(data.DataError, 'already exists'):
            self.plan()
        self.assertEqual((self.output/'keep').read_text(), 'retain')
        shutil.rmtree(self.output)
        with self.assertRaisesRegex(data.DataError, 'overlap'):
            self.plan(str(self.clean))

    def test_duplicate_identical_skips_copy_and_conflict_stops_before_staging(self):
        duplicate = 'map/glb_15min/netcdf/map.nc'
        self.put(self.clean, duplicate, (self.source/duplicate).read_bytes())
        plan = self.plan()
        self.assertEqual(plan['summaries'][1]['identical_duplicates'], 1)
        original_copy = builder.copy_one
        copied = []
        def spy(source, stamp, relative, tree):
            copied.append(relative)
            return original_copy(source, stamp, relative, tree)
        with patch.object(builder, 'copy_one', side_effect=spy):
            self.assemble(plan)
        self.assertEqual(copied.count(duplicate), 1)
        shutil.rmtree(self.output)
        (self.clean/duplicate).write_bytes(b'conflicting')
        with self.assertRaisesRegex(data.DataError, 'Conflicting path: '+duplicate):
            self.plan()
        self.assertEqual(list(self.package.glob('.cmf-package-*')), [])

    def test_unsafe_links_and_generated_or_development_paths_rejected(self):
        link = self.clean/'tools/link'
        link.unlink(); link.symlink_to(self.source)
        with self.assertRaisesRegex(data.DataError, 'Unsafe'):
            self.plan()
        link.unlink(); link.symlink_to('../src_main')
        for bad in ('research/record.md', 'package/cmf_old_pkg/data', 'package/repo_clean_old/data', 'tools/.gitignore'):
            p = self.put(self.clean, bad, b'do not ship')
            with self.assertRaisesRegex(data.DataError, 'Forbidden'):
                self.plan()
            p.unlink()
            # Empty forbidden directory is also rejected; remove fixture parents.
            while p.parent != self.clean and not any(p.parent.iterdir()):
                p = p.parent; p.rmdir()
        symlink = self.source/'map/glb_15min/unsafe.nc'
        symlink.symlink_to(self.source/'inp/ELSE_GPCC/runoff2000.nc')
        with self.assertRaisesRegex(data.DataError, 'Symlink'):
            self.plan()

    def test_mutation_copy_failure_and_low_disk_leave_no_package(self):
        plan = self.plan()
        source = self.source/'inp/ELSE_GPCC/runoff2000.nc'
        source.write_bytes(b'changed since plan')
        with self.assertRaises(data.DataError):
            self.assemble(plan)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.package.glob('.cmf-package-*')), [])
        with patch.object(data, 'copy_verified', side_effect=OSError('injected disk failure')):
            with self.assertRaises(OSError):
                self.assemble()
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.package.glob('.cmf-package-*')), [])
        with patch.object(shutil, 'disk_usage', return_value=shutil._ntuple_diskusage(1,1,0)):
            with self.assertRaisesRegex(data.DataError, 'Insufficient'):
                self.plan()

    def test_large_file_copy_uses_bounded_chunks_and_detects_corruption(self):
        large = self.source/'inp/ELSE_GPCC/runoff2001.nc'
        with large.open('wb') as stream:
            stream.truncate(5*data.CHUNK_SIZE+17)
        original = shutil.copyfileobj
        sizes = []
        def bounded(source, dest, length=0):
            sizes.append(length)
            return original(source, dest, length)
        with patch.object(shutil, 'copyfileobj', side_effect=bounded):
            self.assemble()
        self.assertTrue(sizes)
        self.assertEqual(set(sizes), {data.CHUNK_SIZE})
        shutil.rmtree(self.output)
        original_copy = builder.copy_one
        def corrupt(source, stamp, relative, tree):
            original_copy(source, stamp, relative, tree)
            if relative.endswith('runoff2001.nc'):
                (tree/relative).write_bytes(b'corrupted')
        with patch.object(builder, 'copy_one', side_effect=corrupt):
            with self.assertRaisesRegex(data.DataError, 'differs'):
                self.assemble()
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.package.glob('.cmf-package-*')), [])


if __name__ == '__main__':
    unittest.main()
