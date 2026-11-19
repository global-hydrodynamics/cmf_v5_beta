"""Committed-source selection and failure-safety contracts in tiny Git fixtures."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parents[1]


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cmf archive 日本 ")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "source repo"
        self.repo.mkdir()
        self.git("init", "-q")
        (self.repo / "package").mkdir()
        for name in ("p01-archive_clean_repo.sh", "archive_clean_repo.py", "package_source_exclude.txt"):
            shutil.copy2(PACKAGE / name, self.repo / "package" / name)
        self.put(".gitignore", "/package/repo_clean_*/\n/package/.repo_clean_tmp.*/\n/additional/\n")
        for name in ("AGENTS.md", "CONTRIBUTING.md", "LICENSE", "src_main/model.F90",
                     "legacy/src/old.F90", "docs/design.md", "map/mekong_15min/sample.bin",
                     "inp/sample.nc", "tutorial/test.txt", "visualization/test.py",
                     "config/example.txt", "tools/source.F90", "gosh_test/run.sh",
                     "variable_table/map.csv", "tests/example.py"):
            self.put(name, "committed data\n")
        self.put("research/record.md", "exclude\n")
        self.put(".github/workflows/build.yml", "exclude\n")
        self.put("src_main/.gitignore", "exclude\n")
        self.put(".gitattributes", "*.bin binary\n")
        self.put("src_main/.gitattributes", "# excluded\n")
        self.put(".gitmodules", "# excluded\n")
        self.put("tools/.gitmodules", "# excluded\n")
        self.put("docs/not.gitignore.txt", "keep literal near match\n")
        self.put("docs/research/guide.md", "keep non-root research\n")
        self.put("tools/run.sh", "#!/bin/sh\nexit 0\n").chmod(0o755)
        (self.repo / "tools/link").symlink_to("../src_main")
        self.commit()
        self.commit_id = self.git("rev-parse", "HEAD").strip()
        self.script = self.repo / "package/p01-archive_clean_repo.sh"
        self.version = self.script.read_text().split('VER="', 1)[1].split('"', 1)[0]
        # Freeze the date in this fixture to avoid midnight-sensitive tests.
        self.script.write_text(self.script.read_text().replace(self.version, "v5b01_test"))
        self.output = self.repo / "package/repo_clean_v5b01_test"

    def put(self, name, value):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)
        return path

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True)

    def commit(self):
        self.git("add", "-A")
        self.git("-c", "user.name=Archive test", "-c", "user.email=archive@example.invalid",
                 "commit", "-qm", "fixture")

    def run_archive(self, *args, env=None):
        return subprocess.run(["bash", str(self.script), *args], cwd=self.temp.name,
                              text=True, capture_output=True, env=env)

    def test_dry_run_and_exact_committed_tree_from_other_directory(self):
        self.put("src_main/model.F90", "uncommitted edit\n")
        self.put("untracked.txt", "do not include\n")
        self.put("additional/large.nc", "ignored additional data\n")
        dry = self.run_archive("--dry-run")
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertFalse(self.output.exists())
        self.assertIn(self.commit_id, dry.stdout)
        self.assertIn("Estimated source size:", dry.stdout)
        self.assertIn("WARNING", dry.stderr)
        result = self.run_archive()
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("AGENTS.md", "CONTRIBUTING.md", "legacy/src/old.F90", "docs/design.md",
                     "map/mekong_15min/sample.bin", "inp/sample.nc", "tools/run.sh",
                     "docs/not.gitignore.txt", "docs/research/guide.md"):
            self.assertTrue((self.output / name).is_file(), name)
            self.assertEqual((self.output / name).read_bytes(),
                             subprocess.check_output(["git", "-C", str(self.repo), "show", f"HEAD:{name}"]))
        self.assertEqual((self.output / "src_main/model.F90").read_text(), "committed data\n")
        for name in (".git", ".github", "research", "additional", "untracked.txt"):
            self.assertFalse((self.output / name).exists(), name)
        self.assertFalse(any(p.name in (".gitignore", ".gitattributes", ".gitmodules") for p in self.output.rglob("*")))
        self.assertTrue(os.access(self.output / "tools/run.sh", os.X_OK))
        self.assertTrue((self.output / "tools/link").is_symlink())
        self.assertEqual(os.readlink(self.output / "tools/link"), "../src_main")
        self.assertIn("Source commit: " + self.commit_id,
                      (self.output / "package/PACKAGE_BUILD_INFO.txt").read_text())
        self.assertFalse((self.output / "PACKAGE_BUILD_INFO.txt").exists())
        self.assertEqual(self.git("check-ignore", "package/repo_clean_v5b01_test/src_main/model.F90").strip(),
                         "package/repo_clean_v5b01_test/src_main/model.F90")
        (self.output / "sentinel").write_text("keep")
        self.assertNotEqual(self.run_archive().returncode, 0)
        self.assertEqual((self.output / "sentinel").read_text(), "keep")

    def test_tracked_nested_build_info_cannot_be_overwritten(self):
        self.put("package/PACKAGE_BUILD_INFO.txt", "retained source provenance")
        self.commit()
        result = self.run_archive()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conflict with generated provenance", result.stderr)
        self.assertFalse(self.output.exists())
        self.assertEqual((self.repo / "package/PACKAGE_BUILD_INFO.txt").read_text(), "retained source provenance")

    def test_generated_tree_is_never_nested_even_if_forced_tracked(self):
        self.put("package/repo_clean_old/old.txt", "never nest\n")
        self.git("add", "-f", "package/repo_clean_old/old.txt")
        self.commit()
        result = self.run_archive()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.output / "package/repo_clean_old").exists())
        self.assertIn("generated clean-source tree: 1", result.stdout)

    def test_absolute_escape_and_symlink_chain_rejected_without_output(self):
        for target in ("/private/tmp", "../../outside"):
            link = self.repo / "tools/bad"
            if link.is_symlink():
                link.unlink()
            link.symlink_to(target)
            self.commit()
            result = self.run_archive("--dry-run")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlink", result.stderr.lower())
            self.assertFalse(self.output.exists())

    def test_archive_failure_and_attribute_substitution_leave_no_final_tree(self):
        # export-ignore must not silently drop a committed source file.
        self.put(".gitattributes", "src_main/model.F90 export-ignore\n")
        self.commit()
        result = self.run_archive()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertEqual(list((self.repo / "package").glob(".repo_clean_tmp.*")), [])
        self.put(".gitattributes", "*.bin binary\n")
        self.commit()
        fake = Path(self.temp.name) / "fake commands"
        fake.mkdir()
        (fake / "tar").write_text("#!/bin/sh\nexit 17\n")
        (fake / "tar").chmod(0o755)
        env = dict(os.environ, PATH=str(fake) + os.pathsep + os.environ["PATH"])
        self.assertNotEqual(self.run_archive(env=env).returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertEqual(list((self.repo / "package").glob(".repo_clean_tmp.*")), [])

    def test_output_symlink_and_invalid_version_do_not_touch_destination(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (outside / "sentinel").write_text("keep")
        self.output.symlink_to(outside, target_is_directory=True)
        self.assertNotEqual(self.run_archive().returncode, 0)
        self.assertEqual((outside / "sentinel").read_text(), "keep")
        self.output.unlink()
        self.script.write_text(self.script.read_text().replace('VER="v5b01_test"', 'VER="../../escape"'))
        self.assertNotEqual(self.run_archive("--dry-run").returncode, 0)
        self.assertEqual((outside / "sentinel").read_text(), "keep")

    def test_publication_refuses_even_empty_existing_directory(self):
        # Exercise the atomic no-replace boundary independently of the early check.
        import importlib.util
        spec = importlib.util.spec_from_file_location("archive_helper", PACKAGE / "archive_clean_repo.py")
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        staging = Path(self.temp.name) / "stage"
        staging.mkdir()
        destination = Path(self.temp.name) / "already there"
        destination.mkdir()
        with self.assertRaises(OSError):
            helper.publish(staging, destination)
        self.assertTrue(staging.exists())
        self.assertTrue(destination.exists())


if __name__ == "__main__":
    unittest.main()
