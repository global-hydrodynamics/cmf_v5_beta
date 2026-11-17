"""All Auto entry paths use legitimate full-reference P5/P95, including presets."""

import json
import numpy as np
import pytest
from app import Explorer
from background_style import highres_layer
from hires import assignment, discover_tiles
from map_layers import make_layer, percentile_limits
from map_reader import MapReader
from test_v2 import products


def test_small_positive_log_minimum_is_preserved():
    values = np.array([0.0001, 0.0002, 0.001, 0.002, 0.01, 0.1])
    expected = np.percentile(values, [5, 95])
    assert percentile_limits(values, True) == pytest.approx(expected)
    assert expected[0] < 0.01
    assert percentile_limits([-1, 0, 1, 10], True)[0] == 0.01
    with pytest.raises(ValueError, match="logarithmic"):
        percentile_limits([-10, -5, -1, 0], True)


@pytest.mark.parametrize("mode", ["elevtn", "flddif", "difference", "catchment"])
@pytest.mark.parametrize("policy", ["percentile", "gallery"])
def test_auto_masks_all_invalid_assignment_pairs_and_preserves_manual(products, mode, policy):
    tilepath = products / "fine/tile.catmxy.bin"
    codes = np.fromfile(tilepath, dtype="<i2").reshape(2, 6, 8).copy()
    codes[:, 0, 0] = [-999, -999]  # unassigned land
    codes[:, 0, 1] = [-9999, -9999]  # sea/missing
    codes[:, 0, 2] = [1, 99]  # positive x alone is not a valid assignment
    codes[:, 0, 3] = [0, 1]
    codes[:, 0, 4] = [99, 1]
    codes.tofile(tilepath)
    elevation = np.arange(48, dtype="<f4").reshape(6, 8) + 1
    elevation[0, :5] = 1e8  # excluded pixels cannot dominate Auto statistics
    elevation.tofile(products / "fine/tile.elevtn.bin")
    elevation.tofile(products / "fine/tile.flddif.bin")
    r = MapReader(products)
    t = discover_tiles(products, [])["fine/tile"]
    valid, _, _ = assignment(*codes, r.geometry)
    coarse = make_layer(r, "uparea")
    if mode == "catchment":
        source = r.read("uparea").astype(float).filled(np.nan) * 1e-6
        reference = source[codes[1][valid] - 1, codes[0][valid] - 1]
    else:
        reference = t.sample(mode, np.arange(6), np.arange(8))[valid]
    expected = np.percentile(reference[np.isfinite(reference)], [5, 95])
    result = highres_layer(np.ones((1, 1)), r, t, mode, "uparea", coarse, reference_policy=policy)
    # Constant terrain differences retain the existing small Linear display expansion.
    from map_layers import resolve_color_limits

    log = mode == "catchment"
    assert (result.low, result.high) == pytest.approx(resolve_color_limits(*expected, log))
    manual = highres_layer(
        np.ones((1, 1)), r, t, mode, "uparea", coarse, dict(scale="log", limits=[0.001, 999]), reference_policy=policy
    )
    assert (manual.low, manual.high) == (0.001, 999)


def test_preset_and_old_json_no_longer_force_uparea_minimum(products):
    raw = np.arange(1, 13, dtype="<f4").reshape(3, 4) * 1e6
    raw.tofile(products / "uparea.bin")
    (products / "nextxy_noedge.bin").write_bytes((products / "nextxy.bin").read_bytes())
    app = Explorer(products, products.parent / "exports")
    app.apply_preset("p01-f04b")
    t = app.scene.tiles[app.hires_source.value]
    x, y = t.mmap("catmxy")
    mask, _, _ = assignment(x, y, app.reader.geometry)
    reference = raw[y[mask] - 1, x[mask] - 1].astype(float) * 1e-6
    expected = np.percentile(reference, [5, 95])
    assert (app.frame.layer.low, app.frame.layer.high) == pytest.approx(expected)
    assert app.frame.layer.low > 0.01
    extent = app.extent
    old = app.settings()
    old["layers"].pop("auto_limits_policy")
    app.load(json.dumps(old).encode())
    assert (app.frame.layer.low, app.frame.layer.high) == pytest.approx(expected)
    app.set_extent((11, 12, 21, 22))
    assert (app.frame.layer.low, app.frame.layer.high) == pytest.approx(expected)
    assert app.extent != extent
    # Browser and PNG compose the same physical limits from the same options.
    frame = app.scene.build(app.extent, app.variable.value, app.layer, app.network, app.scene_options(), max_side=2400)
    assert (frame.layer.low, frame.layer.high) == pytest.approx(expected)
