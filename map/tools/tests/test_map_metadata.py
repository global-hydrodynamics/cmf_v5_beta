# SPDX-License-Identifier: Apache-2.0
"""Focused checks for Namelist map geometry and legacy TXT compatibility."""
from decimal import Decimal
from pathlib import Path
import sys
import tempfile
import unittest

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
from migrate_diminfo import convert as convert_diminfo


class MapMetadataTests(unittest.TestCase):
    def test_diminfo_nml_round_trip_uses_f90nml_and_preserves_all_fields(self):
        expected = DimInfo(80, 120, 10, 360, 180, 4, "inpmat_sample.nc",
                           90.0, 110.0, 35.0, 5.0)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "diminfo_sample.nml"
            write_diminfo_nml(path, expected)
            actual = read_diminfo_nml(path)
            text = path.read_text(encoding="utf-8")
        self.assertEqual(actual, expected)
        self.assertIn("&diminfo", text.lower())

    def test_legacy_diminfo_migration_is_verified_idempotent_and_safe(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "diminfo_sample.txt"
            source.write_text("80\n120\n10\n360\n180\n4\ninpmat_sample.nc\n"
                              "90\n110\n35\n5\n", encoding="ascii")
            old = read_legacy_diminfo(source)
            target = convert_diminfo(source)
            self.assertEqual(read_diminfo_nml(target), old)
            self.assertEqual(convert_diminfo(source), target)
            source.unlink()

    def test_diminfo_migration_refuses_conflicting_nml(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "diminfo_sample.txt"
            source.write_text("80\n120\n10\n360\n180\n4\ninpmat_sample.nc\n"
                              "90\n110\n35\n5\n", encoding="ascii")
            write_diminfo_nml(source.with_suffix(".nml"),
                              DimInfo(81, 120, 10, 360, 180, 4, "inpmat_sample.nc",
                                      90.0, 110.0, 35.0, 5.0))
            with self.assertRaisesRegex(ValueError, "Conflicting metadata"):
                convert_diminfo(source)
            self.assertTrue(source.exists())

    def test_sample_geometry_matches_legacy_txt(self):
        map_dir = ROOT / "map/mekong_15min"
        tokens, legacy = read_legacy_values(map_dir / "params.txt")
        self.assertEqual((map_dir / "params.nml").is_file(), True)
        geometry = read_map_geometry(map_dir)
        self.assertEqual(geometry.values(), legacy.values())
        for token, value in zip(tokens, geometry.values()):
            self.assertEqual(Decimal(token), Decimal(str(value)))

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
