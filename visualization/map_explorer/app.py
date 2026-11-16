"""Local Panel/Bokeh map explorer; every browser session owns its state."""

from __future__ import annotations

import argparse
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
    HoverTool,
    LinearColorMapper,
    LogColorMapper,
    Range1d,
    TapTool,
)
from bokeh.plotting import figure

from config import load_settings, save_settings
from map_layers import colorize, export_png, make_layer, network_style, raster_subset
from map_reader import MapReader, SCHEMA
from river_network import RiverNetwork, intersects
from selection import SelectionState, CatchmentIndex
from presets import PresetLibrary
from scene import Scene, OVERLAY_DEFAULTS, export_scene

pn.extension()


class Explorer:
    def __init__(self, map_dir, output_dir=None):
        self.reader = MapReader(map_dir)
        self.scene = Scene(self.reader)
        self._networks = {}
        self._auto_channel_initialized = False
        self.frame = None
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
        self.status = pn.pane.Markdown("", width=295)
        self.network_summary = pn.pane.Markdown("")
        self.inspection = pn.pane.HTML(
            "<p>Click a cell to inspect native values and stored downstream indices.</p>", width=320
        )
        self.variable = pn.widgets.Select(
            name="Raster variable", options={f"{k} · {SCHEMA[k].title}": k for k in self.reader.sources}
        )
        self.scale = pn.widgets.Select(name="Color scale (continuous only)", options=["auto", "linear", "log"])
        self.palette = pn.widgets.Select(
            name="Continuous palette",
            options=["viridis", "terrain", "magma", "Blues", "YlGnBu", "basin_pastel", "subcol_pastel", "subcol_gray"],
        )
        self.auto_limits = pn.widgets.Checkbox(name="Automatic color limits", value=True)
        self.low = pn.widgets.FloatInput(name="Color minimum", value=0, width=140)
        self.high = pn.widgets.FloatInput(name="Color maximum", value=1, width=140)
        self.network_choice = pn.widgets.Select(
            name="Stored network",
            options=["off", *self.reader.network_sources],
            value="nextxy" if "nextxy" in self.reader.network_sources else "off",
        )
        self.width = pn.widgets.FloatSlider(name="Link width", start=0.2, end=4, step=0.2, value=1)
        self.color = pn.widgets.ColorPicker(name="Local / all links", value="#172b4d", width=140)
        self.flex_color = pn.widgets.ColorPicker(name="Flexible links", value="#e67e22", width=140)
        self.distinguish = pn.widgets.Checkbox(name="Distinguish Flexible Downstream", value=True)
        self.area_width = pn.widgets.Checkbox(
            name="Width by upstream area (not discharge)", value=False, disabled="uparea" not in self.reader.sources
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
        self.hires_source = pn.widgets.Select(name="High-resolution source", options=list(self.scene.tiles) or [None])
        self.terrain_palette = pn.widgets.Select(
            name="Terrain palette (full-tile P2/P98)", options=["gray", "pale_terrain"]
        )
        self.representation = pn.widgets.Select(
            name="Main network representation",
            options=["off", "grid_center"] + (["outlet_vector"] if self.scene.products.outlet_source else []),
            value="grid_center",
        )
        self.color_mode = pn.widgets.Select(
            name="Network color", options=["uniform", "connection_type", "upstream_area"], value="connection_type"
        )
        self.width_mode = pn.widgets.Select(name="Network width", options=["uniform", "upstream_area"])
        self.classification = pn.widgets.Select(
            name="Full-map contributing-area classes",
            options=["quartiles", "six_log", "continuous", "fixed"],
            value="quartiles",
        )
        self.area_palette = pn.widgets.Select(name="Network area palette", options=["viridis", "shade_rainbow"])
        self.arrows = pn.widgets.Checkbox(name="Downstream direction heads (zoomed views)", value=False)
        self.overlay_controls = {}
        for key, value in OVERLAY_DEFAULTS.items():
            if isinstance(value, bool):
                self.overlay_controls[key] = pn.widgets.Checkbox(name=key.replace("_", " ").title(), value=value)
            elif isinstance(value, str):
                self.overlay_controls[key] = pn.widgets.ColorPicker(name=key.replace("_", " ").title(), value=value)
            else:
                self.overlay_controls[key] = pn.widgets.FloatSlider(
                    name="Bifurcation width", start=0.2, end=5, step=0.1, value=value
                )
        self.legend = pn.pane.HTML("", sizing_mode="stretch_width")
        self.extent_inputs = [
            pn.widgets.FloatInput(name=k, value=v, width=140)
            for k, v in zip(["West", "East", "South", "North"], self.reader.geometry.extent)
        ]
        self.apply_extent_button = pn.widgets.Button(name="Apply extent", button_type="primary")
        self.reset_button = pn.widgets.Button(name="Full map")
        self.export_button = pn.widgets.Button(name="Export current view · PNG", button_type="primary")
        self.save_button = pn.widgets.Button(name="Save settings · JSON")
        self.upload = pn.widgets.FileInput(name="Load settings JSON", accept=".json")
        choices = {f"{key} · {meta['title']}": key for key, (row, meta) in self.preset_library.presets.items()}
        self.preset_choice = pn.widgets.Select(
            name="Gallery visualization", options=choices or {"Unavailable": None}, sizing_mode="stretch_width"
        )
        self.preset_description = pn.pane.HTML("", sizing_mode="stretch_width")
        self.preset_status = pn.pane.Markdown("Custom settings", sizing_mode="stretch_width")
        self.preset_extent = pn.widgets.Checkbox(name="Apply suggested Gallery extent", value=False)
        self.apply_preset_button = pn.widgets.Button(name="Apply preset", button_type="primary")
        self.settings_toggle = pn.widgets.Toggle(name="Settings panel", value=True, width=135)
        self.coordinate = Div(text="Pointer: longitude / latitude", width=300)
        self.selection_summary = pn.pane.Markdown(
            "Click a map cell; detailed native values appear in **Cell inspector**."
        )
        g = self.reader.geometry
        self.plot = figure(
            x_range=Range1d(g.west, g.east),
            y_range=Range1d(g.south, g.north),
            tools="pan,wheel_zoom,box_zoom,reset,tap,save",
            active_scroll="wheel_zoom",
            title="CaMa-Flood · Map Explorer",
            x_axis_label="Longitude [°]",
            y_axis_label="Latitude [°]",
            background_fill_color="#f5f7fa",
            toolbar_location="above",
            sizing_mode="stretch_width",
            min_width=260,
        )
        self.plot.toolbar.logo = None
        resize = CustomJS(
            args={"plot": self.plot},
            code="""
            const w = plot.x_range.end - plot.x_range.start;
            const h = plot.y_range.end - plot.y_range.start;
            const mid = (plot.y_range.start + plot.y_range.end) / 2;
            const ratio = w * Math.max(0.05, Math.cos(mid * Math.PI / 180)) / h;
            if (plot.inner_width > 0 && ratio > 0)
                plot.frame_height = Math.max(1, Math.round(plot.inner_width / ratio));
        """,
        )
        self.plot.js_on_change("inner_width", resize)
        self.image_source = ColumnDataSource(dict(image=[], x=[], y=[], dw=[], dh=[]))
        self.mapper = LinearColorMapper(palette=["#ffffff", "#000000"], low=0, high=1, nan_color="#f5f7fa")
        self.raster = self.plot.image_rgba(image="image", x="x", y="y", dw="dw", dh="dh", source=self.image_source)
        self.raster.nonselection_glyph = self.raster.glyph
        self.raster.selection_glyph = self.raster.glyph
        # Tap is an inspection gesture, not a selection of scientific layers.
        # Restrict Bokeh selection so clicking does not fade network/overlay glyphs.
        self.plot.select_one(TapTool).renderers = [self.raster]
        self.bar = ColorBar(color_mapper=self.mapper, title="")
        self.plot.add_layout(self.bar, "right")
        self.link_source = ColumnDataSource(dict(x0=[], y0=[], x1=[], y1=[], width=[], color=[]))
        self.plot.segment("x0", "y0", "x1", "y1", line_width="width", line_color="color", source=self.link_source)
        self.overlay_source = ColumnDataSource(dict(x0=[], y0=[], x1=[], y1=[], width=[], color=[]))
        self.plot.segment("x0", "y0", "x1", "y1", source=self.overlay_source, line_width="width", line_color="color")
        self.outlet_source = ColumnDataSource(dict(x=[], y=[]))
        self.plot.scatter(
            "x", "y", source=self.outlet_source, size=4, fill_color="white", line_color="#555555", line_width=0.5
        )
        self.arrow_source = ColumnDataSource(dict(x=[], y=[], angle=[], color=[]))
        self.plot.scatter(
            "x",
            "y",
            source=self.arrow_source,
            marker="triangle",
            angle="angle",
            fill_color="color",
            line_color="color",
            size=7,
        )
        self.selected_source = ColumnDataSource(dict(x=[], y=[]))
        self.plot.scatter(
            "x", "y", source=self.selected_source, size=15, line_color="#e11d48", fill_alpha=0, line_width=3
        )
        self.selected_link = ColumnDataSource(dict(x0=[], y0=[], x1=[], y1=[]))
        self.plot.segment("x0", "y0", "x1", "y1", source=self.selected_link, line_color="#e11d48", line_width=3)
        # Separate from ordinary catchment outlines; source remains mounted.
        self.selection_boundary_source = ColumnDataSource(dict(x0=[], y0=[], x1=[], y1=[]))
        self.selection_boundary_renderer = self.plot.segment(
            "x0",
            "y0",
            "x1",
            "y1",
            source=self.selection_boundary_source,
            line_color="#ff00a8",
            line_width=2.8,
            name="selected-unit-catchment",
        )
        self.plot.add_tools(HoverTool(tooltips=[("lon", "$x{0.0000}"), ("lat", "$y{0.0000}")], renderers=[self.raster]))
        self.plot.js_on_event(
            "mousemove",
            CustomJS(
                args={"target": self.coordinate},
                code="target.text = `Pointer: ${cb_obj.x.toFixed(4)}°, ${cb_obj.y.toFixed(4)}°`;",
            ),
        )
        self.plot.on_event(Tap, self._tap)
        self.plot.on_event(RangesUpdate, self._navigation)
        self.apply_extent_button.on_click(lambda event: self._schedule(self.apply_extent))
        self.reset_button.on_click(lambda event: self._schedule(lambda: self.set_extent(g.extent)))
        self.export_button.on_click(lambda event: self._schedule(self.export))
        self.save_button.on_click(lambda event: self._schedule(self.save))
        self.upload.param.watch(lambda event: self._schedule(lambda: self.load(event.new)), "value")
        for widget in (self.variable, self.scale, self.palette, self.auto_limits, self.low, self.high):
            widget.param.watch(lambda event: self._schedule(self.update_layer), "value")
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
            widget.param.watch(lambda event: self._schedule(self.update_layer), "value")
        for widget in (self.representation, self.classification, self.area_palette, self.arrows):
            widget.param.watch(lambda event: self._schedule(self.update_network), "value")
        for widget in (self.color_mode, self.width_mode):
            widget.param.watch(lambda event: self._schedule(self._style_modes), "value")
        for widget in self.overlay_controls.values():
            widget.param.watch(lambda event: self._schedule(self.render_view), "value")
        self.hires_source.param.watch(lambda event: self._schedule(self._hires_changed), "value")
        self.preset_choice.param.watch(lambda event: self._schedule(self._describe_preset), "value")
        self.apply_preset_button.on_click(lambda event: self._schedule(self.apply_preset))
        background_controls = pn.Column(
            self.background,
            self.variable,
            self.hires_source,
            self.terrain_palette,
            self.scale,
            self.palette,
            self.auto_limits,
            pn.Row(self.low, self.high),
            self.overlay_controls["catchment_boundaries"],
            self.overlay_controls["channel_pixels"],
            width=330,
        )
        network_controls = pn.Column(
            self.network_choice,
            self.representation,
            self.color_mode,
            self.width_mode,
            self.classification,
            self.area_palette,
            self.width,
            pn.Row(self.color, self.flex_color),
            self.arrows,
            width=330,
        )
        overlay_controls = pn.Column(
            *(
                self.overlay_controls[k]
                for k in [
                    "channel",
                    "overland",
                    "outlets",
                    "headwater",
                    "coarse_grid",
                    "channel_color",
                    "overland_color",
                    "bif_width",
                    "bif_classes",
                ]
            ),
            width=330,
        )
        navigation = pn.Column(
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
            pn.pane.Markdown("### Native cell inspection · 1-based indices"),
            self.inspection,
            pn.pane.HTML(diagnostics, width=320),
            width=350,
        )
        self.right_tabs = pn.Tabs(
            ("Background", background_controls),
            ("River", network_controls),
            ("Overlays", overlay_controls),
            ("Inspector", details),
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
        self.settings_panel = pn.Column(
            preset_box,
            self.right_tabs,
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
        self.map_region = pn.Column(
            self.coordinate,
            self.selection_summary,
            self.plot,
            self.legend,
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
        self.view = pn.Column(
            pn.Row(header, pn.Spacer(sizing_mode="stretch_width"), self.settings_toggle, sizing_mode="stretch_width"),
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
        if self._updating:
            return
        document = self.plot.document
        if document is not None and document.session_context is not None:
            document.add_next_tick_callback(lambda: self._guard(function))
        else:
            self._guard(function)

    def _guard(self, function):
        if self._updating:
            return
        try:
            function()
        except (ValueError, OSError, KeyError, TypeError) as exc:
            self.status.object = f'**Error:** {escape(str(exc))}'

    @property
    def extent(self):
        return self.plot.x_range.start, self.plot.x_range.end, self.plot.y_range.start, self.plot.y_range.end

    def _size_map(self):
        w, e, s, n = self.extent
        ratio = (e-w)*max(.05, np.cos(np.deg2rad((s+n)/2)))/(n-s)
        # Set the inner frame, not the whole widget, so axes/colorbar do not
        # distort geographic aspect. This is local equirectangular geometry.
        # Bokeh reports actual inner width only after a browser has laid out
        # the plot. Programmatic/headless sessions must still render data.
        try:
            width = self.plot.inner_width or 425
        except ValueError:
            width = 425
        self.plot.frame_height = max(1, int(width/ratio))

    def set_extent(self, extent):
        self.reader.geometry.validate_extent(extent)
        w, e, s, n = extent
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
        extent = (max(g.west, event.x0), min(g.east, event.x1),
                  max(g.south, event.y0), min(g.north, event.y1))
        if extent[0] >= extent[1] or extent[2] >= extent[3]:
            extent = g.extent
        self._guard(lambda: self.set_extent(extent))

    def update_layer(self):
        name = self.variable.value
        if not SCHEMA[name].categorical and self.palette.value in ("basin_pastel", "subcol_pastel", "subcol_gray"):
            self._updating = True
            self.palette.value = "viridis"
            self._updating = False
        layer = make_layer(
            self.reader,
            name,
            self.scale.value,
            self.palette.value,
            None if self.auto_limits.value else (self.low.value, self.high.value),
        )
        self.layer = layer
        self._updating = True
        try:
            for widget in (self.scale, self.palette, self.auto_limits):
                widget.disabled = SCHEMA[name].categorical
            self.low.disabled = self.high.disabled = self.auto_limits.value or SCHEMA[name].categorical
            if self.auto_limits.value:
                self.low.value, self.high.value = layer.low, layer.high
        finally:
            self._updating = False
        self._set_colorbar(layer)
        self.plot.title.text = layer.label
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
        self.mapper = cls(palette=layer.palette, low=layer.low, high=layer.high, nan_color='#f5f7fa')
        self.bar.color_mapper = self.mapper
        self.bar.title = 'Elevation diff. [m]' if layer.label.startswith('Maximum') else layer.label.split(' —')[0]
        if len(layer.categories):
            ticks = np.unique(np.linspace(0, len(layer.categories)-1, min(16, len(layer.categories))).astype(int))
            self.bar.ticker = FixedTicker(ticks=ticks.tolist())
            self.bar.major_label_overrides = {int(i): str(int(layer.categories[i])) for i in ticks}
        else:
            from bokeh.models import BasicTicker, LogTicker
            self.bar.ticker = LogTicker() if layer.logarithmic else BasicTicker()
            self.bar.major_label_overrides = {}

    def _style_modes(self):
        self._updating = True
        try:
            self.area_color.value = self.color_mode.value == 'upstream_area'
            self.distinguish.value = self.color_mode.value == 'connection_type'
            self.area_width.value = self.width_mode.value == 'upstream_area'
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
        self.render_view()
        if self.selected is not None:
            if hasattr(self, "_last_click"):
                self.inspect(*self._last_click, resolve_selection=False)
            else:
                self._highlight(*self.selected)

    def scene_options(self):
        return dict(background=self.background.value,tile=self.hires_source.value,terrain_palette=self.terrain_palette.value,
                    network_style=self.network_options(),arrows=self.arrows.value,
                    overlays={k:widget.value for k,widget in self.overlay_controls.items()})

    def render_view(self):
        if self.layer is None:
            return
        self._size_map()
        self.frame = frame = self.scene.build(
            self.extent, self.variable.value, self.layer, self.network, self.scene_options()
        )
        self._set_colorbar(frame.layer)
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
        self.image_source.data = dict(
            image=[np.ascontiguousarray(a[::-1]) for a, e in frame.images],
            x=[e[0] for a, e in frame.images],
            y=[e[2] for a, e in frame.images],
            dw=[e[1] - e[0] for a, e in frame.images],
            dh=[e[3] - e[2] for a, e in frame.images],
        )
        self.link_source.data = frame.main
        combined = dict(x0=[], y0=[], x1=[], y1=[], width=[], color=[])
        for segments, color, width, label in frame.overlays:
            for key, values in [
                ("x0", segments[:, 0, 0]),
                ("y0", segments[:, 0, 1]),
                ("x1", segments[:, 1, 0]),
                ("y1", segments[:, 1, 1]),
                ("width", np.broadcast_to(width, (len(segments),))),
                ("color", np.full(len(segments), color)),
            ]:
                combined[key].extend(values.tolist())
        self.overlay_source.data = combined
        self.outlet_source.data = dict(x=frame.points[:, 0], y=frame.points[:, 1])
        self.arrow_source.data = frame.arrows
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

    def _render_catchment_selection(self):
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

    def _hires_changed(self):
        self._reconcile_selection_source()
        self.update_layer()

    def _clear_selection(self, message):
        self.selection = SelectionState(status=message)
        self.selected = None
        if hasattr(self, "_last_click"):
            del self._last_click
        self.selected_source.data = dict(x=[], y=[])
        self.selected_link.data = dict(x0=[], y0=[], x1=[], y1=[])
        self.selection_boundary_source.data = dict(x0=[], y0=[], x1=[], y1=[])
        self.selection_summary.object = message
        self.inspection.object = escape(message)

    def _reconcile_selection_source(self):
        if self.selection.tile_key is not None and self.selection.tile_key != self.hires_source.value:
            self._clear_selection("High-resolution source changed; previous selection cleared. Click to select again.")

    def _highlight(self,row,col):
        g=self.reader.geometry
        x,y=g.lon[col],g.lat[row]
        if self.representation.value=='outlet_vector' and self.scene.products.outlet_source:
            a,b=self.scene.products.outlets
            if np.isfinite(a[row,col]) and np.isfinite(b[row,col]):
                x,y=a[row,col],b[row,col]
        self.selected_source.data=dict(x=[x],y=[y])
        if self.network is not None:
            net=self.network
            ids=np.flatnonzero((net.rows[net.link_index]==row)&(net.cols[net.link_index]==col))
            self.selected_link.data=dict(x0=net.x0[ids],y0=net.y0[ids],x1=net.x1[ids],y1=net.y1[ids])
        else:
            self.selected_link.data=dict(x0=[],y0=[],x1=[],y1=[])

    def inspect(self, lon, lat, resolve_selection=True):
        if resolve_selection:
            self._last_click = (lon, lat)
            coarse = self.reader.geometry.cell(lon, lat)
            if coarse is None:
                raise ValueError("Click is outside the map")
            tile = self.scene.tiles.get(self.hires_source.value)
            pixel = tile.geometry.cell(lon, lat) if tile else None
            if self.background.value == "catchment":
                extra, assigned = self.scene.inspect(lon, lat, self.hires_source.value)
                boundary = None
                if assigned is not None and tile is not None:
                    if tile.key not in self._selection_indexes:
                        self._selection_indexes[tile.key] = CatchmentIndex(tile, self.reader.geometry)
                    boundary = self._selection_indexes[tile.key].boundary(*assigned)
                self.selection = SelectionState(
                    "catchment",
                    (lon, lat),
                    self.hires_source.value,
                    pixel,
                    assigned,
                    boundary,
                    extra.get("assignment status", "No supported catmxy assignment"),
                )
            else:
                terrain = self.background.value in ("elevtn", "flddif", "difference")
                self.selection = SelectionState(
                    "terrain" if terrain else "coarse",
                    (lon, lat),
                    self.hires_source.value if terrain else None,
                    pixel if terrain else None,
                    coarse,
                    None,
                    "Native terrain pixel; containing coarse cell" if terrain else "Containing coarse cell",
                )
            self.selected = self.selection.river_cell
        state = self.selection
        result = {
            "clicked longitude": state.clicked[0] if state.clicked else lon,
            "clicked latitude": state.clicked[1] if state.clicked else lat,
            "selection status": state.status,
        }
        if state.kind in ("catchment", "terrain") and state.clicked:
            extra, _ = self.scene.inspect(*state.clicked, state.tile_key)
            result.update(extra)
        if state.river_cell is not None:
            row, col = state.river_cell
            g = self.reader.geometry
            result.update(self.reader.inspect(g.lon[col], g.lat[row]))
            result["network representation"] = self.representation.value
            net = self.network or self._network_cache
            if net is None and self.reader.network_sources:
                name = "nextxy" if "nextxy" in self.reader.network_sources else next(iter(self.reader.network_sources))
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
            self.selection_summary.object = (
                f"**Selected river cell (1-based):** ix={col+1}, iy={row+1} · {state.status}"
            )
        else:
            # No containing-cell fallback for unassigned catchment pixels.
            self.selected_source.data = dict(x=[], y=[])
            self.selected_link.data = dict(x0=[], y0=[], x1=[], y1=[])
            self.selection_summary.object = (
                f"**No mapped river cell:** {state.status}; native assignment codes are shown in Inspector."
            )
        if state.boundary is not None:
            result["unit catchment assigned pixel count"] = state.boundary.pixel_count
            result["selected boundary"] = "Native exposed edges; " + str(len(state.boundary.segments)) + " merged runs"
            self.selection_summary.object += (
                f" · **{state.boundary.pixel_count:,} native catchment pixels** · magenta outline"
            )
        self._render_catchment_selection()
        rows = "".join(
            f'<tr><td style="padding:4px;border-bottom:1px solid #ddd">{escape(k)}</td><td style="padding:4px;border-bottom:1px solid #ddd">{escape("missing" if v is None else str(v))}</td></tr>'
            for k, v in result.items()
        )
        self.inspection.object = f'<table style="width:100%;font-size:12px">{rows}</table><p>Native values. Magenta = stored assignment boundary; pink = river cell/outlet and downstream link. catmxy is assignment; nextxy is connectivity.</p>'
        return result

    def _tap(self, event):
        self._guard(lambda: self.inspect(event.x, event.y))

    def _output(self, suffix):
        return self.output_dir / f'map-explorer-{datetime.now():%Y%m%d-%H%M%S-%f}{suffix}'

    def export(self):
        frame = self.scene.build(
            self.extent, self.variable.value, self.layer, self.network, self.scene_options(), max_side=2400
        )
        point = None
        segments = None
        if self.selected is not None:
            self._highlight(*self.selected)
            point = (self.selected_source.data["x"][0], self.selected_source.data["y"][0])
            data = self.selected_link.data
            segments = np.stack(
                [np.column_stack([data["x0"], data["y0"]]), np.column_stack([data["x1"], data["y1"]])], axis=1
            )
        path = export_scene(
            self.reader, frame, self.extent, self._output(".png"), point, segments, self.selection.boundary
        )
        self.status.object = f"**PNG saved:** `{path}`"
        return path

    def settings(self):
        layers=self.scene_options()
        layers.pop('network_style')
        layers['representation']=self.representation.value
        return dict(version=2,map_path=str(self.reader.path),variable=self.variable.value,extent=list(self.extent),
                    scale=self.scale.value,palette=self.palette.value,limits=None if self.auto_limits.value else [self.low.value,self.high.value],
                    network=self.network_choice.value,network_options=self.network_options(),layers=layers)

    def save(self):
        path = save_settings(self._output('.json'), self.settings())
        self.status.object = f'**Settings saved:** `{path}`'
        return path

    def load(self, content):
        if not content:
            return
        data = load_settings(content, self.reader)
        self._applied_preset = None
        self._preset_baseline = None
        # Validate the complete display before mutating widgets/session state.
        make_layer(self.reader, data["variable"], data["scale"], data["palette"], data["limits"])
        self._updating = True
        try:
            self.variable.value, self.scale.value, self.palette.value = data["variable"], data["scale"], data["palette"]
            self.auto_limits.value = data["limits"] is None
            if data["limits"] is not None:
                self.low.value, self.high.value = data["limits"]
            self.network_choice.value = data["network"]
            options = data["network_options"]
            layers = data.get("layers", {})
            self.classification.value = options.get("classification", "fixed")
            self.area_palette.value = options.get("area_palette", "viridis")
            self.background.value = layers.get("background", "coarse")
            self.hires_source.value = layers.get("tile", self.hires_source.value)
            self.terrain_palette.value = layers.get("terrain_palette", "gray")
            self.representation.value = layers.get("representation", "grid_center")
            self.arrows.value = layers.get("arrows", False)
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
        self._reconcile_selection_source()
        self.set_extent(data["extent"])
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


def create_app(map_dir, output_dir=None):
    try:
        return Explorer(map_dir, output_dir).view
    except (ValueError, OSError) as exc:
        return pn.pane.Alert(f'Cannot open map: {escape(str(exc))}', alert_type='danger')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('map_dir', type=Path)
    parser.add_argument('--port', type=int, default=5006)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    # Explicit server resources prevent CDN access after dependencies install.
    import os
    os.environ['BOKEH_RESOURCES'] = 'server'
    print(f'Map Explorer: http://127.0.0.1:{args.port}/ (Ctrl-C to stop)', flush=True)
    pn.serve(lambda: create_app(args.map_dir), address='127.0.0.1', port=args.port,
             show=not args.no_browser, title='CaMa-Flood Map Explorer')


if __name__ == "__main__":
    main()
