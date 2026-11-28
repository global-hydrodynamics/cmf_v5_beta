# SPDX-License-Identifier: Apache-2.0
"""Focused checks for Namelist map geometry and legacy TXT compatibility."""
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
CODE = ROOT / "map/tools/code"
sys.path.insert(0, str(CODE))

from map_metadata import (
    DimInfo, MapGeometry, read_diminfo_nml, read_legacy_diminfo,
    read_legacy_values, read_map_geometry, read_nml_values, write_diminfo_nml,
    write_nml,
)
from migrate_map_params import write_legacy_copy
from mod_map_io import Grid


class MapMetadataTests(unittest.TestCase):
    def test_diminfo_nml_round_trip_uses_f90nml_and_preserves_all_fields(self):
        expected = DimInfo(80, 120, 10, 90.0, 110.0, 35.0, 5.0,
                           "inpmat_sample.nc", 360, 180, 4,
                           -180.0, 180.0, 90.0, -90.0, "NtoS")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "diminfo_sample.nml"
            write_diminfo_nml(path, expected)
            actual = read_diminfo_nml(path)
            text = path.read_text(encoding="utf-8")
        self.assertEqual(actual, expected)
        self.assertLess(text.lower().index("&diminfo"), text.lower().index("&inputdim"))
        self.assertLess(text.index("  NX    ="), text.index("  WEST  ="))
        self.assertLess(text.index("  INPMAT_FILE"), text.index("  OLATIN"))

    def test_diminfo_bounds_use_precision_aware_shortest_decimal_format(self):
        float32_bounds = tuple(np.float32(value) for value in (2.45, 13.55, 53.55, 44.45))
        high_precision_float64 = np.float64(53.550000000000004)
        diminfo = DimInfo(
            4, 5, 1, float32_bounds[0], float32_bounds[1],
            high_precision_float64, float32_bounds[3],
            "inpmat_sample.nc", 360, 180, 1,
            *float32_bounds, "NtoS",
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "diminfo_precision.nml"
            write_diminfo_nml(path, diminfo)
            text = path.read_text(encoding="utf-8")
            actual = read_diminfo_nml(path)

        self.assertIn("WEST  = 2.45", text)
        self.assertIn("EAST  = 13.55", text)
        self.assertIn("NORTH = 53.550000000000004", text)
        self.assertIn("SOUTH = 44.45", text)
        self.assertIn("NORTHIN = 53.55", text)
        self.assertIn("SOUTHIN = 44.45", text)
        for original, restored in zip(float32_bounds, (
                actual.west, actual.east, actual.northin, actual.southin)):
            self.assertEqual(np.float32(restored), original)
        self.assertEqual(actual.north, float(high_precision_float64))

    def test_legacy_diminfo_is_rejected_when_input_grid_provenance_is_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "diminfo_sample.txt"
            source.write_text("80\n120\n10\n360\n180\n4\ninpmat_sample.nc\n"
                              "90\n110\n35\n5\n", encoding="ascii")
            with self.assertRaisesRegex(ValueError, "input-grid bounds and latitude order"):
                read_legacy_diminfo(source)
            self.assertTrue(source.exists())

    def test_old_single_group_namelist_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "diminfo_old.nml"
            path.write_text("&DIMINFO NX=2, NY=3, NLFP=1, NXIN=2, NYIN=3, INPN=1, "
                            "INPMAT_FILE='a.nc', WEST=0, EAST=2, NORTH=3, SOUTH=0 /\n")
            with self.assertRaisesRegex(ValueError, "exactly &DIMINFO and &INPUTDIM"):
                read_diminfo_nml(path)

    def test_sample_geometry_matches_expected_map_extent(self):
        map_dir = ROOT / "map/mekong_15min"
        geometry = read_map_geometry(map_dir)
        self.assertEqual(geometry.values(), (80, 120, 10, 0.25, 90.0, 110.0, 5.0, 35.0))

    def test_txt_only_legacy_and_nml_only_maps_are_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            map_dir = Path(temporary)
            txt = map_dir / "params.txt"
            txt.write_text("2\n3\n4\n0.5\n10\n11\n20\n21.5\n", encoding="utf-8")
            grid = Grid.read(map_dir)
            self.assertEqual((grid.nx, grid.ny, grid.nlfp), (2, 3, 4))
            txt.unlink()
            geometry = MapGeometry(2, 3, 4, .5, 10., 11., 20., 21.5)
            write_nml(map_dir / "params.nml", geometry)
            self.assertEqual(read_nml_values(map_dir / "params.nml").values(), geometry.values())

    def test_nml_txt_conflict_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            map_dir = Path(temporary)
            (map_dir / "params.txt").write_text("2\n3\n4\n0.5\n10\n11\n20\n21.5\n", encoding="utf-8")
            write_nml(map_dir / "params.nml", MapGeometry(9, 3, 4, .5, 10., 11., 20., 21.5))
            with self.assertRaisesRegex(ValueError, "Conflicting map geometry"):
                read_map_geometry(map_dir)

    def test_legacy_writer_refuses_conflict_and_writes_matching_geometry(self):
        with tempfile.TemporaryDirectory() as temporary:
            map_dir = Path(temporary)
            write_nml(map_dir / "params.nml", MapGeometry(2, 3, 4, .5, 10., 11., 20., 21.5))
            output = Path("binary/params.txt")
            self.assertEqual(write_legacy_copy(map_dir, output), "WRITTEN")
            self.assertEqual(read_legacy_values(map_dir / output)[1].values(),
                             read_map_geometry(map_dir).values())
            (map_dir / output).write_text("9\n3\n4\n0.5\n10\n11\n20\n21.5\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                write_legacy_copy(map_dir, output)


if __name__ == "__main__":
    unittest.main()
