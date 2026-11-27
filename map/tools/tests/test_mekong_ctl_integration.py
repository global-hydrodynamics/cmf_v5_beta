"""Run the map-local CTL wrapper against a temporary copy of Mekong binaries."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SAMPLE = ROOT / "map" / "mekong_15min"


class MekongCtlWrapperIntegrationTests(unittest.TestCase):
    def test_wrapper_generates_descriptors_for_all_committed_sample_binaries(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmf-mekong-ctl-") as temporary:
            temp_root = Path(temporary)
            map_root = temp_root / "map"
            fixture = map_root / "mekong_15min"
            (map_root / "tools" / "code").mkdir(parents=True)
            (temp_root / "tools").mkdir(parents=True)
            (fixture / "script_format_conv").mkdir(parents=True)
            (fixture / "1min").mkdir(parents=True)
            (fixture / "binary" / "1min").mkdir(parents=True)

            registry_dir = temp_root / "variable_table"
            registry_dir.mkdir()
            shutil.copy2(ROOT / "variable_table" / "map_variables.csv",
                          registry_dir / "map_variables.csv")
            for name in ("generate_ctl.py", "map_metadata.py", "migrate_map_params.py"):
                shutil.copy2(ROOT / "map" / "tools" / "code" / name,
                             map_root / "tools" / "code" / name)
            (temp_root / "tools" / "cmf_shell_functions.sh").write_text(
                "cmf_check_init(){ :; }\ncmf_check_step(){ :; }\ncmf_check_success(){ :; }\n",
                encoding="utf-8",
            )
            shutil.copy2(ROOT / "map" / "tools" / "script_format_conv" / "s09-write_ctl.sh",
                         fixture / "script_format_conv" / "s09-write_ctl.sh")
            for name in ("params.txt", "diminfo_test-1deg.txt"):
                shutil.copy2(SAMPLE / "binary" / name, fixture / "binary" / name)
            shutil.copy2(SAMPLE / "params.txt", fixture / "params.txt")
            shutil.copy2(SAMPLE / "params.toml", fixture / "params.toml")
            shutil.copy2(SAMPLE / "diminfo_test-1deg.txt", fixture / "diminfo_test-1deg.txt")
            shutil.copy2(SAMPLE / "1min" / "location.txt", fixture / "1min" / "location.txt")
            for path in (SAMPLE / "binary").glob("*.bin"):
                shutil.copy2(path, fixture / "binary" / path.name)
            shutil.copy2(SAMPLE / "binary" / "1min" / "location.txt",
                         fixture / "binary" / "1min" / "location.txt")
            for path in (SAMPLE / "binary" / "1min").glob("*.bin"):
                shutil.copy2(path, fixture / "binary" / "1min" / path.name)

            process = subprocess.run(
                ["sh", "s09-write_ctl.sh"], cwd=fixture / "script_format_conv",
                text=True, capture_output=True, check=False,
                env={**os.environ, "CMF_V50_ROOT": str(temp_root)},
            )
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            summaries = [tuple(map(int, match)) for match in re.findall(
                r"Summary: generated=(\d+), skipped=(\d+), failed=(\d+), fallback=(\d+)", process.stdout
            )]
            self.assertEqual(len(summaries), 5, process.stdout + process.stderr)
            expected = (len(list((SAMPLE / "binary").glob("*.bin"))),
                        len(list((SAMPLE / "binary" / "1min").glob("*.bin"))))
            # Two base-map registry entries intentionally have no declared
            # missing-value sentinel, so CTL generation reports those fallback
            # defaults. Fallback warnings do not mean a binary was skipped or
            # failed to receive a descriptor.
            # The Mekong-specific runoff matrix is not registered in the
            # shared map-variable table, so the CTL generator skips it.
            # The two sample variants likewise use standard definitions through
            # explicit NetCDF conversion rather than CTL auto-discovery.
            # Numbered MPI regions now resolve to the standard mpireg row.
            self.assertEqual(
                [summary[:3] for summary in summaries],
                [(expected[0] - 4, 4, 0), (expected[1], 0, 0),
                 (1, 0, 0), (1, 0, 0), (1, 0, 0)],
                process.stdout + process.stderr,
            )
            self.assertIn("SKIP inpmat_repo-mek_1deg.bin: input matrix needs its paired dimension description", process.stdout)

            for variant in ("subbsn-sample.bin", "subcol-sample.bin"):
                self.assertIn(f"SKIP {variant}: not registered", process.stdout)

            binary_map = fixture / "binary"
            base_ctls = list(binary_map.glob("*.ctl"))
            high_ctls = list((binary_map / "1min").glob("*.ctl"))
            self.assertEqual(len(base_ctls), expected[0] - 1)
            self.assertEqual(len(high_ctls), expected[1])
            for ctl in base_ctls + high_ctls:
                text = ctl.read_text(encoding="utf-8")
                self.assertIn("options yrev little_endian", text, ctl.name)
                self.assertRegex(text, r"(?m)^dset \^.+\.bin$", ctl.name)
                self.assertNotRegex(text, r"(?m)^\w+_hires\s", ctl.name)

            self.assertIn("xdef 80 linear", (binary_map / "nextxy.ctl").read_text())
            self.assertIn("vars 2", (binary_map / "nextxy.ctl").read_text())
            self.assertIn("nextx 1 -1,40,4", (binary_map / "nextxy.ctl").read_text())
            self.assertIn("undef -9999", (binary_map / "nextxy.ctl").read_text())
            noedge_ctl = (binary_map / "nextxy_noedge.ctl").read_text()
            self.assertIn("nextx 1 -1,40,4", noedge_ctl)
            self.assertIn("nexty 1 -1,40,4", noedge_ctl)
            self.assertIn("downx 1 -1,40,4", (binary_map / "downxy.ctl").read_text())
            self.assertIn("downy 1 -1,40,4", (binary_map / "downxy.ctl").read_text())
            self.assertIn("zdef 10 linear", (binary_map / "fldhgt.ctl").read_text())
            self.assertIn("zdef 4 linear", (binary_map / "inpmat_test-1deg.ctl").read_text())
            self.assertIn("xdef 1200 linear", (binary_map / "1min" / "1min.catmxy.ctl").read_text())
            catmxy_ctl = (binary_map / "1min" / "1min.catmxy.ctl").read_text()
            self.assertIn("catmxx 1 -1,40,2,-1", catmxy_ctl)
            self.assertIn("catmyy 1 -1,40,2,-1", catmxy_ctl)
            high_downxy_ctl = (binary_map / "1min" / "1min.downxy.ctl").read_text()
            self.assertIn("downx 1 -1,40,2,-1", high_downxy_ctl)
            self.assertIn("downy 1 -1,40,2,-1", high_downxy_ctl)
            for name, sentinel in (("1min.catmz100.ctl", 247), ("1min.catmzz.ctl", 247),
                                   ("1min.flwdir.ctl", 247), ("1min.visual.ctl", 247),
                                   ("1min.downxy.ctl", -9999)):
                ctl_text = (binary_map / "1min" / name).read_text(encoding="utf-8")
                self.assertRegex(ctl_text, rf"(?m)^undef {sentinel}(?:\.0+)?$", name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
