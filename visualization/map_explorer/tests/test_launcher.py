"""Focused tests for isolated profile setup and platform-specific selection."""
import contextlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import launch_desktop as launcher


class LauncherSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="map explorer ")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.stdout = contextlib.redirect_stdout(io.StringIO())
        self.stderr = contextlib.redirect_stderr(io.StringIO())
        self.stdout.__enter__()
        self.stderr.__enter__()
        self.addCleanup(self.stdout.__exit__, None, None, None)
        self.addCleanup(self.stderr.__exit__, None, None, None)
        self.runtime = ([sys.executable], {
            "python": list(sys.version_info[:3]),
            "implementation": "CPython",
            "macos": "13.7.8" if sys.platform == "darwin" else "",
            "machine": "arm64" if sys.platform == "darwin" else "x86_64",
        })

    def test_consent_is_requested_once_and_decline_changes_nothing(self):
        for answer in ("", "n", "no"):
            with self.subTest(answer=answer), \
                 patch.object(launcher.sys.stdin, "isatty", return_value=True), \
                 patch("builtins.input", return_value=answer) as prompt, \
                 patch.object(launcher, "python_candidates") as candidates:
                self.assertEqual(launcher.prepare_environment(self.directory, [], ["rasterio"]), 0)
                prompt.assert_called_once()
                candidates.assert_not_called()
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_noninteractive_setup_does_not_prompt_or_create(self):
        with patch.object(launcher.sys.stdin, "isatty", return_value=False), \
             patch("builtins.input") as prompt, patch.object(launcher, "python_candidates") as candidates:
            self.assertEqual(launcher.prepare_environment(self.directory, [], ["netCDF4"]), 1)
            prompt.assert_not_called()
            candidates.assert_not_called()
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_fallback_uses_standard_then_2024_and_preserves_arguments(self):
        venv = self.directory / ".venv-macos-2024"
        python = venv / "bin/python"
        argv = ["/a map", "--port", "5009", "--no-browser"]
        with patch.object(launcher.sys, "platform", "darwin"), \
             patch.object(launcher.sys.stdin, "isatty", return_value=True), \
             patch("builtins.input", return_value="yes"), \
             patch.object(launcher, "python_candidates", return_value=[self.runtime]), \
             patch.object(launcher, "build_profile", side_effect=[
                 (None, "netCDF4 import failed: NumPy ABI incompatibility", False),
                 ((venv, python), "validated", False),
             ]) as build, \
             patch.object(launcher.subprocess, "run", return_value=SimpleNamespace(returncode=7)) as run:
            self.assertEqual(launcher.prepare_environment(self.directory, argv, ["netCDF4"]), 7)
        self.assertEqual([call.args[1] for call in build.call_args_list], ["standard", "2024"])
        self.assertEqual(run.call_args.args[0], [str(python), str(self.directory / "code/launch_desktop.py"), *argv])
        self.assertEqual(run.call_args.kwargs["env"]["VIRTUAL_ENV"], str(venv))

    def test_2022_is_attempted_only_after_standard_and_2024(self):
        venv = self.directory / ".venv-macos-2022"
        python = venv / "bin/python"
        python310 = ([sys.executable], {**self.runtime[1], "python": [3, 10, 9]})
        with patch.object(launcher.sys, "platform", "darwin"), \
             patch.object(launcher.sys.stdin, "isatty", return_value=True), \
             patch("builtins.input", return_value="y"), \
             patch.object(launcher, "python_candidates", return_value=[python310]), \
             patch.object(launcher, "build_profile", side_effect=[
                 (None, "standard dependencies invalid", False),
                 (None, "2024 dependencies invalid", False),
                 ((venv, python), "2022 isolated smoke check passed", False),
             ]) as build, \
             patch.object(launcher.subprocess, "run", return_value=SimpleNamespace(returncode=0)):
            self.assertEqual(launcher.prepare_environment(self.directory, [], ["Panel"]), 0)
        self.assertEqual([call.args[1] for call in build.call_args_list], ["standard", "2024", "2022"])

    def test_valid_current_environment_skips_setup_and_preserves_map_arguments(self):
        map_dir = self.directory / "sample map"
        map_dir.mkdir()
        (map_dir / "params.txt").write_text("4 NX\n3 NY\n1 NLFP\n1 spacing\n10 west\n14 east\n20 south\n23 north\n")

        class LocalSocket:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def setsockopt(self, *args):
                pass

            def bind(self, *args):
                pass

        with patch.object(launcher, "validate_environment", return_value=(True, "ready")), \
             patch.object(launcher, "prepare_environment") as setup, \
             patch("map_datasets.resolve_map", return_value=map_dir), \
             patch.object(launcher.socket, "socket", return_value=LocalSocket()), \
             patch("app.main") as serve:
            self.assertEqual(launcher.main([str(map_dir), "--port", "5009", "--no-browser"]), 0)
        setup.assert_not_called()
        serve.assert_called_once()
        self.assertIn(str(map_dir), launcher.sys.argv)
        self.assertEqual(launcher.sys.argv[launcher.sys.argv.index("--port") + 1], "5009")

    def test_successful_profile_skips_older_profile_and_removes_test_flag(self):
        venv = self.directory / ".venv-macos-2024"
        python = venv / "bin/python"
        argv = ["--test-setup-profile", "2024", "map", "--port", "5010"]
        with patch.object(launcher.sys, "platform", "darwin"), \
             patch.object(launcher.sys.stdin, "isatty", return_value=True), \
             patch("builtins.input", return_value="y"), \
             patch.object(launcher, "python_candidates", return_value=[self.runtime]), \
             patch.object(launcher, "build_profile", return_value=((venv, python), "ok", False)) as build, \
             patch.object(launcher.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
            self.assertEqual(launcher.prepare_environment(self.directory, argv, ["forced profile test"],
                                                           test_profile="2024"), 0)
        build.assert_called_once()
        self.assertEqual(build.call_args.args[1], "2024")
        self.assertEqual(run.call_args.args[0][-3:], ["map", "--port", "5010"])

    def test_network_failure_stops_profile_fallback(self):
        with patch.object(launcher.sys.stdin, "isatty", return_value=True), \
             patch("builtins.input", return_value="y"), \
             patch.object(launcher, "python_candidates", return_value=[self.runtime]), \
             patch.object(launcher, "build_profile", return_value=(None, "PyPI connection timed out", True)) as build:
            self.assertEqual(launcher.prepare_environment(self.directory, [], ["numpy"]), 1)
        build.assert_called_once()

    def test_2022_is_last_profile_and_version_limited(self):
        self.assertEqual(launcher.PROFILES, ("standard", "2024", "2022"))
        python310 = {"python": [3, 10, 9], "implementation": "CPython"}
        python311 = {"python": [3, 11, 0], "implementation": "CPython"}
        self.assertTrue(launcher.profile_compatible("2022", python310))
        self.assertFalse(launcher.profile_compatible("2022", python311))
        self.assertFalse(launcher.profile_compatible("2024", {**python311, "implementation": "PyPy"}))

    def test_platform_profiles_do_not_share_environment_paths(self):
        with patch.object(launcher.sys, "platform", "darwin"):
            mac = launcher.profile_environment(self.directory, "standard")
        with patch.object(launcher.sys, "platform", "win32"):
            windows = launcher.profile_environment(self.directory, "standard")
        self.assertNotEqual(mac, windows)
        self.assertEqual(mac.name, ".venv-macos-standard")
        self.assertEqual(windows.name, ".venv-windows-standard")

    def test_wsl_profile_is_stored_in_linux_home_cache(self):
        with patch.object(launcher.sys, "platform", "linux"), \
             patch.dict(os.environ, {"WSL_DISTRO_NAME": "Ubuntu"}):
            root = launcher.environment_root(self.directory)
        self.assertEqual(root.parts[-3:-1], (".cache", "cmf-map-explorer"))
        self.assertNotEqual(root, self.directory)

    def test_validation_checks_prefix_pip_imports_and_optional_app(self):
        python = self.directory / "bin/python"
        outputs = [SimpleNamespace(returncode=0, stderr="", stdout="") for _ in range(3)]
        with patch.object(launcher.subprocess, "run", side_effect=outputs) as run:
            passed, _ = launcher.validate_environment(python, self.directory, self.directory,
                                                      initialize_app=True)
        self.assertTrue(passed)
        self.assertEqual(run.call_count, 3)
        self.assertIn("pip", run.call_args_list[1].args[0])
        self.assertIn("Explorer", run.call_args_list[2].args[0][2])

    def test_macos_requirement_selection_and_wheel_guard(self):
        self.assertEqual(launcher.requirements_for(self.directory, "standard", True),
                         self.directory / "requirements-macos.txt")
        self.assertEqual(launcher.requirements_for(self.directory, "2024", True),
                         self.directory / "config/requirements_2024.txt")
        for filename in ("requirements-macos.txt", "config/requirements_2024.txt",
                         "config/requirements_2022.txt"):
            self.assertTrue((ROOT / filename).is_file())

    def test_macos_profile_install_is_wheel_only_and_keeps_existing_venv_separate(self):
        (self.directory / "config").mkdir()
        (self.directory / "config/requirements_2024.txt").write_text("numpy==1.26.4\n")
        old_environment = self.directory / ".venv"
        old_environment.mkdir()
        interpreter = ([sys.executable], {
            "python": [3, 12, 3], "implementation": "CPython", "macos": "13.7.8", "machine": "arm64",
        })

        def command(cmd, **kwargs):
            if "venv" in cmd:
                Path(cmd[-1]).mkdir()
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with patch.object(launcher.sys, "platform", "darwin"), \
             patch.object(launcher, "macos_setup_error", return_value=None), \
             patch.object(launcher.subprocess, "run", side_effect=command) as run, \
             patch.object(launcher, "validate_environment", return_value=(True, "ok")):
            environment, _, _ = launcher.build_profile(self.directory, "2024", interpreter)
        install = next(call.args[0] for call in run.call_args_list if "install" in call.args[0])
        self.assertIn("--only-binary=:all:", install)
        self.assertIn(str(self.directory / "config/requirements_2024.txt"), install)
        self.assertEqual(environment[0], self.directory / ".venv-macos-2024")
        self.assertTrue(old_environment.is_dir())

    @unittest.skipIf(sys.platform == "win32", "POSIX wrapper check")
    def test_terminal_and_mac_wrappers_prefer_local_venv_and_delegate(self):
        tools = self.directory / "visualization/map_explorer"
        tools.mkdir(parents=True)
        log = self.directory / "arguments.txt"
        for base, tag in [(tools, "local"), (self.directory, "shared")]:
            python = base / ".venv/bin/python"
            python.parent.mkdir(parents=True)
            python.write_text('#!/bin/sh\nprintf "%s\\n" "' + tag + '" "$@" > "$LAUNCH_TEST_LOG"\n')
            python.chmod(0o755)
        map_dir = self.directory / "test map"
        map_dir.mkdir()
        env = {k: v for k, v in os.environ.items() if k not in ("PYTHON", "VIRTUAL_ENV")}
        env["LAUNCH_TEST_LOG"] = str(log)
        for name in ("run.sh", "launch_mac.command"):
            shutil.copy2(ROOT / name, tools / name)
            result = subprocess.run(["bash", str(tools / name), str(map_dir), "--no-browser"],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = log.read_text().splitlines()
            self.assertEqual(lines[0], "local")
            self.assertEqual(lines[1], str(tools / "code/launch_desktop.py"))
            self.assertIn(str(map_dir), lines)


if __name__ == "__main__":
    unittest.main()
