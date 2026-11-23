#!/usr/bin/env python3
"""Small contract test for the NetCDF event flddph adapter."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

import netCDF4
import pandas as pd
import xarray as xr
import numpy as np

SCRIPT = Path(__file__).resolve().parents[1] / "a02-prepare_downscale_input.py"
SPEC = importlib.util.spec_from_file_location("downscale_adapter", SCRIPT)
ADAPTER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ADAPTER)


class AdapterContractTests(unittest.TestCase):
    def test_exact_record_mask_clipping_and_netcdf_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output_nc, map_nc, output_flddph = root / "rivdph.nc", root / "rivhgt.nc", root / "flddph.nc"
            with netCDF4.Dataset(output_nc, "w") as ds:
                ds.createDimension("time", 2)
                ds.createDimension("lat", 2)
                ds.createDimension("lon", 3)
                t = ds.createVariable("time", "f8", ("time",))
                t.units = "hours since 2000-01-01 00:00:00"
                t[:] = [0, 24]
                lat = ds.createVariable("lat", "f4", ("lat",))
                lat[:] = [1, 0]
                lon = ds.createVariable("lon", "f4", ("lon",))
                lon[:] = [0, 1, 2]
                v = ds.createVariable("rivdph", "f4", ("time", "lat", "lon"), fill_value=np.float32(-9999))
                v.units = "m"
                v[0] = np.ones((2, 3), dtype="f4") * 20
                v[1] = np.array([[0.5, 2.0, -9999], [3.0, 4.0, 2.5]], dtype="f4")
            with netCDF4.Dataset(map_nc, "w") as ds:
                ds.createDimension("lat", 2)
                ds.createDimension("lon", 3)
                lat = ds.createVariable("lat", "f4", ("lat",))
                lat[:] = [1, 0]
                lon = ds.createVariable("lon", "f4", ("lon",))
                lon[:] = [0, 1, 2]
                v = ds.createVariable("rivhgt", "f4", ("lat", "lon"), fill_value=np.float32(-9999))
                v.units = "m"
                v[:] = np.array([[1, 1, 1], [2, 4, 1]], dtype="f4")
            result = ADAPTER.prepare_input(output_nc, map_nc, "2000-01-02T00:00:00", output_flddph)
            with xr.open_dataset(output_flddph, decode_times=True, mask_and_scale=True) as ds:
                self.assertEqual(ds["flddph"].dims, ("time", "lat", "lon"))
                self.assertEqual(ds["flddph"].attrs["units"], "m")
                np.testing.assert_array_equal(ds.lat.values, [1, 0])
                np.testing.assert_array_equal(ds.lon.values, [0, 1, 2])
                self.assertEqual(pd.Timestamp(ds.time.values[0]), pd.Timestamp("2000-01-02"))
                self.assertEqual(ds.attrs["derivation"], "max(rivdph - rivhgt, 0) on overlapping valid cells")
                raw = np.asarray(ds["flddph"].values[0], dtype=np.float32)
            np.testing.assert_array_equal(raw[0, :2], [0.0, 1.0])
            self.assertTrue(np.isnan(raw[0, 2]))
            np.testing.assert_array_equal(raw[1], [1.0, 0.0, 1.5])
            legacy_mask = np.array([[True, True, False], [True, True, True]])
            legacy_result = np.full((2, 3), np.float32(1.0e20), dtype=np.float32)
            legacy_result[legacy_mask] = np.maximum(
                np.array([[0.5, 2.0, 0.0], [3.0, 4.0, 2.5]], dtype=np.float32)[legacy_mask]
                - np.array([[1, 1, 1], [2, 4, 1]], dtype=np.float32)[legacy_mask], 0.0
            )
            expected = np.where(legacy_result == np.float32(1.0e20), np.nan, legacy_result)
            np.testing.assert_array_equal(raw, expected)
            self.assertEqual(result["time_index_zero_based"], 1)
            self.assertEqual(result["shape"], (2, 3))
            self.assertGreater(output_flddph.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
