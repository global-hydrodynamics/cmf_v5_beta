"""Focused checks that maintained map Shell workflows call the Python tools."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "map" / "tools"
SAMPLE = ROOT / "map" / "mekong_15min"
PARAM_SCRIPTS = TOOLS / "script_params"


class PythonShellMigrationTests(unittest.TestCase):
    def test_analysis_parameter_and_region_templates_call_python_sources(self):
        folders = ("script_params", "script_region", "script_format_conv")
        wrappers = [script for folder in folders for script in (TOOLS / folder).glob("*.sh")
                    if script.name not in {"a01-sample_get_river_point_info.sh",
                                           "a02-sample_calc_upbasin.sh",
                                           "a03-advanced_calc_upbasin.sh"}
                    and not script.name.endswith("write_ctl.sh")
                    and "sample" not in script.name]
        self.assertTrue(wrappers)
        for script in wrappers:
            text = script.read_text()
            with self.subTest(script=script.name):
                self.assertIn("PYTHON_CMD=", text)
                self.assertIn(".py", text)
                self.assertNotRegex(text, r"\./(?:script_params/)?code/(?:analysis|param|region|allocate)_")

    def test_river_point_command_forwards_queries_and_sample_writes_only_stdout(self):
        with tempfile.TemporaryDirectory(prefix="cmf-python-shell-") as temporary:
            root = Path(temporary)
            script_dir = root / "map" / "mekong_15min" / "script_params"
            script_dir.mkdir(parents=True)
            for name in ("get_river_point_info.sh", "a01-sample_get_river_point_info.sh"):
                shutil.copy2(TOOLS / "script_params" / name, script_dir / name)

            fake_bin = root / "bin"
            fake_bin.mkdir()
            python = fake_bin / "python3"
            python.write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$CAPTURE\"\n"
                "printf 'Point Information\\nFortran IX,IY: 62 93\\n'\n",
                encoding="utf-8",
            )
            python.chmod(0o755)
            capture = root / "arguments.txt"
            env = dict(os.environ, CMF_V50_ROOT=str(ROOT), CAPTURE=str(capture),
                       PATH=f"{fake_bin}:{os.environ['PATH']}")
            result = subprocess.run([str(script_dir / "get_river_point_info.sh"), "xy", "62", "93"],
                                    cwd=script_dir, env=env,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Point Information", result.stdout)
            self.assertEqual(capture.read_text().splitlines(),
                             [f"{ROOT}/map/tools/code/analysis_river_point_info.py xy 62 93"])

            capture.unlink()
            before = set(script_dir.iterdir())
            result = subprocess.run([str(script_dir / "a01-sample_get_river_point_info.sh")],
                                    cwd=script_dir, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("xy IX IY", result.stdout)
            self.assertIn("latlon LAT LON", result.stdout)
            self.assertEqual(result.stdout.count("Point Information"), 2)
            self.assertEqual(capture.read_text().splitlines(), [
                f"{ROOT}/map/tools/code/analysis_river_point_info.py xy 62 93",
                f"{ROOT}/map/tools/code/analysis_river_point_info.py latlon 11.579 104.946",
            ])
            self.assertEqual(set(script_dir.iterdir()), before)

    def test_upbasin_command_forwards_xy_and_sample_explains_workflow(self):
        with tempfile.TemporaryDirectory(prefix="cmf-upbasin-shell-") as temporary:
            root = Path(temporary)
            script_dir = root / "map" / "mekong_15min" / "script_params"
            script_dir.mkdir(parents=True)
            for name in ("calc_upbasin.sh", "a02-sample_calc_upbasin.sh"):
                shutil.copy2(TOOLS / "script_params" / name, script_dir / name)

            fake_bin = root / "bin"
            fake_bin.mkdir()
            python = fake_bin / "python3"
            python.write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$CAPTURE\"\n"
                "printf 'Upstream Grid #: 4\\nUpstream Area [km2]: 12\\n'\n",
                encoding="utf-8",
            )
            python.chmod(0o755)
            capture = root / "arguments.txt"
            env = dict(os.environ, CMF_V50_ROOT=str(ROOT), CAPTURE=str(capture),
                       PATH=f"{fake_bin}:{os.environ['PATH']}")
            command = script_dir / "calc_upbasin.sh"

            result = subprocess.run([str(command), "xy", "62", "93"], cwd=root,
                                    env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("IX=62, IY=93", result.stdout)
            self.assertIn("Upstream Grid #: 4", result.stdout)
            self.assertIn("Output file: ../upbasin-62-93.nc", result.stdout)
            expected_python = f"{ROOT}/map/tools/code/analysis_upbasin.py"
            self.assertEqual(capture.read_text().splitlines(), [
                f"{expected_python} 62 93 ../upbasin-62-93.nc",
            ])

            capture.unlink()
            result = subprocess.run(
                [str(command), "xy", "62", "93", "./upbasin-sample.nc"], cwd=script_dir,
                env=env, text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Output file: ./upbasin-sample.nc", result.stdout)
            self.assertEqual(capture.read_text().splitlines(), [
                f"{expected_python} 62 93 ./upbasin-sample.nc",
            ])

            capture.unlink()
            result = subprocess.run([str(command), "latlon", "11.5", "104.9"],
                                    cwd=script_dir, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("Usage:", result.stderr)
            self.assertFalse(capture.exists())

            before = set(script_dir.iterdir())
            result = subprocess.run([str(script_dir / "a02-sample_calc_upbasin.sh")],
                                    cwd=script_dir, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("One-based CaMa-Flood grid indices", result.stdout)
            self.assertIn("confirm the target cell", result.stdout)
            self.assertIn("grid (62, 93)", result.stdout)
            self.assertEqual(capture.read_text().splitlines(), [
                f"{expected_python} 62 93 ./upbasin-sample.nc",
            ])
            self.assertEqual(set(script_dir.iterdir()), before)


    def test_advanced_grdc_example_uses_largest_valid_allocated_station(self):
        with tempfile.TemporaryDirectory(prefix="cmf-grdc-example-") as temporary:
            root = Path(temporary)
            map_root = root / "map" / "mekong_15min"
            script_dir = map_root / "script_params"
            script_dir.mkdir(parents=True)
            for name in ("get_river_point_info.sh", "calc_upbasin.sh", "a03-advanced_calc_upbasin.sh"):
                shutil.copy2(PARAM_SCRIPTS / name, script_dir / name)
                (script_dir / name).chmod(0o755)

            header = "ID lat lon area_Input area_CaMa error diff Type ix1 iy1 ix2 iy2 area1 area2\n"
            rows = (
                "unallocated 10 100 900 900 0 0 -9 62 93 -999 -999 -999 -999\n"
                "smaller 10 100 200 250 0 0 1 61 92 -999 -999 200 -999\n"
                "winner 11 101 120 500 0 0 1 62 93 -999 -999 120 -999\n"
                "tie-later 12 102 130 500 0 0 1 63 94 -999 -999 130 -999\n"
            )
            (map_root / "GRDC_alloc.txt").write_text(header + rows)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            python = fake_bin / "python3"
            python.write_text(
                "#!/bin/sh\ncase \"$1\" in\n"
                "*analysis_river_point_info.py) printf 'Point Information\\nFortran IX,IY: %s %s\\n' \"$3\" \"$4\" ;;\n"
                "*analysis_upbasin.py) printf '%s\\n' \"$*\" >> \"$CAPTURE\"; : > \"$4\"; printf 'Upstream Grid #: 10\\nUpstream Area [km2]: 12\\n' ;;\nesac\n",
                encoding="utf-8",
            )
            python.chmod(0o755)
            capture = root / "arguments.txt"
            env = dict(os.environ, CMF_V50_ROOT=str(ROOT), CAPTURE=str(capture),
                       PATH=f"{fake_bin}:{os.environ['PATH']}")
            result = subprocess.run([str(script_dir / "a03-advanced_calc_upbasin.sh")],
                                    cwd=root, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            selection = (map_root / "grdc_station_selection.txt").read_text()
            self.assertIn("winner", selection)
            self.assertNotIn("tie-later", selection)
            self.assertIn("IX=62, IY=93", result.stdout)
            self.assertIn("../upbasin-winner.nc", capture.read_text())
            self.assertTrue((map_root / "upbasin-winner.nc").is_file())


if __name__ == "__main__":
    unittest.main()
