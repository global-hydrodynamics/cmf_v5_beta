"""Scientific populations and persistent Inspector/navigation contracts.

Detect wrong weighting, post-Log filtering, stale outlet attributes and widget
replacement; small native fixtures give independent numerical expectations.
"""

import json
import numpy as np
import pytest
from app import Explorer
from hires import assignment, discover_tiles
from map_reader import MapReader
from map_layers import make_layer, percentile_limits
from background_style import highres_layer
from test_v2 import products
from test_selection_modes import split_assignment


def test_persistent_modes_and_connectivity(split_assignment):
    root, _ = split_assignment
    a = Explorer(root, root.parent / "exports")
    p = a.cell_inspector
    assert a.panel_mode.value == "Visualization" and a.visualization_panel.visible and not a.inspector_panel.visible
    assert len(a.right_tabs) == 4
    assert p.connectivity_section.active == []
    a.right_tabs.active = 2
    a.show_osm.value = True
    a.osm_opacity.value = 35
    a.overlay_controls["catchment_boundaries"].value = True
    a.inspect(11.25, 22.25)
    plot = a.plot
    state = a.selection
    extent = a.extent
    saved = a.settings()
    a.panel_mode.value = "Inspector"
    p.connectivity_section.active = [0]
    p.pixel_section.active = [0]
    assert a.inspector_panel.visible and not a.visualization_panel.visible
    a.panel_mode.value = "Visualization"
    assert a.plot is plot and a.selection is state and a.extent == extent and a.settings() == saved
    a.inspect(12.25, 21.25)  # still in Visualization, Inspector updates while hidden
    assert a.panel_mode.value == "Visualization" and a.selection is not state
    a.panel_mode.value = "Inspector"
    assert a.right_tabs.active == 2 and p.connectivity_section.active == [0] and p.pixel_section.active == [0]
    assert "High-res ix" in p.pixel.object and "High-res catmx" in p.pixel.object
    for removed in ("Native", "fldhgt", "Assignment status"):
        assert removed not in p.pixel.object
    assert "Assigned Unit Catchment uparea" in p.pixel.object
    p.connectivity_section.active = []
    a.inspect(10.25, 22.75)
    assert p.connectivity_section.active == [] and a.selected is None
    assert "No mapped river cell" in a.selection_summary.object and "798" not in a.selection_summary.object


def test_summary_from_selected_stored_outlet(split_assignment):
    root, codes = split_assignment
    a = Explorer(root, root.parent / "exports")
    data = a.inspect(11.25, 22.25)
    assert a.selected == (1, 0)
    text = a.selection_summary.object
    assert "Selected Unit Catchment" in text and "ix=1, iy=2" in text
    assert "10.60000" in text and "21.40000" in text  # stored, not click or grid center
    assert "Upstream Area" in text and "4 km²" in text and "catmxy assignment" in text
    assert f"{np.count_nonzero((codes[0]==1)&(codes[1]==2)):,} high-res pixels" in text
    assert "orange" not in text
    a.point_select.value = "grid"
    text = a.selection_summary.object
    assert "Selected Grid" in text and "ix=2, iy=1" in text and "geographic containment" in text
    assert "11.60000" in text and "22.40000" in text and "2 km²" in text
    assert data["assigned coarse ix (1-based)"] == 1


def test_coarse_p5_p95_before_log_mask_and_manual(map_dir):
    raw = np.array([[-2, -1, 0, 0.005], [1, 2, 3, 4], [5, 10, 100, -0.009999]], dtype="<f4") * 1e6
    raw[-1, -1] = -9999
    raw.tofile(map_dir / "uparea.bin")
    before = (map_dir / "uparea.bin").read_bytes()
    r = MapReader(map_dir)
    values = raw.astype(float).ravel()[:-1] * 1e-6
    expected = np.percentile(values, [5, 95])
    linear = make_layer(r, "uparea", "linear", "gray")
    assert (linear.low, linear.high) == pytest.approx(expected)
    log = make_layer(r, "uparea", "log", "gray")
    assert (log.low, log.high) == pytest.approx((0.01, expected[1]))
    assert np.isnan(log.image[raw <= 0]).all() and log.image[0, 3] == 0.01
    manual = make_layer(r, "uparea", "log", "gray", limits=[0.001, 4])
    assert (manual.low, manual.high) == (0.001, 4)
    with pytest.raises(ValueError, match="logarithmic"):
        make_layer(r, "uparea", "log", limits=[-1, 4])
    with pytest.raises(ValueError, match="logarithmic"):
        percentile_limits([-10, -5, 0, 0], True)
    a = Explorer(map_dir, map_dir.parent / "exports")
    a.auto_limits.value = False
    a.low.value = -1
    assert a.low.value == -1 and not a.image_source.data["image"]
    a._guard(a.update_network)
    assert not a.image_source.data["image"]
    with pytest.raises(ValueError, match="logarithmic"):
        a.export()  # a failed update must not export the preceding valid layer
    a.low.value = 0.001
    assert a.export().is_file()
    assert (map_dir / "uparea.bin").read_bytes() == before


def test_pixel_weighted_inherited_population(products):
    root = products
    values = np.full((3, 4), 1e12, dtype="<f4")
    values[0, :3] = [1e6, 100e6, 0]
    values.tofile(root / "uparea.bin")
    codes = np.ones((2, 6, 8), dtype="<i2")
    codes[0].flat[-6:-2] = 2
    codes[0].flat[-3:] = 3
    codes[:, 0, 0] = -999
    codes[:, 0, 1] = [99, 1]
    codes.tofile(root / "fine/tile.catmxy.bin")
    r = MapReader(root)
    tile = discover_tiles(root, [])["fine/tile"]
    valid, _, _ = assignment(*codes, r.geometry)
    inherited = r.read("uparea").astype(float).filled(np.nan) * 1e-6
    reference = inherited[codes[1][valid] - 1, codes[0][valid] - 1]
    expected = np.percentile(reference, [5, 95])
    low, high = tile.percentiles("uparea", inherited=inherited)
    assert (low, high) == pytest.approx(expected)
    assert low == .25 and high == 75.25
    layer = highres_layer(
        np.array([[0.0, 1.0, 100.0]]), r, tile, "catchment", "uparea", make_layer(r, "uparea"), dict(scale="log")
    )
    assert (layer.low, layer.high) == (.25, 75.25) and np.isnan(layer.image[0, 0])
    assert len(tile._stats) == 1  # same finite population reused across Log/Linear
    assert high < inherited.max()  # unassigned coarse cells must not contribute


def test_gallery_legacy_policy_and_json(products):
    (products / "nextxy_noedge.bin").write_bytes((products / "nextxy.bin").read_bytes())
    a = Explorer(products, products.parent / "exports")
    assert a.auto_limits_policy == "percentile"
    initial = a.settings()
    a.load(json.dumps(initial).encode())
    assert a.auto_limits_policy == "percentile"
    initial["layers"].pop("auto_limits_policy")
    a.load(json.dumps(initial).encode())
    assert a.auto_limits_policy == "gallery"
    a.apply_preset("p01-f04b")
    assert a.auto_limits_policy == "gallery"
    legacy = (a.frame.layer.low, a.frame.layer.high)
    tile = a.scene.tiles[a.hires_source.value]
    x, y = tile.mmap("catmxy")
    mask, _, _ = assignment(x, y, a.reader.geometry)
    source = a.reader.read("uparea").astype(float).filled(np.nan) * 1e-6
    reference = source[y[mask] - 1, x[mask] - 1]
    expected_auto = np.percentile(reference[np.isfinite(reference)], [5, 95])
    assert legacy == pytest.approx((expected_auto[0] if expected_auto[0] > 0 else .01, expected_auto[1]))

    a.highres_scale.value = "linear"
    tile = a.scene.tiles[a.hires_source.value]
    x, y = tile.mmap("catmxy")
    mask, _, _ = assignment(x, y, a.reader.geometry)
    source = a.reader.read("uparea").astype(float).filled(np.nan) * 1e-6
    reference = source[y[mask] - 1, x[mask] - 1]
    expected = np.percentile(reference[np.isfinite(reference)], [5, 95])
    assert (a.frame.layer.low, a.frame.layer.high) == pytest.approx(expected)
    frame = a.scene.build(a.reader.geometry.extent, a.variable.value, a.layer, a.network, a.scene_options())
    assert frame.layer.image[0, 6] == 0  # explicit Linear retains legitimate zero-uparea assignments
    bad = a.settings()
    bad["layers"]["auto_limits_policy"] = "bogus"
    with pytest.raises(ValueError, match="policy"):
        a.load(json.dumps(bad).encode())


def test_summary_missing_values_and_unassigned_mode(map_dir):
    raw = np.fromfile(map_dir / "uparea.bin", dtype="<f4").reshape(3, 4)
    raw[1, 1] = -9999
    raw.tofile(map_dir / "uparea.bin")
    a = Explorer(map_dir, map_dir.parent / "exports")
    a.inspect(11.25, 21.75)
    text = a.selection_summary.object
    assert "Selected Grid" in text and "Outlet (lat, lon):** Unavailable, Unavailable" in text
    assert "Upstream Area:** Unavailable" in text
    a.point_select.value = "catchment"
    assert a.selected is None and "No mapped river cell" in a.selection_summary.object
    assert "Selected Grid" not in a.selection_summary.object
