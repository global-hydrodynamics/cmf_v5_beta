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


class PythonShellMigrationTests(unittest.TestCase):
    def test_analysis_parameter_and_region_templates_call_python_sources(self):
        folders = ("script_analysis", "script_params", "script_region")
        wrappers = [script for folder in folders for script in (TOOLS / folder).glob("*.sh")
                    if script.name not in {"a00-link_codes.sh", "a01-sample_get_river_point_info.sh",
                                           "a02-sample_calc_upbasin.sh"}
                    and not script.name.endswith("write_ctl.sh")]
        self.assertTrue(wrappers)
        for script in wrappers:
            text = script.read_text()
            with self.subTest(script=script.name):
                self.assertIn("PYTHON_CMD=", text)
                self.assertIn(".py", text)
                self.assertNotRegex(text, r"\./(?:script_analysis/)?code/(?:analysis|param|region|allocate)_")

    def test_river_point_command_forwards_queries_and_sample_writes_only_stdout(self):
        with tempfile.TemporaryDirectory(prefix="cmf-python-shell-") as temporary:
            root = Path(temporary)
            script_dir = root / "map" / "mekong_15min" / "script_analysis"
            script_dir.mkdir(parents=True)
            for name in ("get_river_point_info.sh", "a01-sample_get_river_point_info.sh"):
                shutil.copy2(TOOLS / "script_analysis" / name, script_dir / name)

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
            script_dir = root / "map" / "mekong_15min" / "script_analysis"
            script_dir.mkdir(parents=True)
            for name in ("calc_upbasin.sh", "a02-sample_calc_upbasin.sh"):
                shutil.copy2(TOOLS / "script_analysis" / name, script_dir / name)

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


if __name__ == "__main__":
    unittest.main()
