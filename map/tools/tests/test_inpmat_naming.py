"""Verify runoff and high-resolution tags remain separate in s03."""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WRAPPER = ROOT / "map" / "tools" / "script_params" / "s01-inpmat_default.sh"


class InputMatrixNamingTests(unittest.TestCase):
    def test_user_configured_rofftag_derives_pair_and_hires_tag_selects_map(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmf-inpmat-name-") as temporary:
            root = Path(temporary)
            map_root = root / "map" / "sample"
            script_dir = map_root / "script_params"
            code_dir = root / "map" / "tools" / "code"
            hires_dir = map_root / "15sec"
            script_dir.mkdir(parents=True)
            code_dir.mkdir(parents=True)
            hires_dir.mkdir()
            (map_root / "params.txt").write_text("3\n2\n2\n1\n-1.5\n1.5\n-1\n1\n", encoding="ascii")
            (hires_dir / "location.txt").write_text("1\narea west east south north nx ny cell\n1 tile\n", encoding="ascii")
            (hires_dir / "tile.catmxy.nc").write_bytes(b"fixture")

            program = code_dir / "param_inpmat_generate"
            program.write_text(
                "#!/bin/sh\n"
                "hires=$1; diminfo=$8; inpmat=$9\n"
                "printf '%s\\n%s\\n%s\\n' \"$hires\" \"$diminfo\" \"$inpmat\" > ../called.args\n"
                "printf '&DIMINFO\\n NX=3, NY=2, NLFP=2, NXIN=360, NYIN=180, INPN=1,\\n INPMAT_FILE=\\\'%s\\\', WEST=-1.5, EAST=1.5, NORTH=1, SOUTH=-1\\n/\\n' \"$inpmat\" > ../\"$diminfo\"\n"
                "printf x > ../\"$inpmat\"\n",
                encoding="ascii",
            )
            program.chmod(0o755)
            program_path = code_dir / "param_inpmat_generate.py"
            program.rename(program_path)
            tools_dir = root / "tools"
            shell_functions = tools_dir / "shell_functions"
            shell_functions.mkdir(parents=True)
            (tools_dir / "cmf_shell_functions.sh").write_bytes(
                (ROOT / "tools" / "cmf_shell_functions.sh").read_bytes()
            )
            for name in ("cmf_check_shell_error.sh", "cmf_select_hires_tag.sh"):
                (shell_functions / name).write_bytes(
                    (ROOT / "tools" / "shell_functions" / name).read_bytes()
                )
            bin_dir = root / "bin"
            bin_dir.mkdir()
            python_cmd = bin_dir / "python3"
            python_cmd.write_text("#!/bin/sh\nprogram=$1\nshift\nexec \"$program\" \"$@\"\n", encoding="ascii")
            python_cmd.chmod(0o755)
            script = script_dir / WRAPPER.name
            script_text = WRAPPER.read_text(encoding="utf-8")
            script_text = script_text.replace(
                'ROFFTAG="test-1deg"', 'ROFFTAG="rainfall-025"'
            ).replace('HIRES_TAG=""', 'HIRES_TAG="15sec"')
            script.write_text(script_text, encoding="utf-8")
            script.chmod(0o755)

            result = subprocess.run(
                [str(script)], cwd=script_dir,
                env=dict(os.environ, CMF_V50_ROOT=str(root), PATH=f"{bin_dir}:{os.environ['PATH']}"),
                input="\n", text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((map_root / "diminfo_rainfall-025.nml").is_file(),
                            result.stdout + result.stderr)
            self.assertTrue((map_root / "inpmat_rainfall-025.nc").is_file())
            self.assertIn("inpmat_rainfall-025.nc",
                          (map_root / "diminfo_rainfall-025.nml").read_text())
            self.assertEqual((map_root / "called.args").read_text().splitlines(), [
                "15sec", "diminfo_rainfall-025.nml", "inpmat_rainfall-025.nc"
            ])
            self.assertIn("[STEP 1/1] Map river cells to the configured runoff grid", result.stdout)
            self.assertEqual(result.stdout.count("[SUCCESS]"), 1)


if __name__ == "__main__":
    unittest.main()
