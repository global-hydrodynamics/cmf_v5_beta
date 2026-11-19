"""Selection rule, grid/catchment/link consistency and no-click reassessment."""

import json
from pathlib import Path

import numpy as np
import pytest

from app import Explorer
from hires import Tile
from test_v2 import products


@pytest.fixture
def split_assignment(products):
    path = products / "fine/tile.catmxy.bin"
    data = np.fromfile(path, dtype="<i2").reshape(2, 6, 8)
    # Geographic grid A=(ix2,iy1) at this point is assigned to B=(ix1,iy2).
    # Both A and B have their own native pixels elsewhere in this tile.
    data[:, 1, 2] = [1, 2]
    data.tofile(path)
    return products, data


def test_switching_rules_keeps_grid_catchment_and_nextxy_consistent(split_assignment):
    root, data = split_assignment
    app = Explorer(root, root.parent / "exports")
    lon,lat = 11.25,22.25
    info = app.inspect(lon,lat)
    assert app.point_select.disabled and app.point_select.value == "grid"
    assert app.selected == (0,1) and app.selection.native_pixel is None
    assert "assigned coarse ix (1-based)" not in info
    assert info["ix (1-based)"] == 2 and info["downstream ix (1-based)"] == 4
    assert app.selection.coarse_outline[0].tolist() == [[11.,23.],[12.,23.]]
    assert app.selection.boundary is None
    # Old explicit requests/JSON cannot override the effective display mode.
    app.point_select.value = "catchment"
    assert app.point_select.value == "grid" and app.selected == (0,1)
    for mode in ("coarse","catchment","elevtn","flddif","difference","none"):
        app.background.value = mode
        assert app.selected == (0,1) and app.selection.boundary is None
    saved = app.settings(); app.load(json.dumps(saved).encode())
    assert app.selected == (0,1)
    # The fallback native reader remains scientifically correct for explicit tooling.
    extra,assigned = app.scene.inspect(lon,lat,"fine/tile")
    assert assigned == (1,0) and extra["assigned coarse ix (1-based)"] == 1


def test_unassigned_missing_source_and_tile_reassessment(split_assignment):
    root,data = split_assignment
    app = Explorer(root,root.parent/"exports")
    app.inspect(10.25,22.75)
    assert app.selected == (0,0) and app.selection.boundary is None
    app.point_select.value = "catchment"
    assert app.selected == (0,0) and app.point_select.value == "grid"
    assert len(app.selected_coarse_source.data["x0"]) == 4
    # Native unassigned codes never contaminate a Grid selection.
    assert "native hires ix (1-based)" not in app.inspect(10.25,22.75)
    for tile in app.scene.tiles.values():tile.files.pop("catmxy",None)
    app.highres_variable.value = "elevtn"
    assert app.inspect(11.25,22.25)["ix (1-based)"] == 2
    assert app.selected == (0,1) and not app.cell_inspector.pixel_section.visible


def test_coarse_grid_without_assigned_pixels_remains_selected(products):
    app = Explorer(products, products.parent / "exports")
    app.point_select.value = "grid"
    tile = app.scene.tiles["fine/tile"]
    path = products / "sparse.bin"
    data = tile.mmap("catmxy").copy()
    data[:, (data[0] == 2) & (data[1] == 1)] = -9999
    data.tofile(path)
    tile.files["catmxy"] = path
    tile._maps.clear()
    info = app.inspect(11.25, 22.25)
    assert app.selected == (0, 1) and app.selection.boundary is None
    assert "Grid selected" in info["selection status"]
    assert len(app.selected_coarse_source.data["x0"]) == 4


@pytest.mark.parametrize("raster_type", ["coarse", "highres"])
def test_synthetic_export_matches_browser_selection(split_assignment, raster_type, monkeypatch):
    import app as application

    root, data = split_assignment
    explorer = Explorer(root, root.parent / "exports")
    explorer.set_extent(explorer.reader.geometry.extent)  # Compare complete geometry, not viewport-clipped browser runs.
    explorer.raster_type.value = raster_type
    explorer.point_select.value = "grid" if raster_type=="coarse" else "catchment"
    explorer.inspect(11.25, 22.25)
    expected = (0, 1)  # No native COG means automatic Grid for either representation.
    assert explorer.selected == expected
    captured = []
    original = application.export_scene

    def capture(*args, **kwargs):
        captured.append((args[-2], args[-1]))
        return original(*args, **kwargs)

    monkeypatch.setattr(application, "export_scene", capture)
    assert explorer.export().is_file()
    boundary, rectangle = captured[-1]
    for source, segments in [
        (explorer.selection_boundary_source, np.empty((0,2,2)) if boundary is None else boundary.segments),
        (explorer.selected_coarse_source, rectangle),
    ]:
        browser = np.stack(
            [
                np.column_stack([source.data["x0"], source.data["y0"]]),
                np.column_stack([source.data["x1"], source.data["y1"]]),
            ],
            axis=1,
        )
        np.testing.assert_array_equal(browser, segments)


def test_missing_assignment_clears_while_visual_pixels_remain_available(products):
    app = Explorer(products,products.parent/"exports")
    app.raster_type.value = "highres"; app.highres_variable.value = "elevtn"
    app.overlay_controls["channel_pixels"].value = True
    app.inspect(11.25,21.75)
    assert app.point_select.value == "grid" and app.selection.boundary is None
    tile=app.scene.tiles["fine/tile"]
    app.scene.tiles["terrain_only"] = Tile("terrain_only",tile.directory,tile.prefix,tile.geometry,
        {k:p for k,p in tile.files.items() if k!="catmxy"})
    app.hires_source.options=list(app.scene.tiles);app.hires_source.value="terrain_only"
    assert "automatic limits require native catmxy" in app.status.object
    app.background_ui.highres_auto.value=False
    app.highres_low.value,app.highres_high.value=0,50
    app.render_view()
    assert len(app.frame.images)==2 and app.selected==(1,1)
    assert app.selection.native_pixel is None and app.selection.boundary is None
    assert any("no assignment inferred" in m for m in app.frame.diagnostics)
