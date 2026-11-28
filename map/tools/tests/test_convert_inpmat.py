"""Check two-way INPMAT conversion and safe regeneration of paired DIMINFO."""
from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
CODE = ROOT / "map/tools/code"
SCRIPT = ROOT / "map/tools/script_format_conv/s14-bin2nc_inpmat.sh"
sys.path.insert(0, str(CODE))

from convert_inpmat import convert
from map_metadata import DimInfo, read_diminfo_nml, write_diminfo_nml
from mod_map_io import read_inpmat, write_inpmat


def sample_arrays():
    inpx = np.array([[[1, 2], [3, 4]]], dtype="<i4")
    inpy = np.array([[[5, 6], [7, 8]]], dtype="<i4")
    inpa = np.array([[[0.25, 0.5], [0.75, 1.0]]], dtype="<f4")
    return inpx, inpy, inpa


def sample_diminfo(matrix_name: str = "inpmat_test-1deg.bin") -> DimInfo:
    return DimInfo(2, 2, 1, -1.0, 1.0, 1.0, -1.0, matrix_name,
                   4, 2, 1, -180.0, 180.0, 90.0, -90.0, "NtoS")


class InpmatConversionTests(unittest.TestCase):
    def test_s14_overwrites_conflicting_map_root_diminfo_and_preserves_binary_sources(self):
        with tempfile.TemporaryDirectory(prefix="cmf-inpmat-s14-") as temporary:
            map_root = Path(temporary)
            binary = map_root / "binary"
            script_dir = map_root / "script_format_conv"
            binary.mkdir()
            script_dir.mkdir()
            source = binary / "inpmat_test-1deg.bin"
            source_diminfo = binary / "diminfo_test-1deg.nml"
            destination_diminfo = map_root / source_diminfo.name
            destination = map_root / "inpmat_test-1deg.nc"
            inpx, inpy, inpa = sample_arrays()
            np.stack((inpx, inpy, inpa.view("<i4"))).tofile(source)
            write_diminfo_nml(source_diminfo, sample_diminfo(source.name))
            source_bytes = source.read_bytes()
            source_metadata = source_diminfo.read_bytes()
            conflicting = DimInfo(3, 2, 1, -2.0, 1.0, 1.0, -1.0, "old_matrix.nc",
                                  4, 2, 1, -180.0, 180.0, 90.0, -90.0, "NtoS")
            write_diminfo_nml(destination_diminfo, conflicting)
            shutil.copyfile(SCRIPT, script_dir / SCRIPT.name)

            python = ROOT / ".venv/bin"
            environment = dict(os.environ)
            environment["CMF_V50_ROOT"] = str(ROOT)
            environment["PATH"] = f"{python}:{environment['PATH']}"
            result = subprocess.run(
                ["sh", str(script_dir / SCRIPT.name)], cwd=script_dir,
                input="", text=True, capture_output=True, env=environment, check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(f"Overwrote paired DIMINFO: ../{destination_diminfo.name}", result.stdout)
            self.assertTrue(destination.is_file())
            self.assertEqual(source.read_bytes(), source_bytes)
            self.assertEqual(source_diminfo.read_bytes(), source_metadata)
            self.assertEqual(read_diminfo_nml(destination_diminfo),
                             replace(sample_diminfo(source.name), inpmat_file=destination.name))
            actual = read_inpmat(destination, nx=2, ny=2, slots=1)
            for expected, observed in zip((inpx, inpy, inpa), actual):
                np.testing.assert_array_equal(observed, expected)
            self.assertFalse(list(map_root.glob(".diminfo_test-1deg.nml.*.tmp")))

    def test_netcdf_to_binary_overwrites_conflicting_binary_diminfo(self):
        with tempfile.TemporaryDirectory(prefix="cmf-inpmat-nc2bin-") as temporary:
            map_root = Path(temporary)
            binary = map_root / "binary"
            binary.mkdir()
            source = map_root / "inpmat_test-1deg.nc"
            source_diminfo = map_root / "diminfo_test-1deg.nml"
            destination = binary / "inpmat_test-1deg.bin"
            destination_diminfo = binary / source_diminfo.name
            expected_diminfo = sample_diminfo(source.name)
            write_inpmat(source, *sample_arrays(), {
                "nx": 2, "ny": 2, "inpn": 1, "nxin": 4, "nyin": 2, "nlfp": 1,
            })
            write_diminfo_nml(source_diminfo, expected_diminfo)
            source_bytes = source.read_bytes()
            source_metadata = source_diminfo.read_bytes()
            write_diminfo_nml(destination_diminfo,
                              DimInfo(3, 2, 1, -2.0, 1.0, 1.0, -1.0, "old_matrix.bin",
                                      4, 2, 1, -180.0, 180.0, 90.0, -90.0, "NtoS"))

            convert(source, destination, source_diminfo, "netcdf-to-binary")

            self.assertEqual(source.read_bytes(), source_bytes)
            self.assertEqual(source_diminfo.read_bytes(), source_metadata)
            self.assertEqual(read_diminfo_nml(destination_diminfo),
                             replace(expected_diminfo, inpmat_file=destination.name))
            self.assertEqual(destination.stat().st_size, 3 * 1 * 2 * 2 * 4)
            actual = read_inpmat(destination, nx=2, ny=2, slots=1)
            for expected, observed in zip(sample_arrays(), actual):
                np.testing.assert_array_equal(observed, expected)
            self.assertFalse(list(binary.glob(".diminfo_test-1deg.nml.*.tmp")))


if __name__ == "__main__":
    unittest.main()
