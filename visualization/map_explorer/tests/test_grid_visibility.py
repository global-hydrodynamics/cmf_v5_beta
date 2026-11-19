"""Native grid edges are all-or-none, never an adaptive degree/decimated mesh."""
from types import SimpleNamespace

import numpy as np
import pytest
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection

from app import Explorer
from map_reader import Geometry
from scene import Frame, Scene


@pytest.mark.parametrize("columns,rows,shown", [(29, 29, True), (30, 29, False),
                                                (29, 30, False), (31, 2, False), (2, 31, False)])
def test_grid_threshold_and_every_native_edge(columns, rows, shown):
    g = Geometry(120, 120, 1, 1/60, 130, 132, 30, 32)
    scene = Scene.__new__(Scene)
    scene.reader = SimpleNamespace(geometry=g)
    extent = (g.west + 10*g.resolution, g.west + (10+columns)*g.resolution,
              g.north - (10+rows)*g.resolution, g.north - 10*g.resolution)
    frame = Frame()
    scene._grid(frame, extent)
    assert bool(frame.overlays) == shown
    if shown:
        edges = frame.overlays[0].segments
        assert len(edges) == columns + rows + 2
        vertical = edges[np.isclose(edges[:, 0, 0], edges[:, 1, 0])]
        horizontal = edges[np.isclose(edges[:, 0, 1], edges[:, 1, 1])]
        np.testing.assert_allclose(np.diff(np.sort(vertical[:, 0, 0])), g.resolution)
        np.testing.assert_allclose(np.diff(np.sort(horizontal[:, 0, 1])), g.resolution)
    else:
        assert any("30 or more" in text for text in frame.diagnostics)


def test_offset_view_keeps_all_edges_and_roundoff_does_not_toggle_visibility():
    g = Geometry(120, 120, 1, 1/60, 130, 132, 30, 32)
    scene = Scene.__new__(Scene)
    scene.reader = SimpleNamespace(geometry=g)
    # A 29-cell-wide span stays visible after panning across partial cells.
    frame = Frame()
    scene._grid(frame, (g.west + .25*g.resolution, g.west + 29.25*g.resolution,
                        g.north - 2*g.resolution, g.north))
    assert len(frame.overlays[0].segments) == 32  # 29 vertical plus3 horizontal native edges.
    frame = Frame()
    scene._grid(frame, (g.west, g.west + (29 + 1e-10)*g.resolution,
                        g.north - 29*g.resolution, g.north))
    assert len(frame.overlays[0].segments) == 60


def test_browser_png_and_selection_across_grid_visibility_threshold(tmp_path, monkeypatch):
    root = tmp_path / "map"
    root.mkdir()
    step = 1/60
    (root / "params.txt").write_text(f"60\n60\n1\n{step}\n130\n131\n30\n31\n")
    ((np.arange(3600, dtype="<f4") + 1).reshape(60, 60) * 1e6).tofile(root / "uparea.bin")
    app = Explorer(root, tmp_path / "exports")
    app.point_select.value = "grid"
    app.inspect(130.25, 30.75)
    app.overlay_controls["coarse_grid"].value = True
    selected, plot = app.selected, app.plot
    rectangle = {key: list(value) for key, value in app.selected_coarse_source.data.items()}
    assert all(not grid.visible for grid in app.plot.grid)
    assert not any(o.label == "Coarse-grid boundaries" for o in app.frame.overlays)
    assert app.selected_coarse_renderer.visible and len(rectangle["x0"]) == 4
    app.set_extent((130, 130 + 29*step, 31 - 29*step, 31))
    grid = next(o for o in app.frame.overlays if o.label == "Coarse-grid boundaries")
    assert len(grid.segments) == 60
    collections = []
    add = Axes.add_collection
    def capture(ax, collection, *args, **kwargs):
        if isinstance(collection, LineCollection):
            collections.append(np.asarray(collection.get_segments()))
        return add(ax, collection, *args, **kwargs)
    monkeypatch.setattr(Axes, "add_collection", capture)
    assert app.export().is_file()
    assert any(c.shape == grid.segments.shape and np.allclose(c, grid.segments) for c in collections)
    app.set_extent((130, 130 + 30*step, 31 - 29*step, 31))
    assert not any(o.label == "Coarse-grid boundaries" for o in app.frame.overlays)
    assert app.selected == selected and app.plot is plot
    assert {key: list(value) for key, value in app.selected_coarse_source.data.items()} == rectangle
    assert app.selected_coarse_renderer.visible


def test_rounded_one_minute_params_and_nominal_half_degree_view():
    scene = Scene.__new__(Scene)
    scene.reader = SimpleNamespace(geometry=Geometry(1500, 1320, 10, .01666667, 123, 148, 24, 46))
    frame = Frame()
    # Printed spacing is slightly above exact1/60: nominal30 cells must still hide.
    scene._grid(frame, (139, 139.5, 37, 37.5))
    assert not frame.overlays and any("30 or more" in x for x in frame.diagnostics)
    frame = Frame()
    scene._grid(frame, (139, 139 + 29*.01666667, 37.5 - 29*.01666667, 37.5))
    assert frame.overlays
    segments = frame.overlays[0].segments
    vertical = segments[np.isclose(segments[:, 0, 0], segments[:, 1, 0])]
    np.testing.assert_allclose(np.diff(vertical[:, 0, 0]), .01666667)


def test_deep_zoom_inside_one_cell_has_no_edge_and_no_empty_overlay():
    g = Geometry(120, 120, 1, 1/60, 130, 132, 30, 32)
    scene = Scene.__new__(Scene)
    scene.reader = SimpleNamespace(geometry=g)
    frame = Frame()
    scene._grid(frame, (g.west + .2*g.resolution, g.west + .8*g.resolution,
                        g.north - .8*g.resolution, g.north - .2*g.resolution))
    assert not frame.overlays and not frame.diagnostics
