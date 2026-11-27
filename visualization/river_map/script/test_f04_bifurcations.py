"""Native path classification and corrected f04a/f04b Gallery comparison."""

from pathlib import Path
import csv
import hashlib
import sys

import matplotlib.pyplot as plt
from netCDF4 import Dataset
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent))
from f04_rivmap_catchment import read_bifurcations, read_channel_bifurcations, draw_bifurcations, OVERLAND_COLOR, EXTENT

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def paths(tmp_path):
    lon = np.array([[104.75, 105.5, 106.25]])
    lat = np.array([[10.0, 10.5, 11.0]])
    ix = np.array([1, 2, 1, 3, 1, 99, 1, 1])
    jx = np.array([2, 3, 2, 2, 3, 2, 2, 3])
    first = np.array([10, 0, 0, 20, -1, 10, 50, np.nan])
    file = tmp_path / "bif.nc"
    with Dataset(file, "w") as d:
        d.createDimension("path", len(ix))
        d.createDimension("layer", 1)
        for key, values in [("ix", ix), ("jx", jx), ("iy", np.ones(len(ix))), ("jy", np.ones(len(ix)))]:
            d.createVariable(key, "i4", ("path",))[:] = values
        w = d.createVariable("riv_width", "f4", ("path",))
        w.units = "m"
        w[:] = first
        w = d.createVariable("ovl_width", "f4", ("layer", "path"))
        w.units = "m"
        w[:] = np.full((1, len(ix)), 30.0)
        d.createVariable("end_lon", "f8", ("path",))[:] = lon[0, jx - 1]
        d.createVariable("end_lat", "f8", ("path",))[:] = lat[0, jx - 1]
    return file, lon, lat


def test_native_classification_dedup_and_invalid_paths(paths):
    file, lon, lat = paths
    segments, width = read_bifurcations(file, lon, lat)
    np.testing.assert_array_equal(width, [10, 0, 20])
    np.testing.assert_array_equal(
        segments,
        np.array([[[104.75, 10], [105.5, 10.5]], [[105.5, 10.5], [106.25, 11]], [[106.25, 11], [105.5, 10.5]]]),
    )
    # Zero layer1 remains Overland even with a positive upper-layer width.
    channel, w = read_channel_bifurcations(file, lon, lat)
    np.testing.assert_array_equal(w, [10, 20])
    np.testing.assert_array_equal(channel, segments[[0, 2]])


@pytest.mark.parametrize("overland,expected", [(False, (2, 0)), (True, (2, 1))])
def test_only_panel_b_gets_overland_geometry_and_arrows(paths, overland, expected):
    file, lon, lat = paths
    segments, width = read_bifurcations(file, lon, lat)
    fig, ax = plt.subplots()
    try:
        assert draw_bifurcations(ax, segments, width, EXTENT, [1.2, 1.6, 2, 2.4], include_overland=overland) == expected
        assert len(ax.patches) == sum(expected)
        drawn = [c for c in ax.collections if c.get_label() == "Overland bifurcations"]
        assert bool(drawn) == overland
        if overland:
            np.testing.assert_array_equal(drawn[0].get_segments(), segments[1:2])
            from matplotlib.colors import to_rgba

            np.testing.assert_allclose(drawn[0].get_colors()[0], to_rgba(OVERLAND_COLOR, 0.85))
    finally:
        plt.close(fig)


def test_mismatched_stored_outlet_is_rejected(paths):
    file, lon, lat = paths
    with Dataset(file, "a") as d:
        d.variables["end_lon"][1] = 0
    with pytest.raises(ValueError, match="destination indices"):
        read_bifurcations(file, lon, lat)


def test_mekong_native_path_oracle_and_published_gallery():
    base = ROOT / "map/mekong_15min"
    with Dataset(base / "lonlat.nc") as d:
        lon = np.asarray(d.variables["outlon"][:])
        lat = np.asarray(d.variables["outlat"][:])
    with Dataset(base / "bifprm.nc") as d:
        columns = [np.asarray(d.variables[k][:]) for k in ["ix", "iy", "jx", "jy"]]
        river_width = np.ma.asarray(d.variables["riv_width"][:]).filled(np.nan)
        overland_width = np.ma.asarray(d.variables["ovl_width"][:]).filled(np.nan)
        widths = np.concatenate((river_width[np.newaxis, :], overland_width), axis=0)
    expected = []
    expected_width = []
    seen = set()
    for k, (ix, iy, jx, jy) in enumerate(zip(*columns)):
        if not (
            1 <= ix <= lon.shape[1] and 1 <= jx <= lon.shape[1] and 1 <= iy <= lon.shape[0] and 1 <= jy <= lon.shape[0]
        ):
            continue
        if not np.isfinite(widths[:, k]).all() or (widths[:, k] < 0).any():
            continue
        segment = np.array([[lon[iy - 1, ix - 1], lat[iy - 1, ix - 1]], [lon[jy - 1, jx - 1], lat[jy - 1, jx - 1]]])
        if not np.isfinite(segment).all() or (segment == -9999).any():
            continue
        key = (int(ix), int(iy), int(jx), int(jy))
        if key in seen:
            continue
        seen.add(key)
        expected.append(segment)
        expected_width.append(widths[0, k])
    segments, w = read_bifurcations(base / "bifprm.nc", lon, lat)
    np.testing.assert_array_equal(segments, expected)
    np.testing.assert_array_equal(w, expected_width)
    # Independent reproduction of the established bounding-box extent selection.
    west, east, south, north = EXTENT
    selected = [
        k
        for k, p in enumerate(expected)
        if max(p[:, 0]) >= west and min(p[:, 0]) <= east and max(p[:, 1]) >= south and min(p[:, 1]) <= north
    ]
    assert sum(expected_width[k] > 0 for k in selected) == 14
    assert sum(expected_width[k] == 0 for k in selected) == 77
    figure = ROOT / "visualization/river_map/figure/f04-rivmap_catchment.png"
    published = ROOT / "visualization/gallery/p01-f04-river-map-catchment.png"
    assert hashlib.sha256(figure.read_bytes()).digest() == hashlib.sha256(published.read_bytes()).digest()
    with (ROOT / "visualization/visualization_catalog.csv").open(newline="") as f:
        catalog = {r["visualization_id"]: r for r in csv.DictReader(f)}
    assert "Overland paths" in catalog["p01-f04a"]["method"]
    assert "zero-first-layer-width Overland" in catalog["p01-f04b"]["method"]
    with (ROOT / "visualization/map_explorer/presets.csv").open(newline="") as f:
        presets = {r["gallery_id"]: r for r in csv.DictReader(f)}
    assert presets["p01-f04a"]["channel"] == "true" and presets["p01-f04a"]["overland"] == "false"
    assert presets["p01-f04b"]["channel"] == presets["p01-f04b"]["overland"] == "true"
