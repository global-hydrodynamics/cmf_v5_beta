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

    def make_single_area(self, tag: str) -> None:
        directory = self.map_root / tag
        directory.mkdir(exist_ok=True)
        (directory / "location.csv").write_text(
            "iarea,carea,west,east,south,north,nx,ny,csize\n"
            f"  1,{tag},90,110,5,35,10,10,2\n",
            encoding="ascii",
        )
        (directory / f"{tag}.uparea.nc").touch()

    def make_multi_area(self, tag: str) -> None:
        directory = self.map_root / tag
        directory.mkdir(exist_ok=True)
        (directory / "location.csv").write_text(
            "iarea,carea,west,east,south,north,nx,ny,csize\n"
            "1,n30e120,90,110,5,35,10,10,2\n"
            "2,n35e120,90,110,5,35,10,10,2\n",
            encoding="ascii",
        )
        (directory / "n30e120.uparea.nc").touch()

    def select(self, configured: str, answer: str, single_area: bool = False) -> subprocess.CompletedProcess[str]:
        selector_args = '"$1" --single-area' if single_area else '"$1"'
        command = (
            f'CMF_V50_ROOT="{ROOT}"; export CMF_V50_ROOT; '
            f'. "{ENTRYPOINT}"; '
            f'HIRES_TAG=$(cmf_select_hires_tag {selector_args}) || exit $?; '
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

    def test_single_area_mode_recommends_coarsest_compatible_map(self) -> None:
        self.make_single_area("1min")
        self.make_multi_area("30sec")
        self.make_single_area("15sec")
        result = self.select("", "\n", single_area=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "1min\n")
        self.assertIn("Available single-area resolutions: 1min 15sec", result.stderr)
        self.assertIn("Recommended high-resolution map: 1min", result.stderr)

    def test_single_area_mode_confirms_explicit_valid_resolution(self) -> None:
        self.make_single_area("1min")
        result = self.select("1min", "yes\n", single_area=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "1min\n")
        self.assertIn("Use this map? [Y/n]: ", result.stderr)

    def test_single_area_mode_accepts_legacy_binary_layout(self) -> None:
        directory = self.map_root / "1min"
        directory.mkdir()
        (directory / "location.txt").write_text(
            "1 narea\n iarea carea west east south north nx ny csize\n"
            "1 1min 90 110 5 35 10 10 .0166667\n", encoding="ascii")
        (directory / "1min.uparea.bin").touch()
        result = self.select("", "\n", single_area=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "1min\n")

    def test_single_area_mode_rejects_multi_area_and_offers_only_valid_alternatives(self) -> None:
        self.make_single_area("1min")
        self.make_multi_area("15sec")
        result = self.select("15sec", "1min\n", single_area=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "1min\n")
        self.assertIn("contains multiple areas (2)", result.stderr)
        self.assertIn("Allocation requires a single-area", result.stderr)
        self.assertIn("Choose resolution from [1min]", result.stderr)
        self.assertNotIn("Use this map? [Y/n]", result.stderr)

    def test_single_area_mode_reprompts_after_invalid_candidate(self) -> None:
        self.make_single_area("1min")
        self.make_multi_area("15sec")
        result = self.select("1min", "n\n15sec\n1min\n", single_area=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "1min\n")
        self.assertIn("Choose one of the listed, nonempty resolutions.", result.stderr)

    def test_single_area_mode_rejects_inconsistent_location_or_tile_filenames(self) -> None:
        self.make_single_area("1min")
        inconsistent = self.map_root / "30sec"
        inconsistent.mkdir()
        (inconsistent / "location.txt").write_text(
            "1 narea\n iarea carea west east south north nx ny csize\n"
            "1 30sec 0 1 0 1 1 1 1\n", encoding="ascii")
        (inconsistent / "n30e120.uparea.nc").touch()
        result = self.select("30sec", "1min\n", single_area=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "1min\n")
        self.assertIn("No 30sec.<variable>.nc or 30sec.<variable>.bin files", result.stderr)

    def test_single_area_mode_fails_for_missing_location_or_no_compatible_candidate(self) -> None:
        missing = self.map_root / "1min"
        missing.mkdir()
        result = self.select("", "", single_area=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("No compatible single-area", result.stderr)

    def test_single_area_mode_eof_fails_at_confirmation(self) -> None:
        self.make_single_area("1min")
        result = self.select("", "", single_area=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("Could not read a confirmation", result.stderr)

    def run_wrapper(self, script_name: str, selected: str, single_area: bool = False) -> subprocess.CompletedProcess[str]:
        if single_area:
            self.make_single_area("1min")
            self.make_multi_area("3sec")
        else:
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
            input=f"{'yes' if single_area else 'n'}\n{selected}\n", text=True, capture_output=True,
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

    def test_allocation_wrappers_use_shared_single_area_selection(self) -> None:
        for script_name, python_name in (
            ("t01-alloc_flow_gauge.sh", "allocate_flow_gauge.py"),
            ("t02-alloc_dams.sh", "allocate_dam.py"),
            ("t03-alloc_level_gauge.sh", "allocate_level_gauge.py"),
        ):
            with self.subTest(script=script_name):
                result = self.run_wrapper(script_name, "", single_area=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                call = (self.root / "python-call.txt").read_text().splitlines()
                self.assertTrue(call[0].endswith(python_name))
                self.assertIn("1min", call)
                self.assertIn("--map-dir", call)


if __name__ == "__main__":
    unittest.main(verbosity=2)
