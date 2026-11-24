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
                    if script.name != "a00-link_codes.sh" and not script.name.endswith("write_ctl.sh")]
        self.assertTrue(wrappers)
        for script in wrappers:
            text = script.read_text()
            with self.subTest(script=script.name):
                self.assertIn("PYTHON_CMD=", text)
                self.assertIn(".py", text)
                self.assertNotRegex(text, r"\./(?:script_analysis/)?code/(?:analysis|param|region|allocate)_")

    def test_copied_map_local_analysis_runs_with_cmf5_root(self):
        with tempfile.TemporaryDirectory(prefix="cmf-python-shell-") as temporary:
            root = Path(temporary)
            map_dir = root / "map" / "mekong_15min"
            script_dir = map_dir / "script_analysis"
            script_dir.mkdir(parents=True)
            for name in ("params.txt", "nextxy.bin", "basin.bin", "upgrid.bin", "uparea.bin",
                         "ctmare.bin", "elevtn.bin", "lonlat.bin"):
                shutil.copy2(SAMPLE / name, map_dir / name)
            script = TOOLS / "script_analysis" / "a01-river_point_info.sh"
            shutil.copy2(script, script_dir / script.name)
            env = dict(os.environ, CMF5_ROOT=str(ROOT))
            result = subprocess.run(["sh", str(script_dir / script.name)], cwd=root, env=env,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = script_dir / "out_analysis" / "river_point_info.txt"
            self.assertTrue(report.is_file())
            self.assertIn("Fortran IX,IY:", report.read_text())


if __name__ == "__main__":
    unittest.main()
