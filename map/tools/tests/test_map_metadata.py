# SPDX-License-Identifier: Apache-2.0
"""Focused checks for TOML map geometry and legacy compatibility."""
from decimal import Decimal
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
CODE = ROOT / "map/tools/code"
sys.path.insert(0, str(CODE))

from map_metadata import read_legacy_values, read_map_geometry
from migrate_map_params import convert_map, write_legacy_copy
from mod_map_io import Grid


class MapMetadataTests(unittest.TestCase):
    def test_all_local_map_txt_files_convert_and_match(self):
        paths = sorted((ROOT / "map").rglob("params.txt"))
        self.assertEqual(len(paths), 5)
        for txt_path in paths:
            with self.subTest(path=txt_path.relative_to(ROOT)):
                tokens, legacy = read_legacy_values(txt_path)
                toml = txt_path.with_name("params.toml")
                self.assertTrue(toml.is_file())
                geometry = read_map_geometry(txt_path.parent)
                self.assertEqual(geometry.values(), legacy.values())
                for token, value in zip(tokens, geometry.values()):
                    self.assertEqual(Decimal(token), Decimal(str(value)))

    def test_txt_only_legacy_and_toml_only_maps_are_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            map_dir = Path(temporary)
            txt = map_dir / "params.txt"
            txt.write_text("2\n3\n4\n0.5\n10\n11\n20\n21.5\n", encoding="utf-8")
            grid = Grid.read(map_dir)
            self.assertEqual((grid.nx, grid.ny, grid.nlfp), (2, 3, 4))
            self.assertEqual(convert_map(map_dir), "CONVERTED")
            txt.unlink()
            self.assertEqual(read_map_geometry(map_dir).values(), (2, 3, 4, .5, 10., 11., 20., 21.5))

    def test_conflicting_existing_toml_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            map_dir = Path(temporary)
            (map_dir / "params.txt").write_text("2\n3\n4\n0.5\n10\n11\n20\n21.5\n", encoding="utf-8")
            toml = map_dir / "params.toml"
            original = "[grid]\nnx=9\nny=3\nnlfp=4\nresolution=0.5\n[domain]\nwest=10.0\neast=11.0\nsouth=20.0\nnorth=21.5\n"
            toml.write_text(original, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Conflicting map geometry"):
                convert_map(map_dir)
            self.assertEqual(toml.read_text(encoding="utf-8"), original)

    def test_legacy_writer_refuses_conflict_and_writes_matching_geometry(self):
        with tempfile.TemporaryDirectory() as temporary:
            map_dir = Path(temporary)
            (map_dir / "params.toml").write_text(
                "[grid]\nnx=2\nny=3\nnlfp=4\nresolution=0.5\n"
                "[domain]\nwest=10.0\neast=11.0\nsouth=20.0\nnorth=21.5\n",
                encoding="utf-8",
            )
            output = Path("binary/params.txt")
            self.assertEqual(write_legacy_copy(map_dir, output), "WRITTEN")
            self.assertEqual(read_legacy_values(map_dir / output)[1].values(),
                             read_map_geometry(map_dir).values())
            (map_dir / output).write_text("9\n3\n4\n0.5\n10\n11\n20\n21.5\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                write_legacy_copy(map_dir, output)


if __name__ == "__main__":
    unittest.main()
