"""Native assignment geometry, preset contracts and persistent Explorer state."""

import csv
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from bokeh.document import Document
from bokeh.models import TapTool
from PIL import Image

from app import Explorer
from hires import Tile
from map_reader import Geometry
from presets import PresetLibrary
from selection import CatchmentIndex
from test_v2 import products


def native_tile(tmp_path, mask):
    ny, nx = mask.shape
    data = np.full((2, ny, nx), 2, dtype="<i2")
    data[:, mask] = 1
    path = tmp_path / "assignment.bin"
    data.tofile(path)
    geometry = Geometry(nx, ny, 1, 0.25, 10, 10 + nx * 0.25, 23 - ny * 0.25, 23)
    return Tile("test", tmp_path, "test", geometry, {"catmxy": path})


def elementary_edges(segments, geometry):
    """Expand rendered runs into native unit edges for independent comparison."""
    edges = set()
    for a, b in segments:
        x0, y0 = np.rint(
            [(a[0] - geometry.west) / geometry.resolution, (geometry.north - a[1]) / geometry.resolution]
        ).astype(int)
        x1, y1 = np.rint(
            [(b[0] - geometry.west) / geometry.resolution, (geometry.north - b[1]) / geometry.resolution]
        ).astype(int)
        if y0 == y1:
            edges.update(("h", y0, x) for x in range(min(x0, x1), max(x0, x1)))
        else:
            assert x0 == x1
            edges.update(("v", x0, y) for y in range(min(y0, y1), max(y0, y1)))
    return edges


def expected_edges(mask):
    # Set symmetric difference cancels shared pixel sides independently of
    # extraction algorithm; holes, islands and outside-tile edges remain.
    edges = set()
    for row, col in zip(*np.where(mask)):
        edges.symmetric_difference_update({("h", row, col), ("h", row + 1, col), ("v", col, row), ("v", col + 1, row)})
    return edges


MASKS = [
    [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
    [[1, 1, 1, 1, 1], [1, 1, 1, 1, 1]],  # crosses computational cell edges
    [[0, 1, 0, 0], [1, 1, 1, 0], [0, 0, 1, 1]],
    [[1, 1, 1], [1, 0, 1], [1, 1, 1]],  # hole
    [[1, 0, 0, 1], [0, 0, 0, 0], [1, 0, 1, 1]],  # disconnected components
    [[1, 1, 0], [1, 0, 0], [1, 1, 1]],  # true tile borders
]


@pytest.mark.parametrize("values", MASKS)
@pytest.mark.parametrize("block_pixels", [3, 500000])
def test_native_boundary_topology_and_block_halos(tmp_path, values, block_pixels):
    mask = np.array(values, dtype=bool)
    tile = native_tile(tmp_path, mask)
    coarse = Geometry(4, 3, 1, 1, 10, 14, 20, 23)
    index = CatchmentIndex(tile, coarse, block_pixels=block_pixels)
    boundary = index.boundary(0, 0)
    assert boundary.pixel_count == mask.sum()
    assert elementary_edges(boundary.segments, tile.geometry) == expected_edges(mask)
    assert index.boundary(0, 0) is boundary  # reused without tile scan
    assert not boundary.segments.flags.writeable


def test_native_assignment_clicks_and_persistent_selection(products):
    # An irregular assignment crosses coarse cells; two neighboring assignments
    # share similar display values. Rendering is deliberately downsampled.
    path = products / "fine/tile.catmxy.bin"
    a = np.fromfile(path, dtype="<i2").reshape(2, 6, 8)
    a[:, 2:5, 1:5] = 1
    a[:, 3, 2] = 2  # hole
    a[:, 5, 7] = 1  # disconnected component outside test viewport
    a[0, 0, 2], a[1, 0, 2] = 1, -999  # invalid mixed pair
    a.tofile(path)
    app = Explorer(products, products.parent / "exports-v3")
    app.background.value = "catchment"
    tile = app.scene.tiles["fine/tile"]
    app.scene.build(app.extent, app.variable.value, app.layer, app.network, app.scene_options(), max_side=2)
    info = app.inspect(11.000001, 21.999999)
    assert app.selection.native_pixel == (2, 2)
    assert app.selected == (0, 0)  # geographic cell is (1,1), not assignment
    mask = (a[0] == 1) & (a[1] == 1)
    assert info["unit catchment assigned pixel count"] == mask.sum()
    boundary = app.selection.boundary
    assert elementary_edges(boundary.segments, tile.geometry) == expected_edges(mask)
    assert app.inspect(10.999999, 21.999999)["assigned coarse ix (1-based)"] == 1
    boundary = app.selection.boundary
    app.set_extent((10.5, 12, 20.5, 22))
    app.terrain_palette.value = "pale_terrain"
    app.overlay_controls["catchment_boundaries"].value = False
    app.representation.value = "outlet_vector"
    assert app.selection.boundary is boundary
    assert boundary.pixel_count == mask.sum()  # includes off-screen component
    assert len(app.selection_boundary_source.data["x0"]) > 0
    for lon, lat, code in [(10.25, 22.75, -999), (10.75, 22.75, -9999), (11.25, 22.75, 1)]:
        info = app.inspect(lon, lat)
        assert info["assigned coarse ix (1-based)"] == code
        assert app.selected is None and app.selection.boundary is None
        assert not len(app.selection_boundary_source.data["x0"])
        assert "ix (1-based)" not in info  # no containing-cell fallback
    app.background.value = "coarse"
    app.inspect(11.25, 21.75)
    assert app.selected == (1, 1) and app.selection.boundary is None
    app.background.value = "elevtn"
    app.inspect(11.25, 21.75)
    assert app.selection.kind == "terrain" and app.selection.boundary is None


def test_presets_catalog_missing_inputs_and_atomic_application(map_dir):
    library = PresetLibrary()
    assert len(library.presets) == 11 and not library.messages
    app = Explorer(map_dir, map_dir.parent / "exports")
    before = app.settings()
    missing = library.missing_products("p01-f04b", app.reader, app.scene)
    assert any("catmxy" in name for name in missing)
    assert "nextxy_noedge" in missing
    with pytest.raises(ValueError, match="missing"):
        app.apply_preset("p01-f04b")
    assert app.settings() == before
    app.set_extent((11, 13, 21, 22))
    app.apply_preset("p01-f01a")
    assert app.extent == (11, 13, 21, 22) and app.palette.value == "YlGnBu"
    assert app.settings()["version"] == 2
    app.palette.value = "magma"
    assert "Custom (modified" in app.preset_status.object
    before = app.settings()
    with pytest.raises(ValueError):
        app.apply_preset("p01-f01a", True)  # Gallery extent outside small fixture
    assert app.settings() == before


def test_persistent_layout_and_json_compatibility(products):
    app = Explorer(products, products.parent / "exports")
    document = Document()
    root = app.view.get_root(document)
    document.add_root(root)
    plot = app.plot
    for active in range(len(app.right_tabs)):
        app.right_tabs.active = active
        app.render_view()
        assert app.plot is plot and plot.document is document
    assert app.plot.select_one(TapTool).renderers == [app.raster]
    assert app.settings_panel.styles["overflow-y"] == "auto"
    assert app.map_region in app.content.objects
    for version in (1, 2):
        state = app.settings()
        state["version"] = version
        if version == 1:
            state.pop("layers")
        app.load(json.dumps(state).encode())
        assert app.plot is plot
    document.remove_root(root)


ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.skipif(not (ROOT / "map/mekong_15min/params.txt").exists(), reason="Mekong map not beside app")
def test_mekong_presets_native_outline_and_png(tmp_path):
    app = Explorer(ROOT / "map/mekong_15min", tmp_path)
    plot = app.plot
    for identity in app.preset_library.presets:
        assert not app.preset_library.missing_products(identity, app.reader, app.scene)
        expected = app.apply_preset(identity)
        assert app.settings() == expected
        assert app.plot is plot and "Error" not in app.status.object
    app.apply_preset("p01-f04a", True)
    tile = app.scene.tiles[app.hires_source.value]
    data = tile.mmap("catmxy")
    # These physical locations and native assignments are independently checked;
    # at least one catchment extends beyond its computational geographic cell.
    crossing = False
    for lon, lat in [(105.5, 10.5), (106.0, 11.0), (105.8, 10.8)]:
        rr, cc = tile.geometry.cell(lon, lat)
        x, y = map(int, data[:, rr, cc])
        assert 1 <= x <= app.reader.geometry.nx and 1 <= y <= app.reader.geometry.ny
        info = app.inspect(lon, lat)
        assert app.selected == (y - 1, x - 1)
        mask = (data[0] == x) & (data[1] == y)
        assert info["unit catchment assigned pixel count"] == np.count_nonzero(mask)
        boundary = app.selection.boundary
        assert elementary_edges(boundary.segments, tile.geometry) == expected_edges(mask)
        r0, r1, c0, c1 = boundary.bounds
        g = app.reader.geometry
        crossing |= (
            tile.geometry.west + c0 * tile.geometry.resolution < g.west + (x - 1) * g.resolution
            or tile.geometry.west + c1 * tile.geometry.resolution > g.west + x * g.resolution
            or tile.geometry.north - r0 * tile.geometry.resolution > g.north - (y - 1) * g.resolution
            or tile.geometry.north - r1 * tile.geometry.resolution < g.north - y * g.resolution
        )
    assert crossing
    saved = app.selection.boundary
    app.apply_preset("p01-f04b")
    app.representation.value = "grid_center"
    app.representation.value = "outlet_vector"
    assert app.selection.boundary is saved
    path = app.export()
    with Image.open(path) as image:
        rgb = np.array(image.convert("RGB")).astype(int)
        assert ((rgb[:, :, 0] > 180) & (rgb[:, :, 1] < 30) & ((rgb[:, :, 2] > 130) & (rgb[:, :, 2] < 200))).sum() > 20


def test_source_change_clears_old_outline(products):
    app = Explorer(products, products.parent / "exports")
    app.background.value = "catchment"
    app.inspect(11.25, 21.75)
    assert app.selection.boundary is not None
    original = app.scene.tiles["fine/tile"]
    app.scene.tiles["another/tile"] = Tile(
        "another/tile", original.directory, original.prefix, original.geometry, original.files
    )
    app.hires_source.options = list(app.scene.tiles)
    app.hires_source.value = "another/tile"
    assert app.selection.boundary is None and app.selected is None
    assert "source changed" in app.selection_summary.object


def test_invalid_preset_metadata_is_diagnostic(tmp_path):
    library = PresetLibrary()
    original = Path(__file__).resolve().parents[1] / "presets.csv"
    bad = tmp_path / "presets.csv"
    bad.write_text(original.read_text().replace("p01-f01a,", "unknown-figure,", 1))
    invalid = PresetLibrary(bad, library.catalog_path)
    assert not invalid.presets and "Gallery reference" in invalid.messages[0]
    absent = PresetLibrary(catalog_path=tmp_path / "absent.csv")
    assert not absent.presets and absent.messages
