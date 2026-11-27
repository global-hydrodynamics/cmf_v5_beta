"""Legacy/v5 regression and workflow checks for river-network analysis tools.

All generated rasters are written to temporary map copies. These tests compare
against the preserved v4 programs; they do not claim scientific validation.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

import netCDF4
import numpy as np

from map.tools.code.generate_ctl import generate_directory
from map.tools.code.mod_map_io import Grid

ROOT = Path(__file__).resolve().parents[3]
SAMPLE = ROOT / "map" / "mekong_15min"
CODE = ROOT / "map" / "tools" / "code" / "legacy_fortran"
LEGACY = ROOT / "map" / "src" / "src_param"
PARAM_SCRIPTS = ROOT / "map" / "tools" / "script_params"
MAP_FILES = (
    "params.txt", "nextxy.bin", "basin.bin", "upgrid.bin", "uparea.bin",
    "ctmare.bin", "elevtn.bin", "lonlat.bin", "GRDC_alloc.txt",
)
MAP_NETCDF_FILES = (
    "nextxy.nc", "basin.nc", "upgrid.nc", "uparea.nc", "ctmare.nc", "elevtn.nc", "lonlat.nc",
)


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, CMF_V50_ROOT=str(ROOT), PATH=f"{Path(sys.executable).parent}:{os.environ['PATH']}")
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True, check=False)


class AnalysisMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        compiler_name = os.environ.get("FC", "gfortran").split()[0]
        cls.compiler = shutil.which(compiler_name)
        if cls.compiler is None:
            raise unittest.SkipTest(f"Fortran compiler not available: {compiler_name}")
        cls.tmp = tempfile.TemporaryDirectory(prefix="cmf-analysis-build-")
        cls.root = Path(cls.tmp.name)
        cls.v5_dir = cls.root / "v5"
        cls.legacy_dir = cls.root / "legacy"
        cls.debug_dir = cls.root / "debug"
        for directory in (cls.v5_dir, cls.legacy_dir, cls.debug_dir):
            directory.mkdir()
        flags = ["-O2", "-ffree-line-length-none", "-fimplicit-none"]
        debug_flags = [*flags, "-fcheck=bounds"]
        programs = (
            ("get_rivinfo", "analysis_river_point_info"),
            ("get_upbasin", "analysis_upbasin"),
            ("get_subbasin", "analysis_subbasin"),
            ("get_vecmap", "analysis_river_node_latlon"),
        )
        for legacy_stem, v5_stem in programs:
            for source_dir, out_dir, compile_flags in (
                (LEGACY, cls.legacy_dir, flags),
                (CODE, cls.v5_dir, flags),
                (CODE, cls.debug_dir, debug_flags),
            ):
                stem = legacy_stem if source_dir == LEGACY else v5_stem
                result = run(
                    [cls.compiler, *compile_flags, str(source_dir / f"{stem}.F90"),
                     "-o", str(out_dir / stem)], ROOT,
                )
                if result.returncode:
                    cls.tmp.cleanup()
                    raise RuntimeError(f"Could not compile {stem}:\n{result.stdout}{result.stderr}")

    @classmethod
    def tearDownClass(cls) -> None:
        if hasattr(cls, "tmp"):
            cls.tmp.cleanup()

    def make_map(self, label: str) -> tuple[Path, Path]:
        base = self.root / label
        map_dir = base / "map" / "mekong_15min"
        script_params = map_dir / "script_params"
        script_params.mkdir(parents=True)
        for name in MAP_FILES:
            source = SAMPLE / "binary" / name if name.endswith(".bin") else SAMPLE / name
            shutil.copy2(source, map_dir / name)
        hires = map_dir / "1min"
        hires.mkdir()
        for name in ("location.txt", "1min.catmxy.bin"):
            shutil.copy2(SAMPLE / "binary" / "1min" / name, hires / name)
        return map_dir, script_params

    def test_legacy_and_v5_binary_outputs_match_and_ctl_generation_works(self) -> None:
        v5_map, v5_params = self.make_map("parity")
        legacy_map = self.root / "parity" / "map" / "legacy"
        legacy_params = legacy_map / "src_param"
        legacy_params.mkdir(parents=True)
        for name in MAP_FILES[:-1]:
            shutil.copy2(v5_map / name, legacy_map / name)
        legacy_hires = legacy_map / "1min"
        legacy_hires.mkdir()
        for name in ("location.txt", "1min.catmxy.bin"):
            shutil.copy2(v5_map / "1min" / name, legacy_hires / name)

        for label, executable_dir, workdir in (
            ("v5", self.v5_dir, v5_params), ("legacy", self.legacy_dir, legacy_params),
        ):
            rivinfo = "analysis_river_point_info" if label == "v5" else "get_rivinfo"
            result = run([str(executable_dir / rivinfo), "xy", "62", "93"], workdir)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            if label == "v5":
                v5_river_info = result.stdout
            else:
                self.assertEqual(result.stdout, v5_river_info)
            result = run(
                [str(executable_dir / rivinfo), "latlon", "11.579", "104.946"],
                workdir,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            if label == "v5":
                v5_geo_info = result.stdout
            else:
                self.assertEqual(result.stdout, v5_geo_info)

            upbasin = "analysis_upbasin" if label == "v5" else "get_upbasin"
            upbasin_args = [str(executable_dir / upbasin), "62", "93"]
            if label == "v5":
                upbasin_args.append("../upbasin.bin")
            result = run(upbasin_args, workdir)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            if label == "v5":
                v5_upbasin = (v5_map / "upbasin.bin").read_bytes()
            else:
                self.assertEqual((legacy_map / "upbasin.bin").read_bytes(), v5_upbasin)

            subbasin = "analysis_subbasin" if label == "v5" else "get_subbasin"
            subbasin_args = [str(executable_dir / subbasin), "50000"]
            if label == "v5":
                subbasin_args.extend(("../subbsn.bin", "../subcol.bin"))
            result = run(subbasin_args, workdir)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            if label == "v5":
                v5_subbsn = (v5_map / "subbsn.bin").read_bytes()
                v5_subcol = (v5_map / "subcol.bin").read_bytes()
            else:
                legacy_subbsn = (legacy_map / "subbsn.bin").read_bytes()
                legacy_subcol = (legacy_map / "subcol.bin").read_bytes()
                old_values = struct.unpack("<" + "i" * (80 * 120), legacy_subbsn)
                new_values = struct.unpack("<" + "i" * (80 * 120), v5_subbsn)
                old_colors = struct.unpack("<" + "i" * (80 * 120), legacy_subcol)
                new_colors = struct.unpack("<" + "i" * (80 * 120), v5_subcol)
                nextx_values = struct.unpack("<" + "i" * (80 * 120),
                                             (v5_map / "nextxy.bin").read_bytes()[:80 * 120 * 4])
                for old, new, downstream_x, old_color, new_color in zip(
                        old_values, new_values, nextx_values, old_colors, new_colors):
                    if old > 0:
                        self.assertEqual(new, old)
                    elif downstream_x == -9999:
                        self.assertEqual(new, -9999)
                    else:
                        self.assertEqual(new, 0)
                    if new > 0:
                        self.assertEqual(new_color, old_color)
                        self.assertTrue(1 <= new_color <= 10)
                    elif new == 0:
                        self.assertEqual(old_color, -9999)
                        self.assertEqual(new_color, 0)
                    else:
                        self.assertEqual(new_color, -9999)

        legacy_analysis = legacy_map / "script_analysis"
        legacy_analysis.mkdir()
        for label, executable, workdir in (
            ("v5", self.v5_dir / "analysis_river_node_latlon", v5_map / "script_params"),
            ("legacy", self.legacy_dir / "get_vecmap", legacy_analysis),
        ):
            result = run([str(executable), "90", "110", "5", "35"], workdir)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            if label == "v5":
                v5_vector_text = result.stdout
            else:
                self.assertEqual(result.stdout, v5_vector_text)
                self.assertIn("ori-lat", result.stdout.splitlines()[0])

        # The legacy threshold of 30,000 km2 aborts after basin-color setup on
        # this compiler; verify the sample threshold through the v5-only wrapper.
        result = run(
            [str(self.v5_dir / "analysis_subbasin"), "30000",
             str(v5_map / "subbsn-sample.bin"), str(v5_map / "subcol.bin")],
            v5_params,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        v5_subbsn_30000 = (v5_map / "subbsn-sample.bin").read_bytes()

        record_bytes = 80 * 120 * 4
        self.assertEqual(len(v5_upbasin), record_bytes)
        self.assertEqual(len(v5_subbsn), record_bytes)
        self.assertEqual(len(v5_subcol), record_bytes)
        upstream_values = struct.unpack("<" + "i" * (80 * 120), v5_upbasin)
        subbasin_values = struct.unpack("<" + "i" * (80 * 120), v5_subbsn)
        color_values = struct.unpack("<" + "i" * (80 * 120), v5_subcol)
        self.assertTrue({-9999, 0, 1}.issubset(set(upstream_values)))
        self.assertIn(-9999, subbasin_values)
        self.assertIn(0, subbasin_values)
        self.assertTrue(any(value > 0 for value in subbasin_values))
        self.assertIn(-9999, color_values)
        self.assertIn(0, color_values)
        for subbasin, color in zip(subbasin_values, color_values):
            if subbasin > 0:
                self.assertTrue(1 <= color <= 10)
            else:
                self.assertEqual(color, subbasin)
        ctl_dir = self.root / "ctl"
        ctl_dir.mkdir()
        shutil.copy2(v5_map / "subcol.bin", v5_map / "subcol-sample.bin")
        for name in ("params.txt", "subbsn-sample.bin", "subcol-sample.bin"):
            # CTL auto-discovery registers standard names; samples are variants.
            standard = name.replace("subbsn-sample", "subbsn").replace("subcol-sample", "subcol")
            shutil.copy2(v5_map / name, ctl_dir / standard)
        result = generate_directory(ctl_dir, ROOT / "variable_table" / "map_variables.csv")
        self.assertEqual(result.generated, 2, result)
        for stem, variable in (("subbsn", "subbsn"), ("subcol", "subcol")):
            ctl = (ctl_dir / f"{stem}.ctl").read_text(encoding="utf-8")
            self.assertIn(f"{variable} 1", ctl)
            self.assertIn("undef", ctl)

    def test_bounds_checked_subbasin_and_custom_outputs_do_not_replace_standard(self) -> None:
        map_dir, script_params = self.make_map("bounds")
        standard_subbsn = b"prior-subbasin"
        standard_subcol = b"prior-colors"
        standard_upbasin = b"prior-upstream-mask"
        (map_dir / "subbsn.bin").write_bytes(standard_subbsn)
        (map_dir / "subcol.bin").write_bytes(standard_subcol)
        (map_dir / "upbasin.bin").write_bytes(standard_upbasin)
        result = run([str(self.debug_dir / "analysis_subbasin"), "30000"], script_params)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((map_dir / "subbsn.bin").read_bytes(), standard_subbsn)
        self.assertEqual((map_dir / "subcol.bin").read_bytes(), standard_subcol)
        self.assertEqual((map_dir / "analysis_subbsn_30000.bin").stat().st_size, 80 * 120 * 4)
        self.assertEqual((map_dir / "analysis_subcol_30000.bin").stat().st_size, 80 * 120 * 4)
        result = run([str(self.debug_dir / "analysis_upbasin"), "62", "93"], script_params)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((map_dir / "upbasin.bin").read_bytes(), standard_upbasin)
        self.assertEqual((map_dir / "analysis_upbasin_62_93.bin").stat().st_size, 80 * 120 * 4)
        result = run([str(self.debug_dir / "analysis_subbasin"), "30000", "explore.bin", "explore-col.bin"], script_params)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((map_dir / "subbsn.bin").read_bytes(), standard_subbsn)
        self.assertEqual((map_dir / "subcol.bin").read_bytes(), standard_subcol)
        self.assertEqual((script_params / "explore.bin").stat().st_size, 80 * 120 * 4)
        self.assertEqual((script_params / "explore-col.bin").stat().st_size, 80 * 120 * 4)

    def test_parameter_analysis_examples_use_temporary_map(self) -> None:
        map_dir, params = self.make_map("scripts")
        for filename in MAP_NETCDF_FILES:
            shutil.copy2(SAMPLE / filename, map_dir / filename)
        for name in (
            "a02-sample_subbasin.sh", "get_river_point_info.sh", "calc_upbasin.sh",
            "a01-sample_get_river_point_info.sh", "a03-sample_calc_upbasin.sh",
            "a04-advanced_calc_upbasin.sh",
        ):
            shutil.copy2(PARAM_SCRIPTS / name, params / name)
            (params / name).chmod(0o755)
            syntax = run(["sh", "-n", str(params / name)], self.root)
            self.assertEqual(syntax.returncode, 0, syntax.stderr)

        result = run([str(params / "a02-sample_subbasin.sh")], params)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for filename, variable_name in (("subbsn-sample.nc", "subbsn"), ("subcol-sample.nc", "subcol")):
            with netCDF4.Dataset(map_dir / filename) as dataset:
                self.assertIn(variable_name, dataset.variables)
                self.assertNotIn(f"{variable_name}-sample", dataset.variables)
                self.assertEqual(dataset[variable_name].shape, (120, 80))
                self.assertEqual(np.dtype(dataset[variable_name].dtype), np.dtype("int32"))

        result = run([str(params / "a04-advanced_calc_upbasin.sh")], self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("GRDC station ID: 2569002", result.stdout)
        self.assertIn("IX=62, IY=93", result.stdout)
        self.assertIn("River-point information", result.stdout)
        self.assertFalse((map_dir / "grdc_station_selection.txt").exists())
        self.assertFalse((map_dir / "grdc_river_info.txt").exists())
        station_mask = map_dir / "upbasin-2569002.nc"
        self.assertTrue(station_mask.is_file())
        with netCDF4.Dataset(station_mask) as dataset:
            variable = dataset.variables["upbasin"]
            variable.set_auto_maskandscale(False)
            mask_values = np.asarray(variable[:])
            self.assertEqual(mask_values.shape, (120, 80))
            self.assertEqual(np.dtype(variable.dtype), np.dtype("int32"))
            self.assertTrue({-9999, 0, 1}.issubset(set(np.unique(mask_values))))

        result = run([str(params / "get_river_point_info.sh"), "xy", "62", "93"], params)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Fortran IX,IY: 62 93", result.stdout)
        custom_mask = map_dir / "upbasin-custom.nc"
        result = run([str(params / "calc_upbasin.sh"), "xy", "62", "93", "../upbasin-custom.nc"], params)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(custom_mask.is_file())

        result = run([str(params / "a03-sample_calc_upbasin.sh")], params)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Mekong sample map", result.stdout)
        sample_mask = params / "upbasin-sample.nc"
        self.assertTrue(sample_mask.is_file())
        with netCDF4.Dataset(sample_mask) as dataset:
            self.assertIn("upbasin", dataset.variables)
        result = run([str(params / "calc_upbasin.sh"), "latlon", "11.5", "104.9"], params)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage:", result.stderr)

    def test_river_point_cli_netcdf_modes_match_binary_reference_and_fallback(self) -> None:
        map_dir, _ = self.make_map("river-point-netcdf")
        binary_dir = map_dir / "binary"
        binary_dir.mkdir()
        for name in MAP_NETCDF_FILES:
            shutil.copy2(SAMPLE / name, map_dir / name)
            shutil.copy2(SAMPLE / "binary" / name.replace(".nc", ".bin"),
                         binary_dir / name.replace(".nc", ".bin"))

        hires = map_dir / "1min"
        shutil.copy2(SAMPLE / "1min" / "1min.catmxy.nc", hires / "1min.catmxy.nc")
        binary_hires = binary_dir / "1min"
        binary_hires.mkdir()
        shutil.copy2(SAMPLE / "1min" / "location.txt", hires / "location.txt")
        shutil.copy2(SAMPLE / "binary" / "1min" / "location.txt", binary_hires / "location.txt")
        shutil.copy2(SAMPLE / "binary" / "1min" / "1min.catmxy.bin", binary_hires / "1min.catmxy.bin")

        analysis = map_dir / "script_params"
        point_info = ROOT / "map" / "tools" / "code" / "analysis_river_point_info.py"
        for query in (("xy", "62", "93"), ("latlon", "11.579", "104.946")):
            netcdf = run([sys.executable, str(point_info), *query], analysis)
            binary = run([sys.executable, str(point_info), "--map-format", "binary", *query], analysis)
            self.assertEqual(netcdf.returncode, 0, netcdf.stdout + netcdf.stderr)
            self.assertEqual(binary.returncode, 0, binary.stdout + binary.stderr)
            self.assertEqual(netcdf.stdout, binary.stdout)

        latitude, longitude = np.float32(11.579), np.float32(104.946)
        location_fields = (hires / "location.txt").read_text().splitlines()[2].split()
        nx, ny, size = int(location_fields[6]), int(location_fields[7]), np.float32(location_fields[8])
        grid = Grid.from_file(map_dir / "params.txt")
        x = int(np.float32((longitude - grid.west) / size))
        y = int(np.float32((grid.north - latitude) / size))
        with netCDF4.Dataset(hires / "1min.catmxy.nc") as dataset:
            dataset["catmxx"].set_auto_maskandscale(False)
            dataset["catmyy"].set_auto_maskandscale(False)
            ix, iy = int(dataset["catmxx"][y, x]), int(dataset["catmyy"][y, x])
        self.assertTrue(0 <= x < nx and 0 <= y < ny)
        self.assertRegex(netcdf.stdout, rf"Fortran IX,IY: {ix} {iy}")

        command = analysis / "get_river_point_info.sh"
        shutil.copy2(PARAM_SCRIPTS / command.name, command)
        sample = analysis / "a01-sample_get_river_point_info.sh"
        shutil.copy2(PARAM_SCRIPTS / sample.name, sample)
        python_bin = self.root / "river-point-python"
        python_bin.mkdir()
        python3 = python_bin / "python3"
        python3.write_text(f"#!/bin/sh\nexec {sys.executable} \"$@\"\n", encoding="utf-8")
        python3.chmod(0o755)
        env = dict(os.environ, CMF_V50_ROOT=str(ROOT), PATH=f"{python_bin}:{os.environ['PATH']}")
        before = set(analysis.iterdir())
        result = subprocess.run([str(command), "xy", "62", "93"], cwd=analysis, env=env,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Fortran IX,IY: 62 93", result.stdout)
        result = subprocess.run([str(sample)], cwd=analysis, env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count("Point Information"), 2)
        self.assertEqual(set(analysis.iterdir()), before)

        fallback_map, _ = self.make_map("river-point-fallback")
        fallback_binary = fallback_map / "binary"
        fallback_binary.mkdir()
        for name in MAP_NETCDF_FILES:
            shutil.copy2(SAMPLE / name, fallback_map / name)
            shutil.copy2(SAMPLE / "binary" / name.replace(".nc", ".bin"),
                         fallback_binary / name.replace(".nc", ".bin"))
        (fallback_map / "1min" / "location.txt").unlink()
        (fallback_map / "1min" / "1min.catmxy.bin").unlink()
        fallback_analysis = fallback_map / "script_params"
        netcdf = run([sys.executable, str(point_info), "latlon", "11.579", "104.946"], fallback_analysis)
        binary = run([sys.executable, str(point_info), "--map-format", "binary",
                      "latlon", "11.579", "104.946"], fallback_analysis)
        self.assertEqual(netcdf.returncode, 0, netcdf.stdout + netcdf.stderr)
        self.assertEqual(binary.returncode, 0, binary.stdout + binary.stderr)
        self.assertEqual(netcdf.stdout, binary.stdout)

    def test_mekong_sample_subbasin_wrapper_uses_stable_output_names(self) -> None:
        map_dir, params = self.make_map("sample-script")
        script = params / "a02-sample_subbasin.sh"
        shutil.copy2(SAMPLE / "script_params" / "a02-sample_subbasin.sh", script)
        script.chmod(0o755)
        for filename in MAP_NETCDF_FILES:
            shutil.copy2(SAMPLE / filename, map_dir / filename)
        result = run([str(script)], params)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for filename, variable_name in (("subbsn-sample.nc", "subbsn"), ("subcol-sample.nc", "subcol")):
            with netCDF4.Dataset(map_dir / filename) as dataset:
                self.assertIn(variable_name, dataset.variables)
                self.assertNotIn(f"{variable_name}-sample", dataset.variables)
                self.assertEqual(dataset[variable_name].shape, (120, 80))
        script.write_text(script.read_text().replace("AREA_SMLBSN=5000", 'AREA_SMLBSN=""'))
        result = run([str(script)], params)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with netCDF4.Dataset(map_dir / "subbsn-sample.nc") as dataset:
            dataset.set_auto_maskandscale(False)
            digest = hashlib.sha256(np.asarray(dataset["subbsn"][:], dtype="<i4").tobytes()).hexdigest()
        self.assertEqual(digest, "4c5e85be796a3957fe67d3883ec8ad7cafd15689d1fc81ccf87ef4da0e4a7b1e")

    def test_two_stage_subbasins_preserve_stage1_and_connected_ids(self) -> None:
        # Detect a full smaller-threshold rerun that would destroy Stage 1 IDs.
        map_dir, params = self.make_map("two-stage")
        executable = str(self.debug_dir / "analysis_subbasin")
        for arguments in (
            ["30000", "first.bin", "first-col.bin"],
            ["30000", "5000", "second.bin", "second-col.bin"],
        ):
            result = run([executable, *arguments], params)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        first_bytes = (params / "first.bin").read_bytes()
        # Original tracked 30,000 km2 sample at d4d5b0e2, before two-stage support.
        self.assertEqual(hashlib.sha256(first_bytes).hexdigest(),
                         "4c5e85be796a3957fe67d3883ec8ad7cafd15689d1fc81ccf87ef4da0e4a7b1e")
        first = struct.unpack("<9600i", first_bytes)
        second = struct.unpack("<9600i", (params / "second.bin").read_bytes())
        colors = struct.unpack("<9600i", (params / "second-col.bin").read_bytes())
        nextxy = struct.unpack("<19200i", (map_dir / "nextxy.bin").read_bytes())
        self.assertEqual(max(first), 64)
        self.assertEqual(max(second), 113)
        self.assertEqual(first.count(0), 1274)
        self.assertEqual(second.count(0), 686)
        groups: dict[int, set[int]] = {}
        for index, (old, new, color) in enumerate(zip(first, second, colors)):
            if old != 0:
                self.assertEqual(new, old)
            elif new > 0:
                self.assertGreater(new, max(first))
            self.assertTrue(new >= 0 or new == -9999)
            if new > 0:
                self.assertTrue(1 <= color <= 10)
                groups.setdefault(new, set()).add(index)
            elif new == 0:
                self.assertEqual(color, 0)
            else:
                self.assertEqual(new, -9999)
                self.assertEqual(color, -9999)
        for cells in groups.values():
            # Each ID is one connected directed tree, never reused in another segment.
            edges = 0
            neighbors: dict[int, list[int]] = {index: [] for index in cells}
            for index in cells:
                x, y = nextxy[index], nextxy[9600 + index]
                downstream = (y - 1) * 80 + x - 1
                if x > 0 and y > 0 and downstream in cells:
                    edges += 1
                    neighbors[index].append(downstream)
                    neighbors[downstream].append(index)
            reached: set[int] = set()
            pending = [next(iter(cells))]
            while pending:
                index = pending.pop()
                if index not in reached:
                    reached.add(index)
                    pending.extend(neighbors[index])
            self.assertEqual(reached, cells)
            self.assertEqual(edges, len(cells) - 1)
            self.assertEqual(len({colors[index] for index in cells}), 1)

        # The two-argument default-path form must match the explicit-path form.
        result = run([executable, "30000", "5000"], params)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((map_dir / "analysis_subbsn_30000_5000.bin").read_bytes(),
                         (params / "second.bin").read_bytes())

    def test_subbasin_rejects_invalid_thresholds(self) -> None:
        _, params = self.make_map("invalid-thresholds")
        for arguments in (["0"], ["-1"], ["NaN"], ["invalid"],
                          ["30000", "30000"], ["30000", "40000"],
                          ["30000", "0"], ["30000", "NaN"], ["30000", "bad"]):
            with self.subTest(arguments=arguments):
                result = run([str(self.debug_dir / "analysis_subbasin"), *arguments], params)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ERROR:", result.stdout)

    def test_direct_cli_runs_from_map_local_script_params(self) -> None:
        map_dir, params = self.make_map("portable-cli")
        binary_dir = map_dir / "binary"
        binary_dir.mkdir()
        for name in MAP_FILES:
            if name.endswith(".bin"):
                shutil.copy2(SAMPLE / "binary" / name, binary_dir / name)
        commands = (
            ("analysis_river_point_info.py", "xy", "62", "93"),
            ("analysis_upbasin.py", "62", "93"),
            ("analysis_subbasin.py", "50000"),
            ("analysis_river_node_latlon.py", "90", "110", "5", "35"),
        )
        outputs = []
        for command in commands:
            result = run([sys.executable, str(ROOT / "map" / "tools" / "code" / command[0]),
                          "--map-format", "binary", *command[1:]], params)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            outputs.append(result.stdout)
        self.assertIn("Point Information", outputs[0])
        self.assertIn("Upstream Area", outputs[1])
        self.assertEqual(outputs[2], "")  # Raster products are written to the map root.
        self.assertIn("ori-lat", outputs[3].splitlines()[0])
        self.assertTrue((binary_dir / "analysis_upbasin_62_93.bin").is_file())
        self.assertTrue((binary_dir / "analysis_subbsn_50000.bin").is_file())
        self.assertTrue((binary_dir / "analysis_subcol_50000.bin").is_file())
        self.assertFalse((map_dir / "upbasin.nc").exists())
        self.assertFalse((map_dir / "subbsn.nc").exists())
        self.assertFalse((map_dir / "subcol.nc").exists())

    def test_missing_or_headerless_grdc_allocation_fails_clearly(self) -> None:
        map_dir, params = self.make_map("invalid-grdc")
        script = params / "a04-advanced_calc_upbasin.sh"
        shutil.copy2(PARAM_SCRIPTS / "a04-advanced_calc_upbasin.sh", script)
        script.chmod(0o755)
        (map_dir / "GRDC_alloc.txt").write_text("ID lat lon\n", encoding="ascii")
        result = run([str(script)], self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("contains no valid allocated station", result.stderr)

    def test_grdc_selection_filters_invalid_rows_and_keeps_first_tie(self) -> None:
        map_dir, params = self.make_map("grdc-tie")
        script = params / "a04-advanced_calc_upbasin.sh"
        shutil.copy2(PARAM_SCRIPTS / "a04-advanced_calc_upbasin.sh", script)
        script.chmod(0o755)
        for name in ("get_river_point_info.sh", "calc_upbasin.sh"):
            wrapper = params / name
            wrapper.write_text("#!/bin/sh\necho stub\n", encoding="ascii")
            wrapper.chmod(0o755)
        header = "ID lat lon area_Input area_CaMa error diff Type ix1 iy1 ix2 iy2 area1 area2\n"
        rows = (
            "unallocated 10 100 900 900 0 0 -9 62 93 -999 -999 -999 -999\n"
            "bad-area 10 100 -1 200 0 0 1 62 93 -999 -999 -999 -999\n"
            "bad-cell 10 100 200 300 0 0 1 999 93 -999 -999 -999 -999\n"
            "first-tie 11 101 120 500 0 0 1 62 93 -999 -999 120 -999\n"
            "second-tie 12 102 130 500 0 0 1 62 93 -999 -999 130 -999\n"
        )
        (map_dir / "GRDC_alloc.txt").write_text(header + rows, encoding="ascii")
        result = run([str(script)], self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("GRDC station ID: first-tie", result.stdout)
        self.assertNotIn("second-tie", result.stdout)
        self.assertIn("IX=62, IY=93", result.stdout)
        self.assertIn("River-point information", result.stdout)
        self.assertFalse((map_dir / "grdc_station_selection.txt").exists())
        self.assertFalse((map_dir / "grdc_river_info.txt").exists())

    def test_missing_grdc_allocation_fails_with_manual_next_step(self) -> None:
        map_dir, params = self.make_map("missing-grdc")
        (map_dir / "GRDC_alloc.txt").unlink()
        script = params / "a04-advanced_calc_upbasin.sh"
        shutil.copy2(PARAM_SCRIPTS / "a04-advanced_calc_upbasin.sh", script)
        script.chmod(0o755)
        result = run([str(script)], self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Run t01-alloc_flow_gauge.sh", result.stderr)


if __name__ == "__main__":
    unittest.main()
