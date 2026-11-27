"""Focused checks for the separated bifurcation-width file contract."""

import csv
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "map" / "tools" / "code"))

from mod_bifprm_csv import read_bifprm_csv
from convert_bifprm_csv_to_netcdf import convert
from param_bif_set_params import format_geo_coordinate


BASE_FIELDS = (
    "pth_id", "ix", "iy", "jx", "jy", "length", "elevtn", "depth",
    "riv_width", "start_lat", "start_lon", "end_lat", "end_lon", "ibsn", "jbsn",
)


def test_bifprm_geographic_coordinates_use_three_decimal_places():
    assert format_geo_coordinate(33.6251) == "33.625"
    assert format_geo_coordinate(94.6255) == "94.626"


def write_table(path: Path, overland: tuple[str, ...] = ()) -> None:
    fields = list(BASE_FIELDS) + list(overland)
    row = [1, 4, 5, 6, 7, 8, 0.5, 12, 10, 100, 11, 101, 12, 2, 3]
    row.extend(20 + index for index in range(len(overland)))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow([f"  {name}  " for name in fields])
        writer.writerow([f" {value} " for value in row])


def test_reader_maps_channel_then_overland_and_ignores_blank_optional_column(tmp_path):
    path = tmp_path / "bifprm.csv"
    fields = list(BASE_FIELDS) + ["ovl_width_1", "ovl_width_2", " future_note "]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow([f" {name} " for name in fields])
        writer.writerow([1, 4, 5, 6, 7, 8, 0.5, 0.25, 12, 10, 100, 11, 101, 2, 3, 20, 30, ""])

    result = read_bifprm_csv(path)[0]
    np.testing.assert_array_equal(result["widths"], [12, 20, 30])
    np.testing.assert_array_equal(result["ovl_widths"], [20, 30])


def test_reader_accepts_zero_overland_layers(tmp_path):
    path = tmp_path / "zero.csv"
    write_table(path)

    result = read_bifprm_csv(path)[0]
    np.testing.assert_array_equal(result["widths"], [10])
    assert result["ovl_widths"].size == 0


def test_converter_omits_overland_schema_when_no_overland_layers(tmp_path):
    pytest.importorskip("netCDF4")
    path = tmp_path / "zero.csv"
    fields = list(BASE_FIELDS) + ["future_note"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(fields)
        writer.writerow([1, 4, 5, 6, 7, 8, 0.5, 0.25, 12, 10, 100, 11, 101, 2, 3, ""])
    output = tmp_path / "zero.nc"
    convert(path, output)
    from netCDF4 import Dataset

    with Dataset(output) as dataset:
        assert "layer" not in dataset.dimensions
        assert "ovl_width" not in dataset.variables
        assert dataset.variables["riv_width"].dimensions == ("path",)
        assert dataset.variables["riv_width"][:].tolist() == [12]


@pytest.mark.parametrize(
    "header,match",
    [
        ("ovl_width_2", "consecutive"),
        ("ovl_width_x", "invalid overland"),
        ("ovl_width_1,ovl_width_1", "duplicate"),
        ("riv_width", "duplicate"),
    ],
)
def test_reader_rejects_missing_or_malformed_overland_fields(tmp_path, header, match):
    path = tmp_path / "bad.csv"
    path.write_text(
        ",".join(BASE_FIELDS) + "," + header + "\n"
        "1,4,5,6,7,8,0.5,0.25,12,10,100,11,101,2,3,20\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=match):
        read_bifprm_csv(path)
