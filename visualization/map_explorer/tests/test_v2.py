"""CaMa-Flood-specific high-resolution, topology, layering and Gallery contracts."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
from netCDF4 import Dataset

from app import Explorer
from conftest import write_network
from hires import assignment, catchment_edges, discover_tiles, neighbor_difference
from map_products import Products, area_style
from map_reader import MapReader
from river_network import RiverNetwork
from scene import Scene


@pytest.fixture
def products(map_dir):
    # Fine pixels are 0.5-degree cells assigned to a 1-degree coarse grid.
    d = map_dir / "fine"
    d.mkdir()
    (d / "location.txt").write_text("1 narea\narea name west east south north nx ny step\n1 tile 10 14 20 23 8 6 0.5\n")
    x = np.tile(np.repeat(np.arange(1, 5), 2), (6, 1)).astype("<i2")
    y = np.repeat(np.arange(1, 4), 2)[:, None] * np.ones((1, 8), dtype="<i2")
    y = y.astype("<i2")
    x[0, 0] = y[0, 0] = -999
    x[0, 1] = y[0, 1] = -9999
    np.stack([x, y]).tofile(d / "tile.catmxy.bin")
    elev = np.arange(48, dtype="<f4").reshape(6, 8) - 5
    elev[0, 1] = -9999
    elev.tofile(d / "tile.elevtn.bin")
    fld = elev.copy()
    fld[0, 0] = -9999
    fld.tofile(d / "tile.flddif.bin")
    visual = np.full((6, 8), -9, dtype="i1")
    visual[1, 0] = 10
    visual[1, 1] = 7
    visual.tofile(d / "tile.visual.bin")
    write_network(map_dir)
    nc = map_dir / "netcdf"
    nc.mkdir(exist_ok=True)
    with Dataset(nc / "lonlat.nc", "w") as ds:
        ds.createDimension("lon", 4)
        ds.createDimension("lat", 3)
        ds.createVariable("lon", "f8", ("lon",))[:] = np.arange(4) + 10.5
        ds.createVariable("lat", "f8", ("lat",))[:] = 22.5 - np.arange(3)
        for name, data, units in [
            ("outlon", np.tile(np.arange(4) + 10.6, (3, 1)), "degrees_east"),
            ("outlat", np.tile((22.4 - np.arange(3))[:, None], (1, 4)), "degrees_north"),
        ]:
            v = ds.createVariable(name, "f4", ("lat", "lon"))
            v.units = units
            v[:] = data
    with Dataset(nc / "bifprm.nc", "w") as ds:
        ds.createDimension("path", 5)
        ds.createDimension("layer", 2)
        for name, values in [
            ("ix", [1, 2, 1, 8, 1]),
            ("iy", [1, 1, 1, 1, 1]),
            ("jx", [2, 4, 2, 1, 3]),
            ("jy", [1, 3, 1, 1, 1]),
        ]:
            ds.createVariable(name, "i4", ("path",))[:] = values
        v = ds.createVariable("width", "f4", ("layer", "path"))
        v.units = "m"
        v[:] = [[10, 0, 20, 3, -9999], [12, 8, 21, 4, 4]]
    return map_dir


def test_location_orientation_and_assignment(products):
    r = MapReader(products)
    messages = []
    tiles = discover_tiles(products, messages)
    t = tiles["fine/tile"]
    assert (t.geometry.nx, t.geometry.ny) == (8, 6)
    x, y = t.sample("catmxy", np.array([0, 5]), np.array([0, 1, 7]))
    assert x[1, 2] == 4 and y[1, 2] == 3
    valid, land, invalid = assignment(x, y, r.geometry)
    assert land[0, 0] and not valid[0, 1] and not invalid.any()
    _, _, invalid = assignment(np.array([1, 99]), np.array([-999, 2]), r.geometry)
    assert invalid.all()
    assert t.sample("visual", np.array([1]), np.array([0, 1]))[0].tolist() == [10, 7]
    assert t.sample("elevtn", np.array([0]), np.array([0]))[0, 0] == -5


def test_neighbor_metric_uses_native_halo_not_sample_spacing(products):
    t = discover_tiles(products, [])["fine/tile"]
    full = t.sample("elevtn", np.arange(6), np.arange(8))
    expected = neighbor_difference(full).filled(np.nan)
    actual = t.sample("difference", np.array([0, 3, 5]), np.array([0, 4, 7]))
    np.testing.assert_array_equal(actual, expected[np.ix_([0, 3, 5], [0, 4, 7])])
    assert np.isnan(expected[0, 1]) and expected[0, 0] == 9  # includes diagonal neighbor


def test_percentiles_full_tile_and_missing_floodplain_fill(products):
    app = Explorer(products, products.parent / "exports")
    app.background.value = "flddif"
    t = app.scene.tiles["fine/tile"]
    full = t.sample("flddif", np.arange(6), np.arange(8))
    expected = np.percentile(full[np.isfinite(full)], (3, 97))
    np.testing.assert_allclose(t.percentiles("flddif"), expected)
    rgba = app.frame.images[0][0]
    assert rgba[0, 0] != np.uint32(0xFFFFFFFF)  # missing flddif, valid elevtn: neutral
    assert rgba[0, 1] == np.uint32(0xFFFFFFFF)  # both missing: white
    limits = t.percentiles("flddif")
    app.set_extent((11, 12, 21, 22))
    assert app.frame.layer.low == limits[0] and app.frame.layer.high == limits[1]


def test_pair_boundaries_ignore_equal_display_values():
    x = np.array([[1, 1], [1, 1]])
    y = np.array([[1, 2], [1, 2]])
    v = np.ones((2, 2), bool)
    edges = catchment_edges(x, y, v, (10, 12, 20, 22))
    assert len(edges) == 2
    np.testing.assert_array_equal(edges[:, :, 0], 11)


def test_outlet_geometry_and_bifurcation_validation(products):
    r = MapReader(products)
    p = Products(r)
    net = RiverNetwork(r)
    vector = p.network_view(net, "outlet_vector")
    assert not np.array_equal(vector.x0, net.x0)
    np.testing.assert_allclose(vector.x0[0], 10.6, atol=1e-6)
    np.testing.assert_array_equal(vector.nextx, net.nextx)
    bif = p.bifurcations
    assert bif["channel"].tolist() == [True, False]
    assert bif["stats"] == dict(
        invalid_indices=1, invalid_widths=1, invalid_outlets=0, duplicates=1, conflicting_duplicates=1
    )
    np.testing.assert_array_equal(bif["first_width"], [10, 0])
    assert p.network_view(net, "outlet_vector") is vector


def test_area_classes_are_full_network_and_styles_independent(products):
    r = MapReader(products)
    n = RiverNetwork(r)
    all_ids = n.visible(r.geometry.extent)
    widths, colors, labels, swatches = area_style(
        n, r, all_ids, classification="quartiles", scale_width=True, color_area=False, distinguish=False
    )
    assert len(set(colors)) == 1 and len(set(widths)) > 1
    small = n.visible((11.8, 12.2, 21.4, 21.6))
    w, c, l, _ = area_style(
        n, r, small, classification="quartiles", scale_width=True, color_area=False, distinguish=False
    )
    assert l == labels
    np.testing.assert_array_equal(w, widths[np.searchsorted(all_ids, small)])
    w, c, _, _ = area_style(n, r, all_ids, classification="six_log", color_area=True, scale_width=False)
    assert len(set(w)) == 1 and len(set(c)) > 1


def test_layer_combinations_inspection_and_v1_v2_settings(products):
    app = Explorer(products, products.parent / "exports")
    app.representation.value = "outlet_vector"
    app.background.value = "catchment"
    app.overlay_controls["overland"].value = True
    app.overlay_controls["outlets"].value = True
    app.overlay_controls["headwater"].value = True
    app.overlay_controls["catchment_boundaries"].value = True
    app.overlay_controls["channel_pixels"].value = True
    app.overlay_controls["coarse_grid"].value = True
    app.arrows.value = True
    assert len(app.frame.images) == 2 and len(app.frame.overlays) >= 4
    assert (app.frame.images[1][0] != 0).any()  # independent transparent channel-pixel image
    assert len(app.frame.points) > 0 and len(app.frame.arrows["x"]) > 0
    info = app.inspect(10.75, 22.25)
    assert "assignment status" in info and "derived max 8-neighbor elevation difference [m], NOT slope" in info
    assert app.export().is_file()
    old_extent = app.extent
    data = app.settings()
    app.background.value = "none"
    assert not app.frame.images and len(app.frame.main["x0"]) > 0
    app.load(json.dumps(data).encode())
    assert app.background.value == "catchment" and app.extent == old_extent
    data["version"] = 1
    data.pop("layers")
    data["network_options"].pop("classification")
    app.load(json.dumps(data).encode())
    assert (
        app.background.value == "coarse"
        and app.representation.value == "grid_center"
        and app.classification.value == "fixed"
    )
    data = app.settings()
    data["layers"]["future_option"] = 42
    with pytest.warns(UserWarning, match="Ignored"):
        app.load(json.dumps(data).encode())


def test_missing_optional_products_and_malformed_tile(map_dir):
    messages = []
    d = map_dir / "bad"
    d.mkdir()
    (d / "location.txt").write_text("1\nheader\n1 bad 0 1 0 1 2 2 .1\n")
    assert not discover_tiles(map_dir, messages) and messages
    a = Explorer(map_dir, map_dir.parent / "exports")
    a.background.value = "none"
    a.network_choice.value = "off"
    assert not a.frame.images and not len(a.frame.main["x0"])


def test_navigation_uses_complete_event_before_range_property_patches(map_dir):
    from types import SimpleNamespace

    a = Explorer(map_dir, map_dir.parent / "exports")
    a._navigation(SimpleNamespace(x0=11, x1=13, y0=21, y1=22))
    assert a.extent == (11, 13, 21, 22)


def test_native_centroid_and_sampled_boundaries(products):
    a = Explorer(products, products.parent / "exports")
    tile = a.scene.tiles["fine/tile"]
    g = a.reader.geometry
    river = a.reader.read("uparea").astype(float).filled(np.nan) > 0
    lon, lat, count = tile.centroids(g, river)
    # Coarse cell (1,1) has two assigned lower-row pixels after the two
    # upper pixels were explicitly marked unassigned land / missing.
    assert count[0] == 2
    assert lon[0] == 10.5 and lat[0] == 22.25
    a.background.value = "catchment"
    a.overlay_controls["catchment_boundaries"].value = True
    frame = a.scene.build(g.extent, "uparea", a.layer, a.network, a.scene_options(), max_side=2)
    assert any("sampled view" in message for message in frame.diagnostics)
    assert not any("assignment boundaries" in label for segments, color, width, label, dash in frame.overlays)


ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.skipif(not (ROOT / "map/mekong_15min/params.txt").exists(), reason="actual Mekong fixture absent")
def test_mekong_gallery_numerical_and_multilayer_integration(tmp_path, monkeypatch):
    from time import perf_counter

    gallery = ROOT / "visualization/river_map/script"
    monkeypatch.syspath_prepend(str(gallery))
    monkeypatch.syspath_prepend(str(ROOT / "visualization/cmf_colormap/src"))

    def module(filename, name):
        spec = importlib.util.spec_from_file_location(name, gallery / filename)
        result = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(result)
        return result

    f03 = module("f03a-vector_river_map-upstream_area.py", "gallery03_reference")
    f03b = module("f03b-vector_river_map-extended_network.py", "gallery03b_reference")
    f05 = module("f05_river_background.py", "gallery05_reference")
    root = ROOT / "map/mekong_15min"
    start = perf_counter()
    a = Explorer(root, tmp_path)
    a.set_extent((104.5, 107, 9.5, 12))
    a.representation.value = "outlet_vector"
    reference = f03.read_network(
        root / "netcdf/uparea.nc", root / "netcdf/nextxy.nc", root / "netcdf/lonlat.nc", root / "params.txt"
    )
    np.testing.assert_array_equal(a.network.x0, reference[1])
    np.testing.assert_array_equal(a.network.y1, reference[4])
    area = a.reader.read("uparea")[a.network.rows, a.network.cols].astype(float).filled(np.nan) * 1e-6
    np.testing.assert_array_equal(np.digitize(np.log10(area), reference[7]), reference[6])
    actual = a.scene.products.bifurcations
    segments, widths, invalid = f03b.read_bifurcations(root / "netcdf/bifprm.nc", *a.scene.products.outlets)
    np.testing.assert_array_equal(actual["segments"], segments)
    np.testing.assert_array_equal(actual["first_width"], widths)
    a.background.value = "catchment"
    a.color_mode.value = "upstream_area"
    a.width_mode.value = "upstream_area"
    a.overlay_controls["channel_pixels"].value = True
    a.overlay_controls["catchment_boundaries"].value = True
    a.overlay_controls["overland"].value = True
    a.overlay_controls["headwater"].value = True
    a.overlay_controls["outlets"].value = True
    assert a.export().is_file()
    tile = a.scene.tiles[a.hires_source.value]
    elevation = tile.sample("elevtn", np.arange(tile.geometry.ny), np.arange(tile.geometry.nx))
    baseline = f05.maximum_neighbor_elevation_difference(np.ma.masked_invalid(elevation)).filled(np.nan)
    rows = np.array([0, 600, 1000, 1799])
    cols = np.array([0, 500, 900, 1199])
    np.testing.assert_array_equal(tile.sample("difference", rows, cols), baseline[np.ix_(rows, cols)])
    for mode in ("elevtn", "difference", "flddif"):
        a.background.value = mode
        a.terrain_palette.value = "pale_terrain"
        assert a.frame.layer is not None and "Error" not in a.status.object
    assert a.export().is_file()
    print(
        f'Mekong full integration: {perf_counter()-start:.3f}s; {len(a.network.rows)} links; {actual["channel"].sum()} channel bifurcations'
    )
