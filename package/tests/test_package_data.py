"""Import/Diff contracts: real temporary Git repositories; no scientific data writes."""

import argparse
from contextlib import redirect_stdout
import csv
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package_data as data


class PackageDataTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cmf package 日本 ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "development checkout"
        self.source = self.base / "cmf_v5_package_data"
        self.repo.mkdir()
        self.source.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        (self.repo / ".gitignore").write_text("/map/glb_15min/\n/map/TE-Japan_01min/\n/inp/ELSE_GPCC/\n")
        (self.repo / "package").mkdir()
        self.catalog = self.repo / "package/package_data.csv"
        shutil.copyfile(data.CATALOG, self.catalog)
        self.datasets = data.load_catalog(self.catalog)
        self.put(self.source, "inp/ELSE_GPCC/runoff2000.nc", b"CDF\x01runoff")
        for name, hires in [("glb_15min", "1min"), ("TE-Japan_01min", "15sec")]:
            root = f"map/{name}/"
            self.put(self.source, root + "params.txt", b"parameters")
            self.put(self.source, root + "netcdf/river.nc", b"CDF\x01river")
            self.put(self.source, root + f"{hires}_nc/location.txt", b"location")
            self.put(self.source, root + f"{hires}_nc/tile.nc", b"CDF\x01hires")
            for excluded in [f"{hires}/raw.bin", "script_params/run.sh", "src_old/source.F90", "code/tool",
                             "__pycache__/cache.pyc", ".git/config", "build.o", "model.mod", "run.log",
                             "temp.tmp", ".DS_Store", "source.F90", "Makefile", "convert.py"]:
                self.put(self.source, root + excluded, b"excluded")
        self.put(self.source, "inp/ELSE_GPCC/convert.py", b"excluded by include")

    @staticmethod
    def put(root, relative, content):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def args(self, command="install", **kwargs):
        values = dict(command=command, source=str(self.source), dataset=None, details=False,
                      output=None, dry_run=False, yes=True, overwrite_all=False)
        values.update(kwargs)
        return argparse.Namespace(**values)

    def run_tool(self, **kwargs):
        with redirect_stdout(io.StringIO()):
            return data.run(self.args(**kwargs), self.repo, self.catalog)

    def compare(self):
        return data.compare(self.source.resolve(), self.repo, self.datasets)

    def catalog_rows(self):
        with self.catalog.open(newline="") as stream:
            return list(csv.DictReader(stream))

    def save_catalog(self, rows, legacy=False):
        fields = list(data.COLUMNS) + ([] if legacy else ["exclude_patterns"])
        with self.catalog.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    def conflict(self):
        self.put(self.repo, "map/glb_15min/params.txt", b"local changes")

    def test_empty_import_and_repeat_skip_editable_copies(self):
        source_file = self.source / "map/glb_15min/params.txt"
        source_file.chmod(0o444)
        before = source_file.read_bytes()
        self.assertEqual(self.run_tool(), 0)
        rows = self.compare()
        self.assertEqual(len(rows), 9)
        self.assertTrue(all(d.status == "IDENTICAL" for d in rows))
        self.assertTrue((self.repo / "map/glb_15min/params.txt").stat().st_mode & 0o200)
        self.assertFalse((self.repo / "map/glb_15min/params.txt").is_symlink())
        with patch.object(data, "copy_verified", side_effect=AssertionError("must skip identical")):
            self.assertEqual(self.run_tool(), 0)
        self.assertEqual(source_file.read_bytes(), before)
        self.assertEqual(source_file.stat().st_mode & 0o777, 0o444)

    def test_missing_store_and_required_dataset(self):
        with self.assertRaisesRegex(data.DataError, "root not found"):
            self.run_tool(source=str(self.base / "absent"))
        shutil.rmtree(self.source / "map/TE-Japan_01min")
        with self.assertRaisesRegex(data.DataError, "Required source dataset"):
            self.run_tool()
        self.assertEqual(self.run_tool(dataset=["ELSE_GPCC"]), 0)

    def test_all_four_statuses_and_same_size_same_mtime_change(self):
        self.run_tool()
        modified = self.repo / "map/glb_15min/netcdf/river.nc"
        old = modified.stat()
        modified.write_bytes(b"CDF\x01RIVER")
        os.utime(modified, ns=(old.st_atime_ns, old.st_mtime_ns))
        (self.repo / "map/TE-Japan_01min/params.txt").unlink()
        self.put(self.repo, "map/glb_15min/custom.nc", b"local-only")
        statuses = {d.path.as_posix(): d.status for d in self.compare()}
        self.assertEqual(statuses["map/glb_15min/netcdf/river.nc"], "MODIFIED")
        self.assertEqual(statuses["map/TE-Japan_01min/params.txt"], "SOURCE_ONLY")
        self.assertEqual(statuses["map/glb_15min/custom.nc"], "TARGET_ONLY")
        self.assertEqual(statuses["inp/ELSE_GPCC/runoff2000.nc"], "IDENTICAL")

    def test_binary_difference_at_end_of_large_file(self):
        relative = "map/glb_15min/area.bin"
        contents = b"\x00" * (2 * data.CHUNK_SIZE + 13)
        self.put(self.source, relative, contents)
        self.put(self.repo, relative, contents[:-1] + b"\x01")
        row = next(d for d in self.compare() if d.path.as_posix() == relative)
        self.assertEqual(row.status, "MODIFIED")

    def test_exact_high_resolution_and_code_exclusions_both_sides(self):
        for root, hires in [("map/glb_15min", "1min"), ("map/TE-Japan_01min", "15sec")]:
            self.put(self.repo, root + "/script_local/user.sh", b"tracked-workflow-like")
            self.put(self.repo, root + "/" + hires + "/local.bin", b"raw")
            self.put(self.repo, root + "/local.py", b"source")
        rows = self.compare()
        self.assertEqual(len(rows), 9)
        names = {d.path.as_posix() for d in rows}
        self.assertIn("map/glb_15min/1min_nc/tile.nc", names)
        self.assertIn("map/TE-Japan_01min/15sec_nc/location.txt", names)
        self.run_tool()
        self.assertFalse((self.repo / "map/glb_15min/1min/raw.bin").exists())
        self.assertFalse((self.repo / "inp/ELSE_GPCC/convert.py").exists())
        self.assertEqual((self.repo / "map/glb_15min/script_local/user.sh").read_bytes(), b"tracked-workflow-like")

    def test_global_refusal_cancels_new_copies_too(self):
        self.conflict()
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value=""):
            self.assertEqual(self.run_tool(), 1)
        self.assertEqual((self.repo / "map/glb_15min/params.txt").read_bytes(), b"local changes")
        self.assertFalse((self.repo / "inp/ELSE_GPCC").exists())

    def test_approve_global_and_default_per_file(self):
        self.conflict()
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", side_effect=["y", "", "y"]) as prompt:
            self.assertEqual(self.run_tool(), 0)
        self.assertEqual(prompt.call_count, 3)
        self.assertEqual((self.repo / "map/glb_15min/params.txt").read_bytes(), b"parameters")

    def test_mixed_individual_approval(self):
        self.conflict()
        self.put(self.repo, "map/TE-Japan_01min/params.txt", b"Japan changes")
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", side_effect=["yes", "yes", "yes", ""]):
            self.assertEqual(self.run_tool(), 0)
        self.assertEqual((self.repo / "map/glb_15min/params.txt").read_bytes(), b"parameters")
        self.assertEqual((self.repo / "map/TE-Japan_01min/params.txt").read_bytes(), b"Japan changes")

    def test_skip_individual_prompts_and_overwrite_all_flag(self):
        self.conflict()
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", side_effect=["y", "n"]) as prompt:
            self.assertEqual(self.run_tool(), 0)
        self.assertEqual(prompt.call_count, 2)
        self.conflict()
        with patch("builtins.input", side_effect=AssertionError("explicit flag needs no prompt")):
            self.assertEqual(self.run_tool(overwrite_all=True), 0)

    def test_new_files_need_confirmation_unless_yes(self):
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value=""):
            self.assertEqual(self.run_tool(yes=False), 1)
        self.assertFalse((self.repo / "inp/ELSE_GPCC").exists())
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value="y"):
            self.assertEqual(self.run_tool(yes=False), 0)

    def test_noninteractive_conflict_is_never_approved_by_yes(self):
        self.conflict()
        with patch("sys.stdin.isatty", return_value=False):
            with self.assertRaisesRegex(data.DataError, "confirmation unavailable"):
                self.run_tool(yes=True)
        self.assertFalse((self.repo / "inp/ELSE_GPCC").exists())
        self.assertEqual((self.repo / "map/glb_15min/params.txt").read_bytes(), b"local changes")

    def test_diff_and_dry_run_do_not_write(self):
        self.conflict()
        before = {p.relative_to(self.repo): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        self.assertEqual(self.run_tool(command="diff", details=True), 0)
        self.assertEqual(self.run_tool(dry_run=True, details=True), 0)
        after = {p.relative_to(self.repo): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_target_only_is_retained_on_install(self):
        path = self.put(self.repo, "map/glb_15min/custom_parameter.nc", b"local work")
        self.run_tool(overwrite_all=True)
        self.assertEqual(path.read_bytes(), b"local work")
        self.assertEqual(next(d.status for d in self.compare() if d.target == path), "TARGET_ONLY")

    def test_store_root_symlink_and_unicode_space_file(self):
        link = self.base / "別の data link"
        link.symlink_to(self.source, target_is_directory=True)
        self.put(self.source, "map/glb_15min/観測 点.txt", b"utf8 path")
        self.assertEqual(self.run_tool(source=str(link)), 0)
        self.assertEqual((self.repo / "map/glb_15min/観測 点.txt").read_bytes(), b"utf8 path")

    def test_source_and_target_dataset_symlinks_rejected(self):
        for side in (self.source, self.repo):
            with self.subTest(side=side):
                link = side / "map/glb_15min/netcdf/link.nc"
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(self.base / "outside")
                with self.assertRaisesRegex(data.DataError, "Symlink"):
                    self.run_tool(overwrite_all=True)
                link.unlink()
        target = self.repo / "map/glb_15min"
        shutil.rmtree(target)
        target.symlink_to(self.base / "outside", target_is_directory=True)
        with self.assertRaisesRegex(data.DataError, "Symlink"):
            self.run_tool()

    def test_symlink_directory_inside_source_rejected(self):
        (self.source / "map/glb_15min/linked").symlink_to(self.repo, target_is_directory=True)
        with self.assertRaisesRegex(data.DataError, "Symlink"):
            self.run_tool()

    def test_overlapping_roots_rejected_both_directions(self):
        for path in [self.repo, self.repo / "data", self.base]:
            with self.subTest(path=path), self.assertRaisesRegex(data.DataError, "overlap"):
                self.run_tool(source=str(path))

    def test_unsafe_catalog_paths_duplicates_and_overlapping_targets(self):
        original = self.catalog_rows()
        for field, value in [("source_path", "../escape"), ("target_path", "/tmp/escape"),
                             ("target_path", "map/../escape"), ("target_path", "map/./data"),
                             ("file_pattern", "../*.nc"), ("target_path", ".git/objects")]:
            with self.subTest(field=field, value=value):
                rows = [dict(r) for r in original]
                rows[0][field] = value
                self.save_catalog(rows)
                with self.assertRaises(data.DataError):
                    data.load_catalog(self.catalog)
        rows = [dict(r) for r in original]
        rows[1]["dataset_id"] = rows[0]["dataset_id"]
        self.save_catalog(rows)
        with self.assertRaisesRegex(data.DataError, "duplicate"):
            data.load_catalog(self.catalog)
        rows = [dict(r) for r in original]
        rows[1]["target_path"] = rows[0]["target_path"] + "/nested"
        self.save_catalog(rows)
        with self.assertRaisesRegex(data.DataError, "Overlapping catalog"):
            data.load_catalog(self.catalog)

    def test_six_column_catalog_and_unknown_dataset(self):
        rows = self.catalog_rows()[:1]
        self.save_catalog(rows, legacy=True)
        self.assertEqual(self.run_tool(dataset=["ELSE_GPCC"]), 0)
        with self.assertRaisesRegex(data.DataError, "Unknown dataset"):
            self.run_tool(dataset=["unknown"])

    def test_git_tracked_file_is_error_even_with_overwrite_all(self):
        path = self.put(self.repo, "map/glb_15min/params.txt", b"tracked source")
        subprocess.run(["git", "-C", str(self.repo), "add", "-f", "map/glb_15min/params.txt"], check=True)
        with self.assertRaisesRegex(data.DataError, "Git-tracked"):
            self.run_tool(overwrite_all=True)
        self.assertEqual(path.read_bytes(), b"tracked source")
        self.assertFalse((self.repo / "inp/ELSE_GPCC").exists())

    def test_unignored_destination_is_error(self):
        (self.repo / ".gitignore").write_text("")
        with self.assertRaisesRegex(data.DataError, "not Git-ignored"):
            self.run_tool(overwrite_all=True)
        self.assertFalse((self.repo / "inp/ELSE_GPCC").exists())

    def test_failed_copy_preserves_previous_file_and_cleans_temp(self):
        self.conflict()
        row = next(d for d in self.compare() if d.path.as_posix() == "map/glb_15min/params.txt")
        def fail_copy(source, output, length):
            output.write(b"partial")
            raise OSError("simulated disk failure")
        with patch.object(data.shutil, "copyfileobj", side_effect=fail_copy), self.assertRaises(OSError):
            data.copy_verified(row, self.repo)
        self.assertEqual(row.target.read_bytes(), b"local changes")
        self.assertEqual(list(row.target.parent.glob(".cmf-import-*.tmp")), [])

    def test_verification_failure_preserves_previous_file(self):
        self.conflict()
        row = next(d for d in self.compare() if d.path.as_posix() == "map/glb_15min/params.txt")
        with patch.object(data.shutil, "copyfileobj", return_value=None), self.assertRaisesRegex(data.DataError, "verification"):
            data.copy_verified(row, self.repo)
        self.assertEqual(row.target.read_bytes(), b"local changes")
        self.assertEqual(list(row.target.parent.glob(".cmf-import-*.tmp")), [])

    def test_insufficient_space_stops_before_any_copy(self):
        usage = shutil._ntuple_diskusage(100, 100, 0)
        with patch.object(data.shutil, "disk_usage", return_value=usage), self.assertRaisesRegex(data.DataError, "Insufficient"):
            self.run_tool()
        self.assertFalse((self.repo / "inp/ELSE_GPCC").exists())

    def test_target_or_source_changed_after_diff(self):
        self.conflict()
        for change_source in (False, True):
            row = next(d for d in self.compare() if d.path.as_posix() == "map/glb_15min/params.txt")
            (row.source if change_source else row.target).write_bytes(b"changed since diff")
            with self.assertRaisesRegex(data.DataError, "changed since Diff"):
                data.copy_verified(row, self.repo)
            self.assertEqual(row.target.read_bytes(), b"changed since diff")

    def test_non_directory_destination_ancestor_stops_before_copy(self):
        path = self.put(self.repo, "map/glb_15min/netcdf", b"local file occupying directory")
        with self.assertRaisesRegex(data.DataError, "not a directory"):
            self.run_tool(overwrite_all=True)
        self.assertEqual(path.read_bytes(), b"local file occupying directory")
        self.assertFalse((self.repo / "inp/ELSE_GPCC").exists())

    def test_csv_report_and_data_git_metadata_protection(self):
        report = self.base / "差分 report.csv"
        self.assertEqual(self.run_tool(command="diff", output=str(report)), 0)
        with report.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 9)
        self.assertEqual({r["status"] for r in rows}, {"SOURCE_ONLY"})
        blocked = [self.source / "report.csv", self.repo / "map/glb_15min/report.csv", self.repo / ".git/config"]
        for path in blocked:
            with self.subTest(path=path), self.assertRaises(data.DataError):
                self.run_tool(command="diff", dataset=["ELSE_GPCC"], output=str(path))
        tracked = self.repo / "tracked.md"
        tracked.write_text("original")
        subprocess.run(["git", "-C", str(self.repo), "add", "tracked.md"], check=True)
        with self.assertRaisesRegex(data.DataError, "Git-tracked"):
            self.run_tool(command="diff", output=str(tracked))
        self.assertEqual(tracked.read_text(), "original")

    def test_wrappers_from_another_cwd_and_noninteractive_exit(self):
        for filename in ("package_data.py", "install_package_data.sh", "diff_package_data.sh"):
            shutil.copyfile(Path(data.__file__).parent / filename, self.repo / "package" / filename)
        diff = subprocess.run(["bash", str(self.repo / "package/diff_package_data.sh"), "--dataset", "ELSE_GPCC", "--details"],
                              cwd=self.base, capture_output=True, text=True)
        self.assertEqual(diff.returncode, 0, diff.stderr)
        self.assertIn("Selected source files: 1", diff.stdout)
        self.conflict()
        install = subprocess.run(["bash", str(self.repo / "package/install_package_data.sh"), "--yes"],
                                 cwd=self.base, input="y\ny\ny\n", capture_output=True, text=True)
        self.assertEqual(install.returncode, 2)
        self.assertIn("confirmation unavailable", install.stderr)
        self.assertFalse((self.repo / "inp/ELSE_GPCC").exists())
        dry = subprocess.run(["bash", str(self.repo / "package/install_package_data.sh"), "--dry-run"],
                             cwd=self.base, capture_output=True, text=True)
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertIn("Dry-run: no files changed", dry.stdout)


if __name__ == "__main__":
    unittest.main()
