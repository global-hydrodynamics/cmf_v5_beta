"""Focused checks for the public Shell import and interactive hires selector."""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENTRYPOINT = ROOT / "tools" / "cmf_shell_functions.sh"


class SharedShellFunctionsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="cmf-hires-select-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.map_root = self.root / "map" / "sample"
        self.script_dir = self.map_root / "script_params"
        self.script_dir.mkdir(parents=True)

    def make_resolutions(self, *tags: str) -> None:
        for tag in tags:
            (self.map_root / tag).mkdir(exist_ok=True)

    def select(self, configured: str, answer: str) -> subprocess.CompletedProcess[str]:
        command = (
            f'CMF_V50_ROOT="{ROOT}"; export CMF_V50_ROOT; '
            f'. "{ENTRYPOINT}"; '
            'HIRES_TAG=$(cmf_select_hires_tag "$1") || exit $?; '
            'printf "%s\\n" "$HIRES_TAG"'
        )
        return subprocess.run(
            ["/bin/sh", "-c", command, "test", configured], cwd=self.script_dir,
            input=answer, text=True, capture_output=True, check=False, timeout=5,
        )

    def test_public_entrypoint_imports_without_traps_or_processing(self) -> None:
        result = subprocess.run(
            ["/bin/sh", "-c",
             f'CMF_V50_ROOT="{ROOT}"; export CMF_V50_ROOT; '
             f'before=$(trap); . "{ENTRYPOINT}"; after=$(trap); '
             '[ "$before" = "$after" ] && '
             'command -v cmf_check_init >/dev/null && '
             'command -v cmf_select_hires_tag >/dev/null && printf imported'],
            text=True, capture_output=True, check=False, timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "imported")

    def test_single_available_resolution_is_recommended_and_only_tag_is_stdout(self) -> None:
        self.make_resolutions("3sec")
        result = self.select("", "\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "3sec\n")
        self.assertIn("Available resolutions: 3sec", result.stderr)
        self.assertIn("Recommended high-resolution map: 3sec", result.stderr)
        self.assertIn("Use this map? [Y/n]: ", result.stderr)

    def test_multiple_resolutions_can_decline_recommendation_and_choose(self) -> None:
        self.make_resolutions("1min", "15sec", "3sec")
        result = self.select("", "n\n15sec\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "15sec\n")
        self.assertIn("Available resolutions: 1min 15sec 3sec", result.stderr)

    def test_explicit_available_tag_can_be_accepted(self) -> None:
        self.make_resolutions("1min", "15sec")
        result = self.select("15sec", "YES\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "15sec\n")
        self.assertIn("Selected high-resolution map: 15sec", result.stderr)

    def test_explicit_tag_can_be_rejected_and_replaced_without_second_confirmation(self) -> None:
        self.make_resolutions("1min", "15sec", "3sec")
        result = self.select("15sec", "no\n3sec\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "3sec\n")

    def test_invalid_config_and_invalid_alternative_are_reported(self) -> None:
        self.make_resolutions("1min", "3sec")
        result = self.select("30sec", "2sec\n3sec\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "3sec\n")
        self.assertIn("Configured high-resolution map is not available: 30sec", result.stderr)
        self.assertIn("Choose one of the listed, nonempty resolutions.", result.stderr)

    def test_invalid_confirmation_is_reprompted(self) -> None:
        self.make_resolutions("1min")
        result = self.select("", "maybe\nyes\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "1min\n")
        self.assertIn("Please answer Yes or No", result.stderr)

    def test_no_available_resolution_fails(self) -> None:
        result = self.select("", "")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("No supported high-resolution map directory", result.stderr)

    def test_eof_fails_without_looping(self) -> None:
        self.make_resolutions("1min")
        result = self.select("", "")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("Could not read a confirmation", result.stderr)

    def run_wrapper(self, script_name: str, selected: str) -> subprocess.CompletedProcess[str]:
        self.make_resolutions("1min", "3sec")
        script_dir = self.script_dir
        script = script_dir / script_name
        source = ROOT / "map" / "tools" / "script_params" / script_name
        script.write_bytes(source.read_bytes())
        script.chmod(0o755)
        fake_bin = self.root / "bin"
        fake_bin.mkdir(exist_ok=True)
        call_log = self.root / "python-call.txt"
        fake_python = fake_bin / "python3"
        fake_python.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$CALL_LOG\"\n",
            encoding="ascii",
        )
        fake_python.chmod(0o755)
        return subprocess.run(
            [str(script)], cwd=script_dir,
            env={**os.environ, "CMF_V50_ROOT": str(ROOT), "CALL_LOG": str(call_log),
                 "PATH": f"{fake_bin}:{os.environ['PATH']}"},
            input=f"n\n{selected}\n", text=True, capture_output=True,
            check=False, timeout=5,
        )

    def test_s03_wrapper_passes_shared_selection_to_python(self) -> None:
        result = self.run_wrapper("s01-inpmat_default.sh", "3sec")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        call = (self.root / "python-call.txt").read_text().splitlines()
        self.assertTrue(call[0].endswith("param_inpmat_generate.py"))
        self.assertEqual(call[1], "3sec")

    def test_s04_wrapper_passes_shared_selection_to_python(self) -> None:
        result = self.run_wrapper("s04-permanent_water.sh", "3sec")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        call = (self.root / "python-call.txt").read_text().splitlines()
        self.assertTrue(call[0].endswith("param_water_calc_prmwat.py"))
        self.assertEqual(call[1], "3sec")


if __name__ == "__main__":
    unittest.main(verbosity=2)
