"""Exercise workflow STEP/SUCCESS/ERROR banners with small mock executables."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = ROOT / "map" / "tools" / "script_params"


class WorkflowMessageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="cmf-workflow-messages-")
        self.root = Path(self.temporary.name)
        self.map_root = self.root / "map" / "sample"
        self.script_dir = self.map_root / "script_params"
        self.code_dir = self.root / "map" / "tools" / "code"
        self.script_dir.mkdir(parents=True)
        self.code_dir.mkdir(parents=True)
        shell_functions_dir = self.root / "tools" / "shell_functions"
        shell_functions_dir.mkdir(parents=True)
        shutil.copy2(ROOT / "tools" / "cmf_shell_functions.sh", self.root / "tools" / "cmf_shell_functions.sh")
        for name in ("cmf_check_shell_error.sh", "cmf_select_hires_tag.sh",
                     "cmf_select_hires_for_conversion.sh"):
            shutil.copy2(ROOT / "tools" / "shell_functions" / name, shell_functions_dir / name)
        (self.map_root / "1min").mkdir()
        (self.map_root / "1min" / "location.txt").write_text("fixture\n", encoding="ascii")
        self.log = self.root / "calls.txt"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def install(self, script_name: str, executables: tuple[str, ...]) -> Path:
        script = self.script_dir / script_name
        shutil.copyfile(SCRIPT_DIR / script_name, script)
        script.chmod(0o755)
        for name in executables:
            (self.code_dir / f"{name}.py").write_text("# fixture\n", encoding="ascii")
        (self.code_dir / "convert_bifprm_csv_to_netcdf.py").write_text(
            "# fixture\n", encoding="ascii"
        )
        python = self.code_dir / "python3"
        python.write_text(
            "#!/bin/sh\n"
            "SCRIPT=${1##*/}; NAME=${SCRIPT%.py}; shift\n"
            "LOG_NAME=$NAME\n"
            "if [ \"$NAME\" = convert_bifprm_csv_to_netcdf ]; then LOG_NAME=python3; fi\n"
            "printf '%s %s\\n' \"$LOG_NAME\" \"$*\" >> \"$MOCK_LOG\"\n"
            "if [ \"${FAIL_MATCH:-}\" = \"$LOG_NAME\" ] || [ \"${FAIL_MATCH:-}\" = \"$LOG_NAME:${1:-}\" ]; then\n"
            "    exit \"${FAIL_STATUS:-23}\"\n"
            "fi\n"
            "case \"$NAME\" in\n"
            "    param_mpi_set_basin) : > ../bifbsn_mpi.nc ; : > ../bifcol_mpi.nc ;;\n"
            "    param_mpi_set_region) : > ../mpireg-$1.nc ;;\n"
            "    analysis_mpi_region_color) : > bsncol_mpi-${1#mpireg-}.nc ;;\n"
            "    convert_bifprm_csv_to_netcdf) : > \"$2\" ;;\n"
            "esac\n",
            encoding="ascii",
        )
        python.chmod(0o755)
        return script

    def run_script(
        self, script: Path, fail_match: str | None = None, cwd: Path | None = None,
        args: tuple[str, ...] = (),
    ) -> subprocess.CompletedProcess[str]:
        env = {
            **os.environ,
            "CMF_V50_ROOT": str(self.root),
            "MOCK_LOG": str(self.log),
            "PATH": f"{self.code_dir}:{os.environ['PATH']}",
        }
        if fail_match:
            env["FAIL_MATCH"] = fail_match
            env["FAIL_STATUS"] = "23"
        return subprocess.run(
            [str(script), *args], cwd=cwd or script.parent, env=env, text=True,
            input="\n", capture_output=True, check=False,
        )

    def calls(self) -> list[str]:
        return self.log.read_text(encoding="ascii").splitlines() if self.log.exists() else []

    def assert_success(
        self, result: subprocess.CompletedProcess[str], script_name: str, success_count: int = 1,
    ) -> None:
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count("[SUCCESS]"), success_count)
        self.assertIn(f"[SUCCESS] {script_name}", result.stdout)
        self.assertNotIn("[ERROR]", result.stdout + result.stderr)

    def assert_failure(
        self, result: subprocess.CompletedProcess[str], script_name: str,
        step: str, expected_status: int = 23, expected_success_count: int = 0,
    ) -> None:
        self.assertEqual(result.returncode, expected_status, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count("[SUCCESS]"), expected_success_count)
        self.assertIn(f"!!! ERROR: {script_name} FAILED !!!", result.stderr)
        self.assertIn(f"!!! Step: {step}", result.stderr)
        self.assertIn(f"!!! Exit status: {expected_status}", result.stderr)

    def test_s01_success_and_failures_stop_at_first_middle_and_final_program(self) -> None:
        executables = ("param_channel_calc_outclm", "param_channel_calc_rivwth", "param_channel_set_merit_width")
        script = self.install("s02-channel_params.sh", executables)
        result = self.run_script(script)
        self.assert_success(result, script.name)
        self.assertEqual([line.split()[0] for line in self.calls()], list(executables))
        self.assertEqual(result.stdout.count("[STEP "), 3)

        cases = (
            ("param_channel_calc_outclm", "Calculate mean river discharge from runoff and the input matrix", 1),
            ("param_channel_calc_rivwth", "Estimate channel width, depth, and roughness", 2),
            ("param_channel_set_merit_width", "Merge power-law widths with MERIT Hydro widths", 3),
        )
        for executable, step, expected_calls in cases:
            with self.subTest(executable=executable):
                self.log.unlink(missing_ok=True)
                result = self.run_script(script, executable)
                self.assert_failure(result, script.name, step)
                self.assertEqual(len(self.calls()), expected_calls)

    def test_s02_runs_generation_conversion_then_basin_merge_and_stops_on_each_failure(self) -> None:
        executables = ("param_bif_set_params", "param_bif_set_basin")
        script = self.install("s03-bifurcation.sh", executables)
        result = self.run_script(script)
        self.assert_success(result, script.name)
        self.assertEqual([line.split()[0] for line in self.calls()], [
            "param_bif_set_params", "python3", "param_bif_set_basin",
        ])

        for fail_match, step, expected, successes in (
            ("param_bif_set_params", "Generate the finalized bifurcation CSV", 1, 0),
            ("python3", "Convert the finalized bifurcation CSV to NetCDF", 2, 0),
            ("param_bif_set_basin", "Merge basins linked by bifurcation pathways", 3, 0),
        ):
            with self.subTest(fail_match=fail_match):
                self.log.unlink(missing_ok=True)
                result = self.run_script(script, fail_match)
                self.assert_failure(result, script.name, step, expected_success_count=successes)
                self.assertEqual(len(self.calls()), expected)

    def test_s02_forwards_configured_check_map_option(self) -> None:
        script = self.install("s03-bifurcation.sh", (
            "param_bif_set_params", "param_bif_set_basin",
        ))
        source = script.read_text(encoding="utf-8")
        source = source.replace('"$RIVHGT" "$BIFPRM_CSV" "$BIFLAYER" "$DIMINFO" --map-dir ..',
                                '"$RIVHGT" "$BIFPRM_CSV" "$BIFLAYER" "$DIMINFO" --check-map --map-dir ..')
        source = source.replace('"$CODE_DIR/param_bif_set_basin.py" --map-dir ..',
                                '"$CODE_DIR/param_bif_set_basin.py" --check-map --map-dir ..')
        script.write_text(source, encoding="utf-8")
        result = self.run_script(script)
        self.assert_success(result, script.name)
        calls = [line.split() for line in self.calls()]
        self.assertIn("--check-map", calls[0])
        self.assertNotIn("--check-map", calls[1])
        self.assertIn("--check-map", calls[2])

    def test_s03_success_and_program_failure(self) -> None:
        script = self.install("s01-inpmat_default.sh", ("param_inpmat_generate",))
        result = self.run_script(script)
        self.assert_success(result, script.name)
        self.assertIn("[STEP 1/1]", result.stdout)
        self.log.unlink()

        result = self.run_script(script, "param_inpmat_generate:1min")
        self.assert_failure(result, script.name, "Map river cells to the configured runoff grid")
        self.assertEqual(len(self.calls()), 1)

    def test_regional_script_success_and_bifurcation_failure(self) -> None:
        regional_dir = self.map_root / "script_region"
        regional_dir.mkdir()
        global_map = self.root / "map" / "glb_15min"
        (global_map / "1min").mkdir(parents=True)
        (global_map / "1min" / "location.txt").write_text("fixture\n", encoding="ascii")
        script = regional_dir / "s01-regional_map.sh"
        shutil.copyfile(ROOT / "map" / "tools" / "script_region" / script.name, script)
        script.chmod(0o755)
        executables = (
            "region_cut_domain", "region_cut_bifway", "region_set_map",
            "region_combine_hires", "region_default_inpmat",
        )
        for name in executables:
            path = self.code_dir / name
            path.write_text(
                "#!/bin/sh\n"
                "NAME=${0##*/}\n"
                "printf '%s %s\\n' \"$NAME\" \"$*\" >> \"$MOCK_LOG\"\n"
                "if [ \"${FAIL_MATCH:-}\" = \"$NAME\" ]; then exit \"${FAIL_STATUS:-23}\"; fi\n",
                encoding="ascii",
            )
            path.chmod(0o755)
        python = self.code_dir / "python3"
        python.write_text(
            "#!/bin/sh\n"
            "SCRIPT=${1##*/}; NAME=${SCRIPT%.py}; shift\n"
            "printf '%s %s\\n' \"$NAME\" \"$*\" >> \"$MOCK_LOG\"\n"
            "if [ \"${FAIL_MATCH:-}\" = \"$NAME\" ]; then exit \"${FAIL_STATUS:-23}\"; fi\n",
            encoding="ascii",
        )
        python.chmod(0o755)

        result = self.run_script(script, cwd=regional_dir)
        self.assert_success(result, script.name)
        self.assertEqual([line.split()[0] for line in self.calls()], list(executables))
        self.assertEqual(result.stdout.count("[STEP "), 6)
        self.log.unlink()

        result = self.run_script(script, "region_cut_bifway", cwd=regional_dir)
        self.assert_failure(
            result, script.name, "Retain bifurcation pathways inside the regional domain",
        )
        self.assertEqual(
            [line.split()[0] for line in self.calls()],
            ["region_cut_domain", "region_cut_bifway"],
        )

    def test_x01_success_cleans_visible_intermediate_and_reports_connectivity_failure(self) -> None:
        executables = (
            "param_mpi_set_basin", "param_mpi_set_region", "analysis_mpi_dropped_bifurcation",
        )
        script = self.install("x01-mpi_map_setup.sh", executables)
        result = self.run_script(script)
        self.assert_success(result, script.name)
        self.assertIn("[STEP 5/5]", result.stdout)
        calls = [line.split() for line in self.calls()]
        self.assertEqual([call[0] for call in calls], [
            "param_mpi_set_basin", "param_mpi_set_region", "param_mpi_set_region",
            "param_mpi_set_region", "analysis_mpi_dropped_bifurcation",
        ])
        self.assertEqual(calls[1:4], [
            ["param_mpi_set_region", "4", "--map-dir", ".."],
            ["param_mpi_set_region", "8", "--map-dir", ".."],
            ["param_mpi_set_region", "16", "--map-dir", ".."],
        ])
        self.assertEqual(calls[4], ["analysis_mpi_dropped_bifurcation", "../mpireg-16.nc", "--map-dir", ".."])
        self.assertFalse((self.map_root / "mpireg.bin").exists())
        self.assertTrue((self.map_root / "bifcol_mpi.nc").exists())
        self.assertFalse(list(self.map_root.glob("bsncol_mpi-*.bin")))
        self.assertFalse((self.map_root / "bifbsn_mpi.nc").exists())
        self.log.unlink()

        result = self.run_script(script, "analysis_mpi_dropped_bifurcation:../mpireg-16.nc")
        self.assert_failure(
            result, script.name,
            "Check dropped bifurcation pathways for the largest requested MPI count (16)",
        )
        self.assertFalse((self.map_root / "bifbsn_mpi.nc").exists())
        self.assertEqual(self.calls()[-1].split()[0], "analysis_mpi_dropped_bifurcation")

    def test_x01_partition_loop_failure_stops_later_counts_and_cleans_intermediate(self) -> None:
        script = self.install("x01-mpi_map_setup.sh", (
            "param_mpi_set_basin", "param_mpi_set_region", "analysis_mpi_dropped_bifurcation",
        ))
        result = self.run_script(script, "param_mpi_set_region:8")
        self.assert_failure(result, script.name, "Assign basins to 8 MPI regions")
        self.assertEqual(self.calls()[-1].split(), ["param_mpi_set_region", "8", "--map-dir", ".."])
        self.assertNotIn("param_mpi_set_region 16", self.calls())
        self.assertNotIn("analysis_mpi_dropped_bifurcation", "\n".join(self.calls()))
        self.assertFalse((self.map_root / "bifbsn_mpi.nc").exists())

    def test_x01_forwards_check_map_only_to_basin_aggregation(self) -> None:
        script = self.install("x01-mpi_map_setup.sh", (
            "param_mpi_set_basin", "param_mpi_set_region", "analysis_mpi_dropped_bifurcation",
        ))
        source = script.read_text(encoding="utf-8")
        source = source.replace('--mode "$BASIN_MERGE_MODE" \\\n    --map-dir ..', '--mode "$BASIN_MERGE_MODE" \\\n    --check-map --map-dir ..')
        script.write_text(source, encoding="utf-8")
        result = self.run_script(script)
        self.assert_success(result, script.name)
        calls = self.calls()
        self.assertEqual(calls[0].split(), ["param_mpi_set_basin", "--mode", "standard", "--check-map", "--map-dir", ".."])
        self.assertEqual(calls[-1].split(), ["analysis_mpi_dropped_bifurcation", "../mpireg-16.nc", "--map-dir", ".."])
        self.assertNotIn("analysis_mpi_region_color", "\n".join(calls))
        self.assertTrue(all("check_map" not in call for call in calls[1:]))

    def test_x01_uses_largest_unsorted_count_once_for_diagnostic(self) -> None:
        script = self.install("x01-mpi_map_setup.sh", (
            "param_mpi_set_basin", "param_mpi_set_region", "analysis_mpi_dropped_bifurcation",
        ))
        source = script.read_text(encoding="utf-8").replace('MPI_COUNTS="4 8 16"', 'MPI_COUNTS="16 4 8"')
        script.write_text(source, encoding="utf-8")
        result = self.run_script(script)
        self.assert_success(result, script.name)
        calls = [line.split() for line in self.calls()]
        self.assertEqual([call[1] for call in calls[1:4]], ["16", "4", "8"])
        diagnostics = [call for call in calls if call[0] == "analysis_mpi_dropped_bifurcation"]
        self.assertEqual(diagnostics, [["analysis_mpi_dropped_bifurcation", "../mpireg-16.nc", "--map-dir", ".."]])

    def test_x01_empty_list_stops_before_processing(self) -> None:
        script = self.install("x01-mpi_map_setup.sh", (
            "param_mpi_set_basin", "param_mpi_set_region", "analysis_mpi_dropped_bifurcation",
        ))
        source = script.read_text(encoding="utf-8").replace('MPI_COUNTS="4 8 16"', 'MPI_COUNTS=""')
        script.write_text(source, encoding="utf-8")
        result = self.run_script(script)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("MPI_COUNTS must not be empty", result.stderr)
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
