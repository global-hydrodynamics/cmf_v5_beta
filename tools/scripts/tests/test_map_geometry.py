"""Focused tests for model-grid geometry read by model CTL generators."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "tools" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from generate_output_ctl import generate as generate_output_ctls
from generate_restart_ctl import generate as generate_restart_ctls
from map_geometry import MapMetadataError, read_map_geometry


class MapGeometryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.run_dir = self.root / "run"
        self.map_dir = self.run_dir / "map"
        self.map_dir.mkdir(parents=True)
        (self.map_dir / "nextxy.nc").touch()
        (self.map_dir / "ctmare.nc").touch()
        self.write_params()
        self.write_diminfo()

    def write_params(self, *, west: float = 1.0) -> None:
        (self.map_dir / "params.nml").write_text(
            "&GRID\n NX=4\n NY=2\n NLFP=3\n RESOLUTION=0.5\n/\n"
            f"&DOMAIN\n WEST={west}\n EAST=3.0\n SOUTH=-1.0\n NORTH=0.0\n/\n",
            encoding="ascii",
        )

    def write_diminfo(self, *, west: float = 1.0, east: float = 3.0, input_shape: tuple[int, int] = (900, 400)) -> None:
        nxin, nyin = input_shape
        (self.map_dir / "diminfo_test.nml").write_text(
            "&DIMINFO\n NX=4\n NY=2\n NLFP=3\n"
            f" WEST={west}\n EAST={east}\n SOUTH=-1.0\n NORTH=0.0\n/\n"
            "&INPUTDIM\n INPMAT_FILE='inpmat.nc'\n"
            f" NXIN={nxin}\n NYIN={nyin}\n INPN=1\n"
            " WESTIN=-180.0\n EASTIN=180.0\n SOUTHIN=-90.0\n NORTHIN=90.0\n OLATIN='NtoS'\n/\n",
            encoding="ascii",
        )

    def values(self) -> dict[str, str]:
        return {
            "CNEXTXY": "map/nextxy.nc",
            "CGRAREA": "map/ctmare.nc",
            "CDIMINFO": "map/diminfo_test.nml",
        }

    def write_model_namelist(self, *, restart: bool = False) -> Path:
        self.run_dir.mkdir(exist_ok=True)
        values = [
            "&RUN\nSYEAR=2000\nSMON=1\nSDAY=1\nSHOUR=0\n"
            "EYEAR=2000\nEMON=1\nEDAY=2\nEHOUR=0\n/\n",
            "&OUTPUT\nIFRQ_OUT=24\nDT=3600\nCVARSOUT='outflw'\n"
            "COUTDIR='./'\nCOUTTAG='test'\nLOUTCDF=.FALSE.\nLOUTVEC=.FALSE.\n/\n",
            "&MAP\nCNEXTXY='map/nextxy.nc'\nCGRAREA='map/ctmare.nc'\n"
            "CDIMINFO='map/diminfo_test.nml'\n/\n",
        ]
        if restart:
            values.append(
                "&NRESTART\nLRESTCDF=.FALSE.\nLSTOONLY=.TRUE.\n"
                "LGDWDLY=.FALSE.\nLDAMOUT=.FALSE.\nLLEVEE=.FALSE.\n"
                "CVNREST='restart'\nCSUFBIN='.bin'\nCRESTDIR='./'\n"
                "LRESTDBL=.TRUE.\nDMIS=1.0E20\n/\n"
            )
        path = self.run_dir / "input_cmf.nam"
        path.write_text("\n".join(values), encoding="ascii")
        return path

    def test_params_is_authoritative_and_paired_diminfo_agrees(self) -> None:
        geometry = read_map_geometry(self.run_dir, self.values())
        self.assertEqual(
            (geometry.nx, geometry.ny, geometry.resolution, geometry.west,
             geometry.east, geometry.south, geometry.north),
            (4, 2, 0.5, 1.0, 3.0, -1.0, 0.0),
        )

    def test_diminfo_model_geometry_fallback_ignores_inputdim_axes(self) -> None:
        (self.map_dir / "params.nml").unlink()
        geometry = read_map_geometry(self.run_dir, self.values())
        self.assertEqual((geometry.nx, geometry.ny, geometry.resolution), (4, 2, 0.5))

    def test_inconsistent_pair_and_non_square_diminfo_are_rejected(self) -> None:
        self.write_diminfo(west=1.25, east=3.25)
        with self.assertRaisesRegex(MapMetadataError, "conflicts"):
            read_map_geometry(self.run_dir, self.values())

        (self.map_dir / "params.nml").unlink()
        self.write_diminfo(west=1.0)
        path = self.map_dir / "diminfo_test.nml"
        path.write_text(path.read_text().replace("NORTH=0.0", "NORTH=1.0"), encoding="ascii")
        with self.assertRaisesRegex(MapMetadataError, "spacing differ"):
            read_map_geometry(self.run_dir, self.values())

    def test_legacy_params_txt_remains_supported(self) -> None:
        (self.map_dir / "params.nml").unlink()
        (self.map_dir / "diminfo_test.nml").unlink()
        (self.map_dir / "params.txt").write_text(
            "4\n2\n3\n0.5\n1\n3\n-1\n0\n", encoding="ascii"
        )
        self.assertEqual(read_map_geometry(self.run_dir, self.values()).resolution, 0.5)

    def test_planned_output_and_restart_ctl_use_model_axes(self) -> None:
        namelist = self.write_model_namelist()
        output_registry = ROOT / "variable_table" / "output_variables.csv"
        self.assertEqual(generate_output_ctls(argparse.Namespace(
            run_dir=self.run_dir, namelist=namelist, registry=output_registry,
            mode="planned", endian="little_endian",
        )), 0)
        output_ctl = (self.run_dir / "outflwtest.ctl").read_text(encoding="utf-8")
        self.assertIn("XDEF 4 LINEAR 1.25 0.5", output_ctl)
        self.assertIn("YDEF 2 LINEAR -0.75 0.5", output_ctl)

        restart_namelist = self.write_model_namelist(restart=True)
        restart = self.run_dir / "restart2000010100.bin"
        restart.write_bytes(b"\0" * (4 * 2 * 8 * 2))
        self.assertEqual(generate_restart_ctls(argparse.Namespace(
            run_dir=self.run_dir, namelist=restart_namelist,
            registry=ROOT / "variable_table" / "restart_variables.csv",
            restart=restart, endian="little",
        )), 0)
        restart_ctl = restart.with_suffix(".ctl").read_text(encoding="utf-8")
        self.assertIn("XDEF 4 LINEAR 1.25 0.5", restart_ctl)
        self.assertIn("YDEF 2 LINEAR -0.75 0.5", restart_ctl)


if __name__ == "__main__":
    unittest.main(verbosity=2)
