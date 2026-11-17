"""Local Panel/Bokeh map explorer; every browser session owns its state."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from datetime import datetime
from html import escape
from pathlib import Path
import sys

import numpy as np
import panel as pn
from bokeh.events import RangesUpdate, Tap
from bokeh.models import (
    ColorBar,
    ColumnDataSource,
    CustomJS,
    Div,
    FixedTicker,
    LinearColorMapper,
    LogColorMapper,
    Range1d,
    TapTool,
)
from bokeh.plotting import figure

from config import load_settings, save_settings
from map_datasets import DEFAULT_MAP
from basemap import GeographicBasemap
from map_layers import colorize, export_png, make_layer, network_style, raster_subset
from map_reader import MapReader, SCHEMA
from river_network import RiverNetwork, intersects
from selection import SelectionState, CatchmentIndex, coarse_cell_outline, visible_catchment_boundary
from presets import PresetLibrary
from background_controls import BackgroundControls
from river_controls import RiverControls
from map_viewport import MapViewport, frame_size
from view_controls import ASPECTS, ASPECT_LABELS, geographic_ratio, aspect_extent, translated_extent, allocated_frame
from presets import VISIBLE_PRESETS
from inspector import CellInspector
from pins import PinControls
from scene import DASH_PIXELS
from scene import Scene, OVERLAY_DEFAULTS, export_scene

pn.extension()


class Explorer:
    def __init__(self, map_dir, output_dir=None):
        self._closed = False
        self._pending_callbacks = []
        self._queued_functions = set()
        self.reader = MapReader(map_dir)
        self.scene = Scene(self.reader)
        self.cell_inspector = CellInspector(self.reader, self.scene.products)
        self._networks = {}
        self._auto_channel_initialized = False
        self.frame = None
        self._background_error = None
        self.selection = SelectionState()
        self._selection_indexes = {}
        self.preset_library = PresetLibrary()
        self._applied_preset = None
        self._preset_baseline = None
        if not self.reader.sources:
            raise ValueError("No supported readable rasters. " + "; ".join(self.reader.messages))
        self.output_dir = Path(output_dir or Path(__file__).parent / "output").resolve()
        # Even an explicitly supplied export directory must not be inside input.
        if self.output_dir == self.reader.path or self.reader.path in self.output_dir.parents:
            raise ValueError("Output directory must be outside MAP_DIR")
        self.network = None
        self.selected = None
        self.layer = None
        self._updating = False
        self._network_cache = None
        self.apply_aspect_button = pn.widgets.Button(name="Apply Aspect Ratio", button_type="primary")
        self.apply_aspect_button.on_click(lambda event: self._schedule(self._apply_aspect))
        self.basemap = GeographicBasemap()
        self.show_osm = pn.widgets.Checkbox(name="Show OpenStreetMap", value=False)
        self.osm_opacity = pn.widgets.IntSlider(name="OpenStreetMap Opacity", start=0, end=100, step=5, value=100)
        self.map_aspect = pn.widgets.Select(name="Map Aspect Ratio", options=ASPECT_LABELS, value="square")
        self._frame_ratio = 1.0
        self.auto_limits_policy = "percentile"
        self.background_method = "default"
        self.network_geometry = "straight"
        initial_extent = aspect_extent(self.reader.geometry.extent, self.reader.geometry, 1.0)
        self.center_lon = pn.widgets.FloatInput(
            name="Center Longitude [°]", value=(initial_extent[0] + initial_extent[1]) / 2, width=145
        )
        self.center_lat = pn.widgets.FloatInput(
            name="Center Latitude [°]", value=(initial_extent[2] + initial_extent[3]) / 2, width=145
        )
        self.center_button = pn.widgets.Button(name="Move to Center", button_type="primary")
        self.view_note = pn.pane.Markdown("", sizing_mode="stretch_width")
        self.map_aspect.param.watch(lambda event: self._schedule(self._apply_aspect), "value")
        self.center_button.on_click(lambda event: self._schedule(self.move_center))
        self.status = pn.pane.Markdown("", width=295)
        self.network_summary = pn.pane.Markdown("")
        self.inspection = self.cell_inspector.advanced  # Preserve native diagnostic access.
        self.variable = pn.widgets.Select(
            name="Raster variable",
            options={f"{k} · {SCHEMA[k].title}": k for k in self.reader.sources},
            value="uparea" if "uparea" in self.reader.sources else next(iter(self.reader.sources)),
        )
        self.scale = pn.widgets.Select(name="Color scale (continuous only)", options=["auto", "linear", "log"])
        self.palette = pn.widgets.Select(
            name="Continuous palette",
            options=[
                "viridis",
                "terrain",
                "magma",
                "gray",
                "gray_r",
                "Blues",
                "YlGnBu",
                "basin_pastel",
                "subcol_pastel",
                "subcol_gray",
            ],
        )
        self.auto_limits = pn.widgets.Checkbox(name="Automatic color limits", value=True)
        self.low = pn.widgets.FloatInput(name="Color minimum", value=0, width=140)
        self.high = pn.widgets.FloatInput(name="Color maximum", value=1, width=140)
        self.network_choice = pn.widgets.Select(
            name="Stored network",
            options=["off", *(["nextxy"] if "nextxy" in self.reader.network_sources else [])],
            value="nextxy" if "nextxy" in self.reader.network_sources else "off",
        )
        self.width = pn.widgets.FloatSlider(name="Link width", start=0.2, end=4, step=0.2, value=1)
        self.color = pn.widgets.ColorPicker(name="Local / all links", value="#172b4d", width=140)
        self.flex_color = pn.widgets.ColorPicker(name="Flexible links", value="#e67e22", width=140)
        self.distinguish = pn.widgets.Checkbox(name="Distinguish Flexible Downstream", value=True)
        self.area_width = pn.widgets.Checkbox(
            name="Width by upstream area (not discharge)",
            value="uparea" in self.reader.sources,
            disabled="uparea" not in self.reader.sources,
        )
        self.area_color = pn.widgets.Checkbox(
            name="Color by upstream area (overrides type)", value=False, disabled="uparea" not in self.reader.sources
        )
        background_options = {"None": "none", "Coarse raster": "coarse"}
        if any("catmxy" in t.files for t in self.scene.tiles.values()):
            background_options["Unit catchments"] = "catchment"
        if any("elevtn" in t.files for t in self.scene.tiles.values()):
            background_options.update(
                {"High-resolution elevation": "elevtn", "8-neighbor elevation difference (not slope)": "difference"}
            )
        if any("elevtn" in t.files and "flddif" in t.files for t in self.scene.tiles.values()):
            background_options["Floodplain height"] = "flddif"
        self.background = pn.widgets.Select(
            name="Background representation", options=background_options, value="coarse"
        )
        self.hires_source = pn.widgets.Select(
            name="High-resolution source",
            options=list(self.scene.tiles) or [None],
            value=next(
                (key for key, tile in self.scene.tiles.items() if "catmxy" in tile.files),
                next(iter(self.scene.tiles), None),
            ),
        )
        tile = self.scene.tiles.get(self.hires_source.value)
        self.point_select = pn.widgets.RadioButtonGroup(
            name="Point Select",
            options={"Grid": "grid", "Catchment": "catchment"},
            value="grid", disabled=True,
        )
        self.point_note = pn.pane.Markdown("")
        self.resolution_status = pn.pane.Markdown("Selection: Grid", margin=(0,5), styles={"font-size":"12px"})
        self.point_select.param.watch(lambda event: self._schedule(self._point_mode_changed), "value")
        self.terrain_palette = pn.widgets.Select(
            name="Terrain palette (assigned P5/P95)", options=["gray", "pale_terrain"]
        )
        self.representation = pn.widgets.Select(
            name="Main network representation",
            options=["off", "grid_center"] + (["outlet_vector"] if self.scene.products.outlet_source else []),
            value="grid_center",
        )
        self.color_mode = pn.widgets.Select(
            name="Network color", options=["uniform", "connection_type", "upstream_area"], value="connection_type"
        )
        self.width_mode = pn.widgets.Select(
            name="Network width",
            options=["uniform", "upstream_area"],
            value="upstream_area" if "uparea" in self.reader.sources else "uniform",
        )
        self.classification = pn.widgets.Select(
            name="Full-map contributing-area classes",
            options=["quartiles", "six_log", "continuous", "fixed"],
            value="continuous",
        )
        self.area_palette = pn.widgets.Select(
            name="Network area palette", options=["viridis", "shade_rainbow"], value="shade_rainbow"
        )
        self.arrows = pn.widgets.Checkbox(name="Downstream direction heads (zoomed views)", value=False)
        self.arrow_size = pn.widgets.IntSlider(name="Arrow Size [px]", start=0, end=20, step=1, value=0)
        self.overlay_controls = {}
        for key, value in OVERLAY_DEFAULTS.items():
            if isinstance(value, bool):
                self.overlay_controls[key] = pn.widgets.Checkbox(
                    name={
                        "channel": "Bifurcation Channel",
                        "overland": "Bifurcation Overland",
                        "catchment_boundaries": "Unit Catchment Boundaries",
                    }.get(key, key.replace("_", " ").title()),
                    value=value,
                )
            elif key == "channel_pixels_opacity":
                self.overlay_controls[key] = pn.widgets.FloatSlider(
                    name="Channel Pixels Opacity", start=0, end=1, step=0.05, value=value, format="0%"
                )
            elif isinstance(value, str):
                self.overlay_controls[key] = pn.widgets.ColorPicker(name=key.replace("_", " ").title(), value=value)
            else:
                self.overlay_controls[key] = pn.widgets.FloatSlider(
                    name="Bifurcation width", start=0.2, end=5, step=0.1, value=value
                )
        self.overlay_controls["catchment_boundary_color"].name = "Unit Catchment Boundary Color"
        self.overlay_controls["outlet_size"] = pn.widgets.IntSlider(
            name="Outlet Size [px]", start=0, end=20, step=1, value=4, disabled=True
        )
        self.overlay_controls["bif_width"].name = "Base Bifurcation Width [px]"
        self.bif_width_mode = pn.widgets.Select(
            name="Bifurcation Channel Width",
            options={"Uniform": False, "Channel Width": True},
            value=self.overlay_controls["bif_classes"].value,
        )
        self.bif_width_mode.param.watch(lambda event: self._schedule(self._bif_mode_changed), "value")
        self.legend = pn.pane.HTML("", sizing_mode="stretch_width")
        self.extent_inputs = [
            pn.widgets.FloatInput(name=k, value=v, width=140)
            for k, v in zip(["West", "East", "South", "North"], initial_extent)
        ]
        self.apply_extent_button = pn.widgets.Button(name="Apply extent", button_type="primary")
        self.reset_button = pn.widgets.Button(name="Full map")
        self.export_button = pn.widgets.Button(name="Export current view · PNG", button_type="primary")
        self.save_button = pn.widgets.Button(name="Save settings · JSON")
        self.upload = pn.widgets.FileInput(name="Load settings JSON", accept=".json")
        choices = {
            f"{key} · {meta['title'].removeprefix(key).lstrip(' ·:—–-')}": key
            for key in VISIBLE_PRESETS
            if key in self.preset_library.presets
            for row, meta in [self.preset_library.presets[key]]
        }
        self.preset_choice = pn.widgets.Select(
            name="Gallery visualization", options=choices or {"Unavailable": None}, sizing_mode="stretch_width"
        )
        self.preset_description = pn.pane.HTML("", sizing_mode="stretch_width")
        self.preset_status = pn.pane.Markdown("Custom settings", sizing_mode="stretch_width")
        self.preset_extent = pn.widgets.Checkbox(name="Apply suggested Gallery extent", value=False)
        self.apply_preset_button = pn.widgets.Button(name="Apply preset", button_type="primary")
        self.settings_toggle = pn.widgets.Toggle(name="Settings panel", value=True, width=135)
        self.coordinate = Div(text="Lon: —  Lat: —", width=300)
        self.selection_summary = pn.pane.Markdown(
            "Click a map cell; detailed native values appear in **Cell inspector**."
        )
        g = self.reader.geometry
        self.plot = figure(
            x_range=Range1d(initial_extent[0], initial_extent[1]),
            y_range=Range1d(initial_extent[2], initial_extent[3]),
            tools="pan,wheel_zoom,box_zoom,reset,tap,save",
            active_scroll="wheel_zoom",
            title="CaMa-Flood · Map Explorer",
            x_axis_label="Longitude [°]",
            y_axis_label="Latitude [°]",
            background_fill_color="#f5f7fa",
            toolbar_location="above",
            sizing_mode="fixed",
        )
        # Degree-tick graticules are not native computational cell edges.
        # Only the explicit Coarse Grid overlay renders a mesh, without thinning.
        self.plot.grid.visible = False
        self.plot.toolbar.logo = None
        self.basemap_source = ColumnDataSource(dict(image=[], x=[], y=[], dw=[], dh=[]))
        self.basemap_renderer = self.plot.image_rgba(
            image="image", x="x", y="y", dw="dw", dh="dh", source=self.basemap_source, level="image"
        )
        self.basemap.driver.param.watch(lambda event: self._schedule(self._basemap_image), "png")
        for widget in (self.show_osm, self.osm_opacity):
            widget.param.watch(lambda event: self._schedule(self._update_basemap), "value")
        self.image_source = ColumnDataSource(dict(image=[], x=[], y=[], dw=[], dh=[]))
        self.mapper = LinearColorMapper(palette=["#ffffff", "#000000"], low=0, high=1, nan_color="#f5f7fa")
        self.raster = self.plot.image_rgba(
            image="image", x="x", y="y", dw="dw", dh="dh", source=self.image_source, level="image"
        )
        # Overlapping rows of a single image glyph do not define semantic layer order.
        # Keep channel pixels above the background and below vector/selection glyphs.
        self.channel_image_source = ColumnDataSource(dict(image=[], x=[], y=[], dw=[], dh=[]))
        self.channel_raster = self.plot.image_rgba(
            image="image", x="x", y="y", dw="dw", dh="dh", source=self.channel_image_source, level="underlay"
        )
        self.raster.nonselection_glyph = self.raster.glyph
        self.raster.selection_glyph = self.raster.glyph
        # Tap is an inspection gesture, not a selection of scientific layers.
        # Restrict Bokeh selection so clicking does not fade network/overlay glyphs.
        self.plot.select_one(TapTool).renderers = [self.raster]
        self.bar = ColorBar(color_mapper=self.mapper, title="")
        self.plot.add_layout(self.bar, "right")
        self.link_source = ColumnDataSource(dict(x0=[], y0=[], x1=[], y1=[], width=[], color=[]))
        self.plot.segment("x0", "y0", "x1", "y1", line_width="width", line_color="color", source=self.link_source)
        self.path_source = ColumnDataSource(dict(xs=[], ys=[], width=[], color=[]))
        self.plot.multi_line("xs", "ys", source=self.path_source, line_color="color", line_width="width")
        self.overlay_sources = {}
        self.overlay_renderers = {}
        for dash, pattern in DASH_PIXELS.items():
            source = ColumnDataSource(dict(x0=[], y0=[], x1=[], y1=[], width=[], color=[]))
            self.overlay_sources[dash] = source
            self.overlay_renderers[dash] = self.plot.segment(
                "x0",
                "y0",
                "x1",
                "y1",
                source=source,
                line_width="width",
                line_color="color",
                line_dash=dict(value=list(pattern)),
                line_cap="round" if dash == "dotted" else "butt",
            )
        self.overlay_source = self.overlay_sources["solid"]  # existing public solid-layer adapter
        self.outlet_source = ColumnDataSource(dict(x=[], y=[], size=[]))
        self.outlet_renderer = self.plot.scatter(
            "x", "y", source=self.outlet_source, size="size", fill_color="white", line_color="#555555", line_width=0.5
        )
        self.arrow_source = ColumnDataSource(dict(x=[], y=[], angle=[], color=[], size=[]))
        self.plot.scatter(
            "x",
            "y",
            source=self.arrow_source,
            marker="triangle",
            angle="angle",
            fill_color="color",
            line_color="color",
            size="size",
        )
        self.selected_source = ColumnDataSource(dict(x=[], y=[]))
        self.plot.scatter(
            "x", "y", source=self.selected_source, size=15, line_color="#FFD400", fill_alpha=0, line_width=3
        )
        self.selected_link = ColumnDataSource(dict(x0=[], y0=[], x1=[], y1=[], angle=[]))
        self.plot.segment("x0", "y0", "x1", "y1", source=self.selected_link, line_color="#FFD400", line_width=3)
        self.selected_arrow_renderer = self.plot.scatter(
            "x1",
            "y1",
            source=self.selected_link,
            marker="triangle",
            angle="angle",
            size=15,
            fill_color="#FFD400",
            line_color="#FFD400",
            name="selected-downstream-arrow",
        )
        # Computational rectangle is a guide, never the unit-catchment boundary.
        self.selected_coarse_source = ColumnDataSource(dict(x0=[], y0=[], x1=[], y1=[]))
        self.selected_coarse_renderer = self.plot.segment(
            "x0",
            "y0",
            "x1",
            "y1",
            source=self.selected_coarse_source,
            line_color="#D8C8F0",
            line_width=3,
            line_alpha=1,
            line_dash="dashed",
            name="selected-coarse-grid",
        )
        # Separate from ordinary catchment outlines; source remains mounted.
        self.selection_boundary_source = ColumnDataSource(dict(x0=[], y0=[], x1=[], y1=[]))
        self.selection_boundary_renderer = self.plot.segment(
            "x0",
            "y0",
            "x1",
            "y1",
            source=self.selection_boundary_source,
            line_color="#FF7F00",
            line_width=3,
            line_dash="solid",
            name="selected-unit-catchment",
        )
        self.plot.js_on_event(
            "mousemove",
            CustomJS(
                args={"target": self.coordinate},
                code="target.text = `Lon: ${cb_obj.x.toFixed(4)}°  Lat: ${cb_obj.y.toFixed(4)}°`;",
            ),
        )
        self.plot.on_event(Tap, self._tap)
        self.plot.on_event(RangesUpdate, self._navigation)
        self.apply_extent_button.on_click(lambda event: self._schedule(self.apply_extent))
        self.reset_button.on_click(lambda event: self._schedule(lambda: self.set_extent(g.extent)))
        self.export_button.on_click(lambda event: self._schedule(self.export))
        self.save_button.on_click(lambda event: self._schedule(self.save))
        self.upload.param.watch(lambda event: self._schedule(lambda: self.load(event.new)), "value")
        self.background_ui = BackgroundControls(self)
        self.raster_type = self.background_ui.raster_type
        self.coarse_variable = self.background_ui.coarse_variable
        self.highres_variable = self.background_ui.highres_variable
        self.no_background = self.background_ui.no_background
        self.background_opacity = self.background_ui.opacity
        self.highres_palette = self.background_ui.highres_palette
        self.highres_scale = self.background_ui.highres_scale
        self.highres_auto_limits = self.background_ui.highres_auto
        self.highres_low = self.background_ui.highres_low
        self.highres_high = self.background_ui.highres_high
        self.river_ui = RiverControls(self)
        for widget in (self.variable, self.scale, self.palette, self.auto_limits, self.low, self.high):
            widget.param.watch(
                lambda event: self._schedule(lambda: self.background_ui.legacy_changed(event.obj)), "value"
            )
        for widget in (
            self.network_choice,
            self.width,
            self.color,
            self.flex_color,
            self.distinguish,
            self.area_width,
            self.area_color,
        ):
            widget.param.watch(lambda event: self._schedule(self.update_network), "value")
        self.variable.value = "uparea" if "uparea" in self.reader.sources else next(iter(self.reader.sources))
        self._guard(self.update_layer)
        self._guard(self.update_network)
        for widget in (self.background, self.terrain_palette):
            widget.param.watch(
                lambda event: self._schedule(lambda: self.background_ui.legacy_changed(event.obj)), "value"
            )
        for widget in (self.representation,):
            widget.param.watch(lambda event: self._schedule(self.update_network), "value")
        for widget in (self.color_mode, self.width_mode):
            widget.param.watch(lambda event: self._schedule(self._style_modes), "value")
        for widget in self.overlay_controls.values():
            widget.param.watch(lambda event: self._schedule(self.render_view), "value")
        self.arrows.param.watch(lambda event: self._schedule(self.river_ui.legacy_arrows), "value")
        self.hires_source.param.watch(lambda event: self._schedule(self._hires_changed), "value")
        self.preset_choice.param.watch(lambda event: self._schedule(self._describe_preset), "value")
        self.apply_preset_button.on_click(lambda event: self._schedule(self.apply_preset))
        background_controls = self.background_ui.view
        network_controls = self.river_ui.view
        self.boundary_status = pn.pane.Markdown("", sizing_mode="stretch_width")
        self._update_assignment_controls()
        self.overlay_visibility = pn.Column(
            pn.pane.Markdown("### Visible Overlays", margin=(0, 0)),
            *(
                self.overlay_controls[k]
                for k in (
                    "catchment_boundaries",
                    "channel_pixels",
                    "channel",
                    "overland",
                    "outlets",
                    "headwater",
                    "coarse_grid",
                )
            ),
        )
        self.overlay_controls["headwater"].name = "Headwater Guides"
        self.overlay_styles = pn.Column(
            pn.pane.Markdown("### Overlay Display Settings", margin=(0, 0)),
            self.overlay_controls["catchment_boundary_color"],
            self.boundary_status,
            self.overlay_controls["channel_pixels_opacity"],
            self.overlay_controls["channel_color"],
            self.overlay_controls["overland_color"],
            self.overlay_controls["bif_width"],
            self.bif_width_mode,
            pn.pane.Markdown(
                "Scale bifurcation line width using stored first-layer channel width (m); not discharge or upstream area."
            ),
            self.overlay_controls["outlet_size"],
        )
        overlay_controls = pn.Column(
            self.overlay_visibility, self.background_ui.channel_note, self.overlay_styles, width=330
        )
        navigation = pn.Column(
            self.map_aspect,
            self.apply_aspect_button,
            self.view_note,
            pn.pane.Markdown("### Move Map Center", margin=(0, 0)),
            pn.Row(self.center_lon, self.center_lat),
            self.center_button,
            pn.pane.Markdown("### Geographic extent"),
            pn.Row(*self.extent_inputs[:2]),
            pn.Row(*self.extent_inputs[2:]),
            pn.Row(self.apply_extent_button, self.reset_button),
            self.export_button,
            self.save_button,
            self.upload,
            self.status,
            width=330,
        )
        diagnostics = (
            "<br>".join(escape(v) for v in self.reader.messages + self.scene.messages)
            or "Supported products passed metadata checks."
        )
        header = pn.pane.HTML(
            f'<h2 style="margin:4px">CaMa-Flood · Map Explorer v3</h2><small>{escape(self.reader.path.name)} · {g.nx} × {g.ny} · local & read-only</small>'
        )
        details = pn.Column(
            pn.pane.Markdown("#### Point Select"), self.point_select, self.point_note, self.cell_inspector.view
        )
        self.right_tabs = pn.Tabs(
            ("Background", background_controls),
            ("River", network_controls),
            ("Overlays", overlay_controls),
            ("View", navigation),
            sizing_mode="stretch_width",
        )
        preset_box = pn.Column(
            pn.pane.Markdown("### Gallery Presets", margin=(0, 0)),
            self.preset_choice,
            self.preset_description,
            self.preset_extent,
            self.apply_preset_button,
            self.preset_status,
            sizing_mode="stretch_width",
        )
        self.panel_mode = pn.widgets.RadioButtonGroup(
            options=["Visualization", "Inspector"], value="Visualization", sizing_mode="stretch_width"
        )
        self.visualization_panel = pn.Column(preset_box, self.right_tabs, sizing_mode="stretch_width")
        self.inspector_panel = details
        self.inspector_panel.sizing_mode = "stretch_width"
        self.inspector_panel.styles = {"flex-shrink": "0", "max-height": "none"}
        self.visualization_panel.styles = {"flex-shrink": "0", "max-height": "none"}
        self.inspector_panel.visible = False
        self.panel_mode.param.watch(lambda event: self._schedule(self._panel_mode_changed), "value")
        self.settings_panel = pn.Column(
            self.panel_mode,
            self.visualization_panel,
            self.inspector_panel,
            sizing_mode="stretch_width",
            min_width=340,
            max_width=420,
            styles={
                "flex": "1 1 28%",
                "height": "calc(100vh - 95px)",
                "overflow-y": "auto",
                "position": "sticky",
                "top": "8px",
                "padding": "8px",
                "background": "#f5f7fb",
            },
        )
        self.map_viewport = MapViewport(plot=pn.pane.Bokeh(self.plot), sizing_mode="stretch_width")
        self.map_viewport.param.watch(lambda *events: self._schedule(self.render_view), ["bounds", "pixel_ratio"])
        self.pins = PinControls(self)
        self.inspector_panel.append(self.pins.view)
        self.map_region = pn.Column(
            self.coordinate,
            self.resolution_status,
            self.selection_summary,
            self.map_viewport,
            self.basemap.driver,
            self.basemap.attribution,
            self.legend,
            self.pins.comparison,
            sizing_mode="stretch_width",
            min_width=300,
            styles={"flex": "3 1 68%", "min-width": "300px"},
        )
        self.content = pn.FlexBox(
            self.map_region,
            self.settings_panel,
            flex_wrap="wrap",
            align_items="flex-start",
            sizing_mode="stretch_width",
        )
        self.header_bar = pn.Row(
            header, pn.Spacer(sizing_mode="stretch_width"), self.settings_toggle, sizing_mode="stretch_width"
        )
        self.view = pn.Column(
            self.header_bar,
            self.content,
            sizing_mode="stretch_width",
        )
        self.settings_toggle.param.watch(
            lambda event: self._schedule(lambda: setattr(self.settings_panel, "visible", event.new)), "value"
        )
        self._describe_preset()

    def _schedule(self, function):
        # Panel widget events can run outside Bokeh's document lock. Queue
        # direct glyph/range/source mutations on a locked server tick; otherwise
        # a callback can stop halfway and leave the GUI inconsistent with export.
        if self._updating or self._closed:
            return
        document = self.plot.document
        if document is not None and document.session_context is not None:
            if function in self._queued_functions:
                return
            self._queued_functions.add(function)
            def execute():
                self._queued_functions.discard(function)
                self._pending_callbacks[:] = [(d, h) for d, h in self._pending_callbacks if h is not handle]
                self._guard(function)
            handle = (document.add_timeout_callback(execute,75)
                      if function in (self.render_view,self._apply_navigation) else document.add_next_tick_callback(execute))
            self._pending_callbacks.append((document, handle))
        else:
            self._guard(function)

    def _guard(self, function):
        if self._updating or self._closed:
            return
        try:
            function()
        except (ValueError, OSError, KeyError, TypeError) as exc:
            self.status.object = f"**Error:** {escape(str(exc))}"

    def close(self):
        """Detach queued work and release map-dependent caches after view replacement.

        Panel removes the old view/models from the document; internal widget
        cycles are garbage-collectable. Never forcibly close a memmap still held
        by NumPy views: releasing references lets its normal lifetime handle it.
        """
        self._closed = True
        for document, handle in self._pending_callbacks:
            try:
                document.remove_next_tick_callback(handle)
            except ValueError:
                try:
                    document.remove_timeout_callback(handle)
                except ValueError:
                    pass
        self._pending_callbacks.clear()
        self._queued_functions.clear()
        self._visible_boundary = None
        self.frame = self.layer = self.network = self._network_cache = None
        self._networks.clear()
        self._selection_indexes.clear()
        self.reader._cache.clear()
        self.scene.products._views.clear()
        for name in ("outlets", "bifurcations"):
            self.scene.products.__dict__.pop(name, None)
        for tile in self.scene.tiles.values():
            for source in tile.cog.values():
                source.cache.clear()
        self.scene._outline_cache.clear()
        self.scene.tiles.clear()
        self.cell_inspector._graphs.clear()
        for name in ("outlet_coordinates", "bifurcation_counts"):
            self.cell_inspector.__dict__.pop(name, None)
        self.cell_inspector.native.__dict__.pop("subbasins", None)
        self.pins.pins.clear()
        self.basemap.driver.enabled = False

    @property
    def extent(self):
        return self.plot.x_range.start, self.plot.x_range.end, self.plot.y_range.start, self.plot.y_range.end

    def _size_map(self):
        bounds = self.map_viewport.bounds if hasattr(self, "map_viewport") else [900, 600]
        data, allocation = allocated_frame(self.extent, bounds, self._frame_ratio)
        self.plot.frame_width, self.plot.frame_height = data
        if hasattr(self, "map_viewport"):
            self.map_viewport.height = allocation[1] + 90
            self.map_viewport.plot.width = allocation[0] + 150
            self.map_viewport.plot.height = allocation[1] + 85
        self._update_basemap()

    def _update_basemap(self):
        self.basemap_renderer.glyph.global_alpha = self.osm_opacity.value / 100
        self.basemap_renderer.visible = self.show_osm.value
        if not self.show_osm.value:
            self.basemap_source.data = dict(image=[], x=[], y=[], dw=[], dh=[])
        self.basemap.update(
            self.extent,
            (self.plot.frame_width or 900, self.plot.frame_height or 600),
            self.show_osm.value,
            self.osm_opacity.value / 100,
        )

    def _basemap_image(self):
        decoded = self.basemap.decode()
        if decoded is not None:
            image, (w, e, s, n) = decoded
            self.basemap_source.data = dict(image=[image], x=[w], y=[s], dw=[e - w], dh=[n - s])

    def _panel_mode_changed(self):
        # Persistent children preserve widget/Bokeh ownership, tab selection and
        # accordion state. Map clicks never change this independent UI mode.
        self.visualization_panel.visible = self.panel_mode.value == "Visualization"
        self.inspector_panel.visible = self.panel_mode.value == "Inspector"

    def _point_mode_changed(self):
        self._update_assignment_controls()
        if hasattr(self, "_last_click"):
            self.inspect(*self._last_click)

    def _apply_aspect(self):
        if self.map_aspect.value == "custom":
            self._frame_ratio = geographic_ratio(self.extent)
            self._size_map()
            return
        self._frame_ratio = ASPECTS[self.map_aspect.value]
        self.set_extent(aspect_extent(self.extent, self.reader.geometry, self._frame_ratio), preserve_aspect=True)
        self.view_note.object = (
            "Frame shape changed around the same center; scale is reduced only when needed to fit the domain."
        )

    def move_center(self):
        requested = (self.center_lon.value, self.center_lat.value)
        extent = translated_extent(self.extent, self.reader.geometry, *requested)
        self.set_extent(extent, preserve_aspect=True)
        actual = ((extent[0] + extent[1]) / 2, (extent[2] + extent[3]) / 2)
        adjusted = any(abs(a - b) > 1e-8 for a, b in zip(requested, actual))
        self.view_note.object = (
            f"Center adjusted to {actual[0]:.5f}°, {actual[1]:.5f}° to fit the domain. "
            if adjusted
            else "Center moved. "
        ) + "Degree spans and frame preference preserved; geographic latitude correction may add letterboxing."

    def _bif_mode_changed(self):
        self.overlay_controls["bif_classes"].value = self.bif_width_mode.value

    def _overlay_controls_state(self):
        updating = self._updating
        self._updating = True
        try:
            self.bif_width_mode.value = self.overlay_controls["bif_classes"].value
            self.bif_width_mode.disabled = self.overlay_controls["channel_color"].disabled = not self.overlay_controls[
                "channel"
            ].value
            self.overlay_controls["overland_color"].disabled = not self.overlay_controls["overland"].value
            self.overlay_controls["bif_width"].disabled = not (
                self.overlay_controls["channel"].value or self.overlay_controls["overland"].value
            )
            self.overlay_controls["catchment_boundary_color"].disabled = not self.overlay_controls[
                "catchment_boundaries"
            ].value
            self.overlay_controls["outlet_size"].disabled = not self.overlay_controls["outlets"].value
            self.overlay_controls["channel_pixels_opacity"].disabled = (
                not self.overlay_controls["channel_pixels"].value
                or self.overlay_controls["channel_pixels"].disabled
            )
        finally:
            self._updating = updating

    def set_extent(self, extent, *, preserve_aspect=False):
        self.reader.geometry.validate_extent(extent)
        w, e, s, n = extent
        updating = self._updating
        self._updating = True
        try:
            if not preserve_aspect:
                self.map_aspect.value = "custom"
                self._frame_ratio = geographic_ratio(extent)
                self.view_note.object = (
                    "Custom geographic extent is authoritative; the frame follows its undistorted proportions."
                )
            self.center_lon.value, self.center_lat.value = (w + e) / 2, (s + n) / 2
        finally:
            self._updating = updating
        self.plot.x_range.start, self.plot.x_range.end = w, e
        self.plot.y_range.start, self.plot.y_range.end = s, n
        for widget, value in zip(self.extent_inputs, extent):
            widget.value = value
        self.render_view()

    def apply_extent(self):
        self.set_extent(tuple(w.value for w in self.extent_inputs))

    def _navigation(self, event):
        # Wheel/pan may move beyond map bounds; clamp to the map on completion
        # rather than rendering misleading extrapolated data or exporting it.
        g = self.reader.geometry
        # Browser range events can arrive before the separate Range1d property
        # patches. Use the event's complete viewport, not partly stale ranges.
        extent = (max(g.west, event.x0), min(g.east, event.x1), max(g.south, event.y0), min(g.north, event.y1))
        if extent[0] >= extent[1] or extent[2] >= extent[3]:
            extent = g.extent
        if np.allclose(extent,getattr(self,"_rendered_extent",(0,0,0,0)),rtol=0,atol=1e-10):
            return
        self._pending_navigation_extent = extent
        self._schedule(self._apply_navigation)

    def _apply_navigation(self):
        self.set_extent(self._pending_navigation_extent,preserve_aspect=True)

    def _unavailable_background(self, exc):
        self._background_error = str(exc)
        self.image_source.data = dict(image=[], x=[], y=[], dw=[], dh=[])
        self.channel_image_source.data = dict(image=[], x=[], y=[], dw=[], dh=[])
        self.bar.visible = False
        self.background_ui.color_note.object = "Background unavailable: " + str(exc)
        self.plot.title.text = "Background unavailable · check color limits"

    def update_layer(self):
        name = self.variable.value
        if not SCHEMA[name].categorical and self.palette.value in ("basin_pastel", "subcol_pastel", "subcol_gray"):
            self._updating = True
            self.palette.value = "viridis"
            self._updating = False
        try:
            layer = make_layer(
                self.reader,
                name,
                self.scale.value,
                self.palette.value,
                None if self.auto_limits.value else (self.low.value, self.high.value),
                reference_policy=self.auto_limits_policy if self.background.value == "coarse" else "gallery",
                palette_range=(
                    [self.background_ui.coarse_palette_min.value, self.background_ui.coarse_palette_max.value]
                    if self.background.value == "coarse"
                    else None
                ),
            )
        except ValueError as exc:
            self._unavailable_background(exc)
            raise
        self.layer = layer
        self._background_error = None
        self._updating = True
        try:
            for widget in (self.scale, self.palette, self.auto_limits):
                widget.disabled = SCHEMA[name].categorical
            self.low.disabled = self.high.disabled = self.auto_limits.value or SCHEMA[name].categorical
            if self.auto_limits.value or layer.logarithmic:
                self.low.value, self.high.value = layer.low, layer.high
        finally:
            self._updating = False
        self._set_colorbar(layer)
        self.plot.title.text = layer.label
        mode = self.background.value
        if mode in ("elevtn", "flddif", "difference"):
            tile = self.scene.tiles.get(self.hires_source.value)
            source = tile.files.get("elevtn" if mode == "difference" else mode) if tile else None
            self.status.object = f"**Background source:** `{source.name if source else 'unavailable'}` · {mode} [m]. Terrain display transforms affect display only."
        elif mode == "none":
            self.status.object = (
                "No raster background. Grid selection and river-network overlays remain available."
            )
        else:
            self.status.object = f"**Source:** `{self.reader.sources[name].path.name}`\n\n" + (
                "Discrete categories; colors may repeat."
                if SCHEMA[name].categorical
                else "Color transforms affect display only."
            )
        self.render_view()

    def _set_colorbar(self, layer):
        self.bar.visible = layer is not None
        if layer is None:
            return
        cls = LogColorMapper if layer.logarithmic else LinearColorMapper
        self.mapper = cls(palette=layer.palette, low=layer.low, high=layer.high, nan_color="#f5f7fa")
        self.bar.color_mapper = self.mapper
        self.bar.scale_alpha = self.background_opacity.value / 100
        # Match the canvas underneath the translucent raster, not a white legend patch.
        self.bar.background_fill_color = self.plot.background_fill_color
        self.bar.background_fill_alpha = 1.0
        short_name = layer.label.split(" —")[0]
        self.bar.title = (
            "Elevation diff. [m]"
            if layer.label.startswith("Maximum")
            else f"{short_name} [{SCHEMA[short_name].display_units}]" if short_name in SCHEMA else short_name
        )
        if len(layer.categories):
            ticks = np.unique(np.linspace(0, len(layer.categories) - 1, min(16, len(layer.categories))).astype(int))
            self.bar.ticker = FixedTicker(ticks=ticks.tolist())
            self.bar.major_label_overrides = {int(i): str(int(layer.categories[i])) for i in ticks}
        else:
            from bokeh.models import BasicTicker, LogTicker

            self.bar.ticker = LogTicker() if layer.logarithmic else BasicTicker()
            self.bar.major_label_overrides = {}

    def _style_modes(self):
        self._updating = True
        try:
            self.area_color.value = self.color_mode.value == "upstream_area"
            self.distinguish.value = self.color_mode.value == "connection_type"
            self.area_width.value = self.width_mode.value == "upstream_area"
        finally:
            self._updating = False
        self.update_network()

    def network_options(self):
        return dict(
            width=self.width.value,
            color=self.color.value,
            flexible_color=self.flex_color.value,
            distinguish=self.distinguish.value,
            scale_width=self.area_width.value,
            color_area=self.area_color.value,
            classification=self.classification.value,
            area_palette=self.area_palette.value,
            area_limits=None if self.river_ui.auto.value else [self.river_ui.low.value, self.river_ui.high.value],
            area_color_style=self.river_ui.color_style,
            area_scale=self.river_ui.scale.value,
        )

    def update_network(self):
        name = self.network_choice.value
        if name == "off" or self.representation.value == "off":
            self.network = None
        else:
            if name not in self._networks:
                self._networks[name] = RiverNetwork(self.reader, name)
            self._network_cache = self._networks[name]
            self.network = self.scene.products.network_view(self._network_cache, self.representation.value)
            if self.representation.value == "outlet_vector" and not self._auto_channel_initialized:
                self._auto_channel_initialized = True
                self._updating = True
                try:
                    self.overlay_controls["channel"].value = self.scene.products.bif_path is not None
                finally:
                    self._updating = False
        if name in self.reader.network_sources:
            if name not in self._networks:
                self._networks[name] = RiverNetwork(self.reader, name)
            self.cell_inspector.graph(self._networks[name])
        self.render_view()
        if self.selected is not None:
            if hasattr(self, "_last_click"):
                self.inspect(*self._last_click, resolve_selection=False)
            else:
                self._highlight(*self.selected)

    def scene_options(self):
        return dict(
            automatic_selection=True,
            background_method=(
                self.background_method
                if self.background.value == "coarse" and self.variable.value == "subcol"
                else "default"
            ),
            network_geometry=self.network_geometry,
            network_detail=self.river_ui.detail.value,
            network_budget=self.river_ui.budget.value,
            background=self.background.value,
            tile=self.hires_source.value,
            screen=((self.plot.frame_width or 750)*getattr(getattr(self,"map_viewport",None),"pixel_ratio",1), (self.plot.frame_height or 515)*getattr(getattr(self,"map_viewport",None),"pixel_ratio",1)),
            terrain_palette=self.terrain_palette.value,
            background_opacity=self.background_ui.opacity.value / 100,
            highres_style=self.background_ui.highres_options(),
            auto_limits_policy=self.auto_limits_policy,
            coarse_palette_range=[
                self.background_ui.coarse_palette_min.value,
                self.background_ui.coarse_palette_max.value,
            ],
            network_style=self.network_options(),
            arrows=self.arrows.value,
            arrow_size=self.arrow_size.value,
            overlays={k: widget.value for k, widget in self.overlay_controls.items()},
        )

    def render_view(self):
        if self.background.value == "coarse" and self._background_error is not None:
            # A River/Overlay callback must not revive the previous valid raster
            # while current coarse physical limits are invalid. update_layer
            # clears this flag only after constructing the current valid layer.
            raise ValueError(self._background_error)
        if self.layer is None:
            return
        # Resolve selection before composing layers: even an unavailable overlay
        # must not leave old grid/catchment highlights from another rule/tile.
        self._size_map()
        try:
            self.frame = frame = self.scene.build(
                self.extent, self.variable.value, self.layer, self.network, self.scene_options()
            )
        except ValueError as exc:
            # Never leave a previous variable's image masquerading as the new
            # background when native-assignment statistics cannot be computed.
            self._unavailable_background(exc)
            raise
        self._background_error = None
        self._rendered_extent = tuple(self.extent)
        self._update_assignment_controls()
        self._reconcile_selection_source()
        self._set_colorbar(frame.layer)
        # Synchronize effective Log bounds only after building the current frame;
        # visibility/profile restoration can still refer to a previous frame.
        if self.background_ui.raster_type.value == "highres" and frame.layer is not None and frame.layer.logarithmic:
            updating = self._updating
            self._updating = True
            try:
                self.highres_low.value, self.highres_high.value = frame.layer.low, frame.layer.high
            finally:
                self._updating = updating
        self.plot.title.text = (
            "Unit catchments · " + self.variable.value
            if self.background.value == "catchment"
            else (
                "8-neighbor elevation difference [m]"
                if self.background.value == "difference"
                else (
                    "High-resolution " + self.background.value + " [m]"
                    if self.background.value in ("elevtn", "flddif")
                    else self.variable.value if self.background.value == "coarse" else "Stored river-map geometry"
                )
            )
        )
        for source, images in ((self.image_source, frame.images[:frame.background_count]), (self.channel_image_source, frame.images[frame.background_count:])):
            # Clear each source on every update, including toggles and unavailable layers.
            source.data = dict(
                image=[np.ascontiguousarray(a[::-1]) for a, e in images],
                x=[e[0] for a, e in images],
                y=[e[2] for a, e in images],
                dw=[e[1] - e[0] for a, e in images],
                dh=[e[3] - e[2] for a, e in images],
            )
        self.path_source.data = frame.paths
        self.link_source.data = (
            dict(x0=[], y0=[], x1=[], y1=[], width=[], color=[]) if frame.paths["xs"] else frame.main
        )
        for dash, source in self.overlay_sources.items():
            combined = dict(x0=[], y0=[], x1=[], y1=[], width=[], color=[])
            for overlay in frame.overlays:
                if overlay.dash != dash:
                    continue
                segments = overlay.segments
                for key, values in [
                    ("x0", segments[:, 0, 0]),
                    ("y0", segments[:, 0, 1]),
                    ("x1", segments[:, 1, 0]),
                    ("y1", segments[:, 1, 1]),
                    ("width", np.broadcast_to(overlay.width, (len(segments),))),
                    ("color", np.full(len(segments), overlay.color)),
                ]:
                    combined[key].extend(values.tolist())
            source.data = combined
        self.outlet_source.data = dict(
            x=frame.points[:, 0], y=frame.points[:, 1], size=np.full(len(frame.points), frame.point_size)
        )
        self._overlay_controls_state()
        self.arrow_source.data = frame.arrows
        self.river_ui.detail_note.object = frame.network_detail_note
        labels = frame.legend + [entry[3] for entry in frame.overlays] + frame.diagnostics
        swatches = "".join(
            f'<div><span style="display:inline-block;width:35px;height:{max(2,width*2):.2f}px;background:{color};margin-right:8px"></span>{escape(label)}</div>'
            for label, color, width in frame.swatches
        )
        self.legend.object = (
            "<details><summary>Legend & diagnostics</summary>"
            + swatches
            + "".join("<div>" + escape(label) + "</div>" for label in labels)
            + "</details>"
        )
        if self.selected is not None:
            self._highlight(*self.selected)

        self._render_catchment_selection()
        self._check_preset_modified()
        if hasattr(self, "background_ui"):
            self.background_ui.refresh_visibility()
        if hasattr(self, "river_ui"):
            self.river_ui.refresh()

    def _render_catchment_selection(self):
        if self.selection.kind == "catchment" and self.selection.river_cell is not None:
            tile = self.scene.tiles.get(self.selection.tile_key)
            if tile is not None and "catmxy" in tile.cog:
                boundary, _ = self._selected_catchment(tile,self.selection.river_cell)
                if boundary is not self.selection.boundary:
                    self.selection = replace(self.selection,boundary=boundary)
        rectangle = self.selection.coarse_outline
        self.selected_coarse_source.data = (
            dict(x0=[], y0=[], x1=[], y1=[])
            if rectangle is None
            else dict(x0=rectangle[:, 0, 0], y0=rectangle[:, 0, 1], x1=rectangle[:, 1, 0], y1=rectangle[:, 1, 1])
        )
        boundary = self.selection.boundary
        if boundary is None:
            self.selection_boundary_source.data = dict(x0=[], y0=[], x1=[], y1=[])
            return
        segments = boundary.segments
        ids = intersects(segments[:, 0, 0], segments[:, 0, 1], segments[:, 1, 0], segments[:, 1, 1], self.extent)
        visible = segments[ids]
        self.selection_boundary_source.data = dict(
            x0=visible[:, 0, 0], y0=visible[:, 0, 1], x1=visible[:, 1, 0], y1=visible[:, 1, 1]
        )

    def _update_assignment_controls(self):
        plans = self.frame.sampling if self.frame is not None else {}
        active = bool(plans) and len(plans) == len(self.scene.visible_tiles(self.hires_source.value, self.extent)) and all(p.native and "catmxy" in self.scene.tiles[key].cog for key,p in plans.items())
        mode = "catchment" if active else "grid"
        updating = self._updating
        self._updating = True
        try:
            self.point_select.value = mode
            self.point_select.disabled = True  # One automatic state, retained in old JSON as effective mode.
        finally:
            self._updating = updating
        self.point_note.object = "**Selection: Catchment** · Native COG pixels without decimation." if active else (
            "**Selection: Grid** · Zoom in to native COG resolution with catmxy to enable Catchment selection.")
        self.resolution_status.object = self.point_note.object
        self.cell_inspector.pixel_section.visible = active
        self.overlay_controls["catchment_boundaries"].disabled = not active
        if hasattr(self,"boundary_status"):
            self.boundary_status.object = "" if active else "Native Unit Catchment Boundaries disabled in Grid mode."

    def _hires_changed(self):
        self._update_assignment_controls()
        self.background_ui.source_changed()

    def _clear_selection(self, message):
        self.selection = SelectionState(status=message)
        self.selected = None
        if hasattr(self, "_last_click"):
            del self._last_click
        self.selected_source.data = dict(x=[], y=[])
        self.selected_link.data = dict(x0=[], y0=[], x1=[], y1=[], angle=[])
        self.selection_boundary_source.data = dict(x0=[], y0=[], x1=[], y1=[])
        self.selected_coarse_source.data = dict(x0=[], y0=[], x1=[], y1=[])
        self.selection_summary.object = message
        self.cell_inspector.clear(message)

    def _reconcile_selection_source(self):
        # Native window counts/attributes must update together after pan/source changes.
        tile = self.scene.tiles.get(self.selection.tile_key)
        native_changed = self.selection.kind == "catchment" and tile is not None and (
            getattr(self, "_visible_boundary_key", None) !=
            (tile.key, tile.source_identity, self.selection.river_cell, self.extent)
        )
        if hasattr(self, "_last_click") and (
            native_changed or self.selection.method != self._selection_method() or getattr(self,"_selection_source_key",None) != self.hires_source.value
        ):
            self.inspect(*self._last_click)

    def _selection_method(self):
        return (
            "Coarse Grid geographic containment"
            if self.point_select.value == "grid"
            else "High-resolution catmxy assignment"
        )

    def _selected_catchment(self, tile, cell):
        if tile is None or "catmxy" not in tile.cog:
            return None, "Catchment boundary unavailable: no native catmxy COG"
        key = (tile.key,tile.source_identity,cell,self.extent)
        if getattr(self,"_visible_boundary_key",None) != key:
            self._visible_boundary = visible_catchment_boundary(tile,self.reader.geometry,*cell,self.extent)
            self._visible_boundary_key = key
        return self._visible_boundary, "Stored unit catchment selected; visible-window boundary"
    def _highlight(self, row, col):
        g = self.reader.geometry
        x, y = g.lon[col], g.lat[row]
        if self.representation.value == "outlet_vector" and self.scene.products.outlet_source:
            a, b = self.scene.products.outlets
            if np.isfinite(a[row, col]) and np.isfinite(b[row, col]):
                x, y = a[row, col], b[row, col]
        self.selected_source.data = dict(x=[x], y=[y])
        if self.network is not None:
            net = self.network
            ids = np.flatnonzero((net.rows[net.link_index] == row) & (net.cols[net.link_index] == col))
            # Endpoint head follows stored downstream connectivity, using the
            # same geographic aspect correction as the displayed map.
            cosine = max(0.05, np.cos(np.deg2rad((self.extent[2] + self.extent[3]) / 2)))
            angle = np.arctan2(net.y1[ids] - net.y0[ids], (net.x1[ids] - net.x0[ids]) * cosine) - np.pi / 2
            self.selected_link.data = dict(x0=net.x0[ids], y0=net.y0[ids], x1=net.x1[ids], y1=net.y1[ids], angle=angle)
        else:
            self.selected_link.data = dict(x0=[], y0=[], x1=[], y1=[], angle=[])

    def inspect(self, lon, lat, resolve_selection=True, network_product=None):
        if resolve_selection:
            self._update_assignment_controls()
            self._last_click = (lon, lat)
            self._selection_source_key = self.hires_source.value
            coarse = self.reader.geometry.cell(lon, lat)
            if coarse is None:
                raise ValueError("Click is outside the map")
            tile = self.scene.tile_at(lon,lat,self.hires_source.value,self.extent) if self.point_select.value == "catchment" else None
            pixel = tile.geometry.cell(lon, lat) if tile else None
            method = self._selection_method()
            extra, assigned = self.scene.inspect(lon, lat, tile.key, cog_only=True) if tile else ({},None)
            if method == "Coarse Grid geographic containment":
                # Geographic computational grid A wins, even if the clicked
                # native pixel is assigned to another river-map grid B.
                selected = coarse
                boundary, status = None, "Geographic computational Grid selected"
                kind = "coarse"
            else:
                # Explicit Catchment mode uses native catmxy for every background. Missing
                # codes or products never substitute the containing rectangle.
                selected = assigned
                boundary = None
                status = extra.get("assignment status", "Catchment selection unavailable: no catmxy in selected source")
                if selected is not None:
                    boundary, status = self._selected_catchment(tile, selected)
                elif tile is None or "catmxy" not in tile.files:
                    status = "Catchment selection unavailable: no catmxy in selected source"
                kind = "catchment"
            self.selection = SelectionState(
                kind=kind,
                clicked=(lon, lat),
                tile_key=tile.key if tile else None,
                native_pixel=pixel,
                river_cell=selected,
                boundary=boundary,
                status=status,
                coarse_outline=coarse_cell_outline(self.reader.geometry, *selected) if selected is not None else None,
                method=method,
                geographic_cell=coarse,
            )
            self.selected = self.selection.river_cell
        state = self.selection
        result = {
            "clicked longitude": state.clicked[0] if state.clicked else lon,
            "clicked latitude": state.clicked[1] if state.clicked else lat,
            "selection method": state.method,
            "selection status": state.status,
        }
        if state.geographic_cell is not None:
            result["clicked coarse ix (1-based)"] = state.geographic_cell[1] + 1
            result["clicked coarse iy (1-based)"] = state.geographic_cell[0] + 1
        if state.clicked and state.kind == "catchment" and state.tile_key is not None:
            extra, _ = self.scene.inspect(*state.clicked, state.tile_key, cog_only=True)
            assigned_area = extra.get("assigned uparea [m2]")
            result["clicked assigned catchment uparea [km²]"] = assigned_area * 1e-6 if assigned_area is not None else None
            # Raw native assignment is informative in either mode. Attributes
            # below belong only to the selected grid, never a different clicked
            # pixel's assigned grid; catmxy and nextxy have distinct roles.
            result.update(
                {
                    key: value
                    for key, value in extra.items()
                    if not key.startswith("assigned ") or key.startswith("assigned coarse ")
                }
            )
        if state.river_cell is not None:
            row, col = state.river_cell
            g = self.reader.geometry
            result.update(self.reader.inspect(g.lon[col], g.lat[row]))
            result["network representation"] = self.representation.value
            name = network_product or self.network_choice.value
            if name != "off":
                if name not in self._networks:
                    self._networks[name] = RiverNetwork(self.reader, name)
                net = self._networks[name]
            else:
                net = self._network_cache
            if net is None and "nextxy" in self.reader.network_sources:
                name = "nextxy"
                self._network_cache = net = RiverNetwork(self.reader, name)
            if net is not None:
                result["network product"] = net.product
                result.update(net.inspect(row, col))
                nx, ny = int(net.nextx[row, col]), int(net.nexty[row, col])
                if self.representation.value == "outlet_vector" and self.scene.products.outlet_source:
                    a, b = self.scene.products.outlets
                    for key, value in [
                        ("source outlet longitude", a[row, col]),
                        ("source outlet latitude", b[row, col]),
                    ]:
                        result[key] = float(value) if np.isfinite(value) else None
                    if 1 <= nx <= g.nx and 1 <= ny <= g.ny:
                        result["downstream outlet longitude"] = (
                            float(a[ny - 1, nx - 1]) if np.isfinite(a[ny - 1, nx - 1]) else None
                        )
                        result["downstream outlet latitude"] = (
                            float(b[ny - 1, nx - 1]) if np.isfinite(b[ny - 1, nx - 1]) else None
                        )
            self._highlight(row, col)
            self.selection_summary.object = ""  # Filled from the shared Inspector source attributes below.
        else:
            # No containing-cell fallback for unassigned catchment pixels.
            self.selected_source.data = dict(x=[], y=[])
            self.selected_link.data = dict(x0=[], y0=[], x1=[], y1=[], angle=[])
            self.selection_summary.object = (
                f"**No mapped river cell:** {state.status}; native assignment codes are shown in Inspector."
            )
        if state.boundary is not None:
            result["unit catchment assigned pixel count"] = state.boundary.pixel_count
            result["unit catchment pixel count scope"] = "visible native window"
            result["selected boundary"] = "Native exposed edges; " + str(len(state.boundary.segments)) + " merged runs"

        self._render_catchment_selection()

        self.cell_inspector.update(state, result, net if state.river_cell is not None else None)
        if state.river_cell is not None:
            row, col = state.river_cell
            label = "Grid" if self.point_select.value == "grid" else "Unit Catchment"

            def number(key, factor=1, digits=5):
                value = result.get(key)
                return (
                    "Unavailable"
                    if value is None or not np.isfinite(value)
                    else (f"{value*factor:,.9g}" if digits == 3 else f"{value*factor:,.{digits}f}")
                )

            outlet_lat = number("source outlet latitude")
            outlet_lon = number("source outlet longitude")
            outlet_lat += "°" if outlet_lat != "Unavailable" else ""
            outlet_lon += "°" if outlet_lon != "Unavailable" else ""
            area = number("uparea [m2]", 1e-6, 3)
            method = "geographic containment" if self.point_select.value == "grid" else "catmxy assignment"
            count = f" · {state.boundary.pixel_count:,} high-res pixels in visible window" if state.boundary is not None else ""
            self.selection_summary.object = (
                f"**Selected {label}:** ix={col+1}, iy={row+1} (1-based Fortran) · "
                f"**Outlet (lat, lon):** {outlet_lat}, {outlet_lon} · **Upstream Area:** {area} km²  \n"
                f"Selection: {method}{count}"
            )
        self._selection_values = result
        if hasattr(self, "pins"):
            active = self.pins.current()
            if active is not None and (
                active.cell != state.river_cell or active.mode != self.point_select.value
                or active.tile != state.tile_key or active.clicked != state.clicked
            ):
                self.pins.active = None
                self.pins.refresh()
        return result

    def _tap(self, event):
        def select():
            if not self.pins.hit(event.x, event.y):
                self.pins.active = None
                self.inspect(event.x, event.y)
                self.pins.refresh()

        self._guard(select)

    def _output(self, suffix):
        return self.output_dir / f"map-explorer-{self.reader.path.name}-{datetime.now():%Y%m%d-%H%M%S-%f}{suffix}"

    def export(self):
        if self._background_error is not None:
            raise ValueError(self._background_error)
        if self.frame is None:
            self.render_view()
        frame = replace(self.frame,legend=list(self.frame.legend))  # Export the displayed COG LOD and image, not a fresh higher-resolution sample.
        point = None
        segments = None
        if self.selected is not None:
            self._highlight(*self.selected)
            point = (self.selected_source.data["x"][0], self.selected_source.data["y"][0])
            data = self.selected_link.data
            segments = np.stack(
                [np.column_stack([data["x0"], data["y0"]]), np.column_stack([data["x1"], data["y1"]])], axis=1
            )
        if self.show_osm.value:
            frame.legend.append("Online basemap excluded from PNG; scientific layers and selection retained")
        path = export_scene(
            self.reader,
            frame,
            self.extent,
            self._output(".png"),
            point,
            segments,
            self.selection.boundary,
            self.selection.coarse_outline,
            pins=self.pins.marker_data(),
        )
        self.status.object = f"**PNG saved:** `{path}`" + (" · Online basemap excluded." if self.show_osm.value else "")
        return path

    def settings(self):
        layers = {key:value for key,value in self.scene_options().items() if key not in ("screen","automatic_selection")}
        layers.pop("network_style")
        layers["representation"] = self.representation.value
        return dict(
            version=2,
            map_path=str(self.reader.path),
            variable=self.variable.value,
            extent=list(self.extent),
            scale=self.scale.value,
            palette=self.palette.value,
            limits=None if self.auto_limits.value else [self.low.value, self.high.value],
            network=self.network_choice.value,
            network_options=self.network_options(),
            layers=layers,
            background_ui=self.background_ui.configuration(),
            point_select=self.point_select.value,
            basemap=dict(show=self.show_osm.value, opacity=self.osm_opacity.value / 100),
            viewport=dict(aspect=self.map_aspect.value, frame_ratio=self._frame_ratio),
        )

    def save(self):
        path = save_settings(self._output(".json"), self.settings())
        self.status.object = f"**Settings saved:** `{path}`"
        return path

    def load(self, content):
        if not content:
            return
        data = load_settings(content, self.reader)
        self._applied_preset = None
        self._preset_baseline = None
        # Validate the complete display before mutating widgets/session state.
        make_layer(
            self.reader,
            data["variable"],
            data["scale"],
            data["palette"],
            data["limits"],
            reference_policy=data.get("layers", {}).get("auto_limits_policy", "gallery"),
        )
        self._updating = True
        try:
            self.point_select.value = data["point_select"]
            self.show_osm.value = data["basemap"]["show"]
            self.osm_opacity.value = round(data["basemap"]["opacity"] * 100)
            self.variable.value, self.scale.value, self.palette.value = data["variable"], data["scale"], data["palette"]
            self.auto_limits.value = data["limits"] is None
            if data["limits"] is not None:
                self.low.value, self.high.value = data["limits"]
            self.network_choice.value = data["network"]
            options = data["network_options"]
            layers = data.get("layers", {})
            self.auto_limits_policy = layers.get("auto_limits_policy", "gallery")
            self.background_method = layers.get("background_method", "default")
            self.network_geometry = layers.get("network_geometry", "straight")
            self.river_ui.detail.value = layers.get("network_detail", "all")
            self.river_ui.budget.value = layers.get("network_budget", 5000)
            self.river_ui.budget.disabled = self.river_ui.detail.value != "auto"
            self.map_aspect.value = data["viewport"]["aspect"]
            self._frame_ratio = data["viewport"]["frame_ratio"]
            self.classification.value = options.get("classification", "fixed")
            self.area_palette.value = options.get("area_palette", "viridis")
            self.background.value = layers.get("background", "coarse")
            self.hires_source.value = layers.get("tile", self.hires_source.value)
            self.terrain_palette.value = layers.get("terrain_palette", "gray")
            self.representation.value = layers.get("representation", "grid_center")
            self.arrow_size.value = layers.get("arrow_size", 7 if layers.get("arrows", False) else 0)
            self.arrows.value = self.arrow_size.value > 0
            self.river_ui.color_style = options.get("area_color_style", "palette")
            self.river_ui.scale.value = options.get("area_scale", "log")
            self.river_ui.auto.value = options.get("area_limits") is None
            if options.get("area_limits") is not None:
                self.river_ui.low.value, self.river_ui.high.value = options["area_limits"]
            self._auto_channel_initialized = True
            for k, w in self.overlay_controls.items():
                w.value = layers.get("overlays", {}).get(k, OVERLAY_DEFAULTS[k])
            self.color_mode.value = (
                "upstream_area" if options["color_area"] else "connection_type" if options["distinguish"] else "uniform"
            )
            self.width_mode.value = "upstream_area" if options["scale_width"] else "uniform"
            for widget, key in [
                (self.width, "width"),
                (self.color, "color"),
                (self.flex_color, "flexible_color"),
                (self.distinguish, "distinguish"),
                (self.area_width, "scale_width"),
                (self.area_color, "color_area"),
            ]:
                widget.value = options[key]
        finally:
            self._updating = False
        self.background_ui.adopt_legacy(data)
        self._update_assignment_controls()
        self.set_extent(data["extent"], preserve_aspect=True)
        self.view_note.object = (
            "Loaded Custom geographic extent; saved bounds remain authoritative."
            if self.map_aspect.value == "custom"
            else "Loaded frame preference and exact saved extent; geographic differences use letterboxing."
        )
        self.update_layer()
        self.update_network()
        self.status.object = "**Settings loaded.** " + "; ".join(data.get("_warnings", []))

    def _describe_preset(self):
        identity = self.preset_choice.value
        if identity is None or identity not in self.preset_library.presets:
            self.apply_preset_button.disabled = True
            self.preset_description.object = "<p>" + escape("; ".join(self.preset_library.messages)) + "</p>"
            return
        row, meta = self.preset_library.presets[identity]
        from urllib.parse import quote

        link = "https://github.com/global-hydrodynamics/cmf_v5_beta/blob/main/visualization/" + quote(
            meta["documentation"], safe="/#-_."
        )
        description = meta.get("purpose") or meta.get("description", "")
        missing = self.preset_library.missing_products(identity, self.reader, self.scene)
        self.apply_preset_button.disabled = bool(missing)
        message = '<p style="color:#a22"><b>Missing:</b> ' + escape(", ".join(missing)) + "</p>" if missing else ""
        self.preset_description.object = (
            f'<small><b>{escape(identity)}</b> · {escape(description)} <a href="{link}" target="_blank">Gallery documentation</a></small>'
            + message
        )

    def _display_state(self):
        value = self.settings()
        value.pop("extent", None)
        value.pop("viewport", None)  # Navigation/frame shape is not Gallery science.
        value.pop("background_ui", None)  # Inactive UI choices are not displayed science.
        return value

    def _check_preset_modified(self):
        if not hasattr(self, "preset_status"):
            return
        if self._applied_preset is None:
            self.preset_status.object = "Custom settings"
        elif self._display_state() != self._preset_baseline:
            self.preset_status.object = f"**Custom (modified from {self._applied_preset})**"
        else:
            self.preset_status.object = f"**Gallery preset {self._applied_preset} applied**"

    def apply_startup_defaults(self, *, use_gallery_extent=True):
        """One-time desktop/server default using the canonical Gallery preset."""
        identity = "p01-f04b"
        if identity not in self.preset_library.presets:
            self.preset_status.object = "**Startup p01-f04b unavailable:** Gallery metadata is missing."
            return
        missing = self.preset_library.missing_products(identity, self.reader, self.scene)
        if missing:
            self.status.object = "**Startup p01-f04b unavailable:** " + ", ".join(missing)
            self.preset_status.object = self.status.object
            return
        row, _ = self.preset_library.presets[identity]
        try:
            self.reader.geometry.validate_extent([row[k] for k in ("west", "east", "south", "north")])
            use_extent = use_gallery_extent
        except ValueError:
            use_extent = False
        base = self.settings()
        self.preset_choice.value = identity
        try:
            self.apply_preset(identity, use_gallery_extent=use_extent)
        except (ValueError, OSError) as exc:
            self.load(json.dumps(base).encode())
            self.status.object = "**Startup p01-f04b unavailable:** " + str(exc)
            self.preset_status.object = self.status.object
            return
        self.status.object = "**Startup:** p01-f04b (Channel + Overland bifurcations)."

    def apply_preset(self, identity=None, use_gallery_extent=None):
        identity = identity or self.preset_choice.value
        if identity not in self.preset_library.presets:
            raise ValueError("No supported Gallery preset selected")
        use_extent = self.preset_extent.value if use_gallery_extent is None else use_gallery_extent
        state = self.preset_library.state(identity, self, gallery_extent=use_extent)
        # Config validation and make_layer run before widget mutation in load.
        self.load(json.dumps(state).encode())
        self._applied_preset = identity
        self._preset_baseline = json.loads(json.dumps(self._display_state()))
        self._check_preset_modified()
        self.status.object = f"**Applied {identity}.** " + (
            "Gallery extent requested." if use_extent else "Current viewport preserved."
        )
        return state


def create_app(map_dir=None, output_dir=None):
    from map_session import ExplorerSession

    try:
        session = ExplorerSession(map_dir, output_dir, factory=Explorer)
        pn.state.on_session_destroyed(lambda session_context: session.close())
        return session.view
    except (ValueError, OSError) as exc:
        return pn.pane.Alert(f"Cannot open map: {escape(str(exc))}", alert_type="danger")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_dir", nargs="?", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--port", type=int, default=5006)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    # Explicit server resources prevent CDN access after dependencies install.
    import os

    os.environ["BOKEH_RESOURCES"] = "server"
    print(f"Map Explorer: http://127.0.0.1:{args.port}/ (Ctrl-C to stop)", flush=True)
    pn.serve(
        lambda: create_app(args.map_dir),
        address="127.0.0.1",
        port=args.port,
        show=not args.no_browser,
        title="CaMa-Flood Map Explorer",
    )


if __name__ == "__main__":
    main()
