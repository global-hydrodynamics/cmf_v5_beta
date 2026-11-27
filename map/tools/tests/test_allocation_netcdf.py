"""NetCDF and explicit legacy-Binary checks for allocation readers."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from netCDF4 import Dataset

TOOLS = Path(__file__).resolve().parents[1]
REPO = TOOLS.parents[1]
SAMPLE = REPO / "map/mekong_15min"
DATA = REPO / "map/data"
FIXTURES = TOOLS / "tests/data/allocation"
sys.path.insert(0, str(TOOLS / "tests"))
sys.path.insert(0, str(TOOLS / "code"))
from test_allocation_regression import assert_output_equivalent, GOLDEN  # noqa: E402
from mod_map_io import Grid, parser  # noqa: E402
from mod_allocation_map_io import read_allocation_hires  # noqa: E402
from hires_metadata import LocationArea, read_location_csv, write_location_csv  # noqa: E402


class AllocationNetCDFTests(unittest.TestCase):
    def test_python_allocation_reader_keeps_single_area_restriction(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmf-allocation-multiarea-") as temp_name:
            root = Path(temp_name)
            directory = root / "1min"
            directory.mkdir()
            write_location_csv(directory / 'location.csv', [
                LocationArea(1, 'tile-a', 0, .1, 0, .1, 1, 1, .1),
                LocationArea(2, 'tile-b', .1, .2, 0, .1, 1, 1, .1),
            ])
            with self.assertRaisesRegex(ValueError, "exactly one high-resolution area"):
                read_allocation_hires(root, "1min")

    def test_standard_netcdf_layout_and_allocation_outputs(self) -> None:
        self.assertTrue((SAMPLE / "params.txt").is_file())
        self.assertTrue((SAMPLE / "1min/location.csv").is_file())
        cli = parser("allocation NetCDF contract check")
        cli.parse_args(["--map-dir", str(SAMPLE)])

        base_grid = Grid.read(SAMPLE / "params.txt")
        base_uparea = base_grid.raster(SAMPLE / "uparea.bin", "<f4")
        base_nextxy = base_grid.raster(SAMPLE / "nextxy.bin", "<i4", 2)
        self.assertEqual(base_uparea.shape, (base_grid.ny, base_grid.nx))
        self.assertEqual(base_uparea.dtype, np.dtype("<f4"))
        self.assertEqual(base_nextxy.shape, (2, base_grid.ny, base_grid.nx))
        self.assertEqual(base_nextxy.dtype, np.dtype("<i4"))
        with Dataset(SAMPLE / "uparea.nc") as dataset:
            dataset.variables["uparea"].set_auto_maskandscale(False)
            np.testing.assert_array_equal(base_uparea, dataset.variables["uparea"][:])
        with Dataset(SAMPLE / "nextxy.nc") as dataset:
            for index, name in enumerate(("nextx", "nexty")):
                dataset.variables[name].set_auto_maskandscale(False)
                np.testing.assert_array_equal(base_nextxy[index], dataset.variables[name][:])

        location, = read_location_csv(SAMPLE / '1min/location.csv')
        nx, ny = location.nx, location.ny
        west, east, south, north = location.west, location.east, location.south, location.north
        hires_grid = Grid(nx, ny, 0, np.float32((east-west)/nx), west, east, south, north)
        hires_uparea = hires_grid.raster(SAMPLE / "1min/1min.uparea.bin", "<f4")
        hires_catmxy = hires_grid.raster(SAMPLE / "1min/1min.catmxy.bin", "<i2", 2)
        hires_downxy = hires_grid.raster(SAMPLE / "1min/1min.downxy.bin", "<i2", 2)
        self.assertEqual(hires_uparea.shape, (ny, nx))
        self.assertEqual(hires_uparea.dtype, np.dtype("<f4"))
        self.assertEqual(hires_catmxy.shape, (2, ny, nx))
        self.assertEqual(hires_catmxy.dtype, np.dtype("<i2"))
        self.assertEqual(hires_downxy.shape, (2, ny, nx))
        self.assertEqual(hires_downxy.dtype, np.dtype("<i2"))
        for filename, values, names in (
            ("1min.catmxy.nc", hires_catmxy, ("catmxx", "catmyy")),
            ("1min.downxy.nc", hires_downxy, ("downx", "downy")),
        ):
            with Dataset(SAMPLE / "1min" / filename) as dataset:
                for index, name in enumerate(names):
                    dataset.variables[name].set_auto_maskandscale(False)
                    np.testing.assert_array_equal(values[index], dataset.variables[name][:])

        with tempfile.TemporaryDirectory(prefix="cmf-allocation-netcdf-") as temp_name:
            temp = Path(temp_name)
            commands = (
                ("allocate_flow_gauge.py", (DATA / "GRDC_allocated.csv", "multi", "1min"),
                 (("flow_multi.txt", "gauge_alloc.txt"),)),
                ("allocate_dam.py", (DATA / "GRanD_allocated.csv", "1min"),
                 (("dam_river.txt", "dam_alloc_river.txt"),
                  ("dam_small.txt", "dam_alloc_small.txt"),
                  ("dam_error.txt", "dam_alloc_error.txt"))),
                ("allocate_level_gauge.py", (FIXTURES / "level_synthetic_mekong.csv", "1min"),
                 (("level_gauge.txt", "gauge_alloc.txt"),)),
            )
            for name, arguments, comparisons in commands:
                output = temp / Path(name).stem
                output.mkdir()
                subprocess.run(
                    [sys.executable, "-B", str(TOOLS / "code" / name),
                     *map(str, arguments), "--map-dir", str(SAMPLE), "--output-dir", str(output)],
                    cwd=REPO, check=True, capture_output=True, text=True,
                )
                for golden, produced in comparisons:
                    assert_output_equivalent(self, GOLDEN / golden, output / produced)

    def test_explicit_legacy_binary_mode_remains_available(self) -> None:
        self.assertTrue((SAMPLE / "binary/1min/location.txt").is_file())
        with tempfile.TemporaryDirectory(prefix="cmf-allocation-binary-") as temp_name:
            output = Path(temp_name)
            subprocess.run(
                [sys.executable, "-B", str(TOOLS / "code/allocate_flow_gauge.py"),
                 str(DATA / "GRDC_allocated.csv"), "multi", "1min", "--map-dir", str(SAMPLE),
                 "--map-format", "binary", "--output-dir", str(output)],
                cwd=REPO, check=True, capture_output=True, text=True,
            )
            assert_output_equivalent(self, GOLDEN / "flow_multi.txt", output / "gauge_alloc.txt")


if __name__ == "__main__":
    unittest.main()
