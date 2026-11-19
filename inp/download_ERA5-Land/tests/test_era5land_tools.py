"""Offline compatibility tests for the ERA5-Land conversion tools.

These tests use synthetic fields only. They do not contact CDS or read/write
the tracked Japan samples. The first-record and reset tests intentionally pin
the current converter behavior; KG-0019 remains open for scientific review.
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1]


def load_tool(name: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


download = load_tool("download_era5land")
try:
    import numpy as np
    import pandas as pd
    import xarray as xr
    import netCDF4  # noqa: F401
except ImportError:
    convert_nc = runoff_info = None
    CONVERSION_DEPENDENCIES_AVAILABLE = False
else:
    convert_nc = load_tool("convert_CMF_nc")
    runoff_info = load_tool("make_CMF_runoff_info")
    CONVERSION_DEPENDENCIES_AVAILABLE = True


def accumulated_field(values, times):
    return xr.DataArray(
        np.asarray(values, dtype=np.float32)[:, None, None],
        dims=("time", "lat", "lon"),
        coords={"time": pd.to_datetime(times), "lat": [10.0], "lon": [20.0]},
        name="runoff",
        attrs={"units": "m"},
    )


class DownloaderRequestTests(unittest.TestCase):
    def make_args(self, **overrides):
        values = dict(
            year=2000, month=2, day=None, start_day=1, end_day=29,
            variable="runoff", time_step=6, area_nswe=[46.0, 24.0, 122.0, 154.0],
            area_is="edge", grid=0.1, retries=3,
        )
        values.update(overrides)
        return Namespace(**values)

    def test_monthly_request_is_daily_records_grouped_by_month(self):
        request = download.make_request(self.make_args(), "monthly")
        self.assertEqual(request["variable"], ["runoff"])
        self.assertEqual(request["day"], [f"{day:02d}" for day in range(1, 30)])
        self.assertEqual(request["time"], ["00:00", "06:00", "12:00", "18:00"])
        self.assertEqual(request["area"], [46.0, 122.0, 24.0, 154.0])
        self.assertEqual(request["data_format"], "netcdf")

    def test_center_area_expands_by_half_grid_and_reorders_for_cds(self):
        args = self.make_args(area_is="center")
        self.assertEqual(download.make_cds_area(args), [46.05, 121.95, 23.95, 154.05])

    def test_invalid_month_is_rejected_without_network_access(self):
        with self.assertRaisesRegex(ValueError, "month"):
            download.validate_args(self.make_args(month=13))


@unittest.skipUnless(CONVERSION_DEPENDENCIES_AVAILABLE, "requires NumPy, pandas, xarray, and NetCDF4")
class AccumulationCompatibilityTests(unittest.TestCase):
    def test_nc_conversion_differences_within_each_utc_day(self):
        data = accumulated_field(
            [0.10, 0.30, 0.05, 0.20],
            ["2000-01-01T00", "2000-01-01T12", "2000-01-02T00", "2000-01-02T12"],
        )
        increments = convert_nc.accumulated_to_increment_daily_groups(
            data, first_step="keep", clip_negative=True
        )
        np.testing.assert_allclose(increments.isel(lat=0, lon=0).values, [0.10, 0.20, 0.05, 0.15])

    def test_current_first_record_and_reset_rules_are_pinned_as_compatibility(self):
        data = accumulated_field(
            [0.2, 0.4, 0.1, 0.15],
            ["2000-01-01T00", "2000-01-01T06", "2000-01-01T12", "2000-01-01T18"],
        )
        nc_values = convert_nc.accumulated_to_increment_daily_groups(
            data, first_step="keep", clip_negative=True
        ).isel(lat=0, lon=0).values
        expected = [0.2, 0.2, 0.1, 0.05]
        np.testing.assert_allclose(nc_values, expected)

    def test_nan_accumulation_remains_missing(self):
        data = accumulated_field(
            [0.1, np.nan, 0.3],
            ["2000-01-01T00", "2000-01-01T08", "2000-01-01T16"],
        )
        increments = convert_nc.accumulated_to_increment_daily_groups(
            data, first_step="keep", clip_negative=True
        ).isel(lat=0, lon=0).values
        self.assertTrue(np.isnan(increments[1]))


@unittest.skipUnless(CONVERSION_DEPENDENCIES_AVAILABLE, "requires NumPy, pandas, xarray, and NetCDF4")
class IncrementArithmeticTests(unittest.TestCase):
    def test_intra_cycle_increments_are_differences_of_cumulative_values(self):
        # Assumption for this arithmetic check: all three values are from one
        # cumulative forecast cycle. The physical attribution of the first
        # timestamp is not asserted here (see KG-0019).
        data = accumulated_field(
            [0.1, 0.3, 0.6],
            ["2000-01-01T00", "2000-01-01T06", "2000-01-01T12"],
        )
        increments = convert_nc.accumulated_to_increment_daily_groups(
            data, first_step="keep", clip_negative=True
        ).isel(lat=0, lon=0).values
        np.testing.assert_allclose(increments[1:], [0.2, 0.3])


@unittest.skipUnless(CONVERSION_DEPENDENCIES_AVAILABLE, "requires NumPy, pandas, xarray, and NetCDF4")
class OutputFormatTests(unittest.TestCase):
    def test_netcdf_output_units_fill_and_latitude_order(self):
        times = pd.to_datetime(["2000-01-01T00", "2000-01-01T12"])
        raw = xr.Dataset(
            {"runoff": (("time", "lat", "lon"), np.array([
                [[0.1, 0.2], [0.3, 0.4]], [[0.2, 0.4], [0.6, 0.8]]
            ], dtype=np.float32), {"units": "m"})},
            coords={"time": times, "lat": [0.0, 1.0], "lon": [10.0, 11.0]},
        )
        args = Namespace(
            input_variable="runoff", output_variable="runoff", first_step="keep",
            clip_negative=True, timestep_hours=12, lat_order="NtoS", input_file_unit="daily",
            input_pattern="synthetic.nc",
        )
        result = convert_nc.build_output_dataset(
            raw, args, pd.Timestamp("2000-01-01").date(), pd.Timestamp("2000-01-01").date()
        )
        self.assertEqual(result["runoff"].attrs["units"], "mm")
        self.assertEqual(result.sizes["time"], 2)
        np.testing.assert_array_equal(result["lat"].values, [1.0, 0.0])
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "runoff.nc"
            convert_nc.save_output(result, target, "runoff", 1.0e20, overwrite=False)
            with xr.open_dataset(target) as written:
                self.assertEqual(written["runoff"].dims, ("time", "lat", "lon"))
                self.assertEqual(written["runoff"].dtype, np.dtype("float32"))
                self.assertEqual(written["runoff"].attrs["units"], "mm")
                self.assertTrue(written["runoff"].encoding["zlib"])
                self.assertEqual(written["runoff"].encoding["complevel"], 3)
                self.assertTrue(written["runoff"].encoding["shuffle"])






if __name__ == "__main__":
    unittest.main()
