"""Check map-local channel-wrapper paths and failure handling with mock tools."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WRAPPER = ROOT / "map" / "tools" / "script_params" / "s01-channel_params.sh"


class ChannelParamsWrapperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="cmf-channel-wrapper-")
        self.root = Path(self.temporary.name)
        self.map_root = self.root / "map" / "sample"
        self.script_dir = self.map_root / "script_params"
        self.code_dir = self.root / "map" / "tools" / "code"
        self.shell_functions_dir = self.root / "tools" / "shell_functions"
        self.tools_dir = self.root / "tools"
        self.script_dir.mkdir(parents=True)
        self.code_dir.mkdir(parents=True)
        self.shell_functions_dir.mkdir(parents=True)
        shutil.copy2(ROOT / "tools" / "cmf_shell_functions.sh", self.tools_dir / "cmf_shell_functions.sh")
        for name in ("cmf_check_shell_error.sh", "cmf_select_hires_tag.sh"):
            shutil.copy2(ROOT / "tools" / "shell_functions" / name, self.shell_functions_dir / name)
        (self.root / "map" / "data").mkdir()
        (self.root / "outside").mkdir()
        (self.root / "map" / "data" / "ELSE_GPCC_clm-1981-2010.nc").write_bytes(b"runoff")
        for name in ("params.txt", "nextxy.bin", "ctmare.bin", "width.bin",
                     "inpmat_test-1deg.bin"):
            (self.map_root / name).write_bytes(b"input")
        (self.map_root / "diminfo_test-1deg.txt").write_text(
            "80\n120\n10\n360\n180\n4\ninpmat_test-1deg.bin\n"
            "90\n110\n35\n5\n", encoding="ascii"
        )
        self.calls = self.root / "calls.txt"
        for name, outputs in (
            ("param_channel_calc_outclm", ("outclm.nc",)),
            ("param_channel_calc_rivwth", ("rivwth.nc", "rivhgt.nc", "rivman.nc", "rivhgt_inf.nc", "rivpar.nc")),
            ("param_channel_set_merit_width", ("rivwth_merit.nc",)),
        ):
            program = self.code_dir / f"{name}.py"
            program.write_text(
                "import os, sys\nfrom pathlib import Path\n"
                "with open(os.environ['CALL_LOG'], 'a') as log:\n"
                "    log.write(os.getcwd() + '|' + sys.argv[0] + '|' + '|'.join(sys.argv[1:]) + '|\\n')\n"
                + "\n".join(f"Path('../{output}').write_text('x')" for output in outputs) + "\n",
                encoding="ascii",
            )
        script = self.script_dir / "s01-channel_params.sh"
        script.write_bytes(WRAPPER.read_bytes())
        script.chmod(0o755)
        self.script = script

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_runs_shared_programs_from_map_local_script_directory(self) -> None:
        env = {**os.environ, "CALL_LOG": str(self.calls), "CMF_V50_ROOT": str(self.root)}
        result = subprocess.run(
            [str(self.script)], cwd=self.script_dir, env=env,
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        records = [line.split("|") for line in self.calls.read_text().splitlines()]
        self.assertEqual(len(records), 3)
        self.assertTrue(all(Path(row[0]).resolve() == self.script_dir.resolve() for row in records))
        self.assertEqual([Path(row[1]).name for row in records], [
            "param_channel_calc_outclm.py", "param_channel_calc_rivwth.py",
            "param_channel_set_merit_width.py",
        ])
        self.assertEqual(records[0][2:], ["../diminfo_test-1deg.txt",
                                          str(self.root / "map" / "data" / "ELSE_GPCC_clm-1981-2010.nc"),
                                          "--map-dir", "..", ""])
        self.assertEqual(records[1][2:], ["../diminfo_test-1deg.txt", "0.1", "0.50", "0.00", "1.0",
                                          "2.50", "0.60", "0.00", "5.0", "--map-dir", "..", ""])
        self.assertEqual(records[2][2:], ["../diminfo_test-1deg.txt", "--map-dir", "..", ""])
        wrapper_text = self.script.read_text()
        self.assertIn('PYTHON_CMD="python3"', wrapper_text)
        self.assertIn('# CaMa-Flood general setting (check CMF root, import shell error checker)', wrapper_text)
        self.assertIn('# Optional Python CLI flags', wrapper_text)
        init = [
            '# CaMa-Flood general setting (check CMF root, import shell error checker)',
            'PYTHON_CMD="python3"',
            ': "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"',
            '. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"',
            '',
            '# ----------------------------------------------------------------------',
            '# User settings',
        ]
        lines = wrapper_text.splitlines()
        set_index = lines.index('set -eu')
        self.assertEqual(lines[set_index + 2:set_index + 9], init)
        self.assertNotIn('TYPE=', wrapper_text)
        self.assertNotIn('INTERP=', wrapper_text)
        self.assertNotIn('MAP_FORMAT=', wrapper_text)
        for name in ("outclm.nc", "rivwth.nc", "rivhgt.nc", "rivman.nc",
                     "rivhgt_inf.nc", "rivpar.nc", "rivwth_merit.nc"):
            self.assertTrue((self.map_root / name).is_file(), name)

    def test_missing_runoff_path_is_passed_to_the_python_program(self) -> None:
        (self.root / "map" / "data" / "ELSE_GPCC_clm-1981-2010.nc").unlink()
        result = subprocess.run(
            [str(self.script)], cwd=self.script_dir,
            env={**os.environ, "CALL_LOG": str(self.calls), "CMF_V50_ROOT": str(self.root)},
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        records = [line.split("|") for line in self.calls.read_text().splitlines()]
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0][3], str(self.root / "map" / "data" / "ELSE_GPCC_clm-1981-2010.nc"))

    def test_unset_cmf_root_fails_before_sourcing_library(self) -> None:
        env = {**os.environ, "CALL_LOG": str(self.calls)}
        env.pop("CMF_V50_ROOT", None)
        result = subprocess.run(
            [str(self.script)], cwd=self.script_dir, env=env,
            text=True, capture_output=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CMF_V50_ROOT is not set", result.stderr)
        self.assertFalse(self.calls.exists())

    def test_missing_shared_program_uses_python_error_and_common_failure_report(self) -> None:
        (self.code_dir / "param_channel_set_merit_width.py").unlink()
        result = subprocess.run(
            [str(self.script)], cwd=self.root / "outside",
            env={**os.environ, "CALL_LOG": str(self.calls), "CMF_V50_ROOT": str(self.root)},
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("param_channel_set_merit_width.py", result.stderr)
        self.assertIn("ERROR: s01-channel_params.sh FAILED", result.stderr)
        records = [line.split("|") for line in self.calls.read_text().splitlines()]
        self.assertEqual(len(records), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
