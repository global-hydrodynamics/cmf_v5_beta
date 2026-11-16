"""Two-stage UI adapter; scientific raster composition remains in Scene."""

from __future__ import annotations

import panel as pn
from bokeh.models import PrintfTickFormatter

from map_reader import SCHEMA
from background_style import PALETTES, SCALES, validate_style

HIGHRES_LABELS = {
    "catchment": "Unit-Catchment (outlet uparea)",
    "elevtn": "Elevation (elevtn)",
    "flddif": "Floodplain Height (flddif)",
    "difference": "Elevation Difference (8-neighbor)",
}


class BackgroundControls:
    def __init__(self, app):
        self.app = app
        self._changing = False
        self._profiles = {}
        self._key = None
        self.raster_type = pn.widgets.RadioButtonGroup(
            name="Raster Type",
            options={"Coarse Raster": "coarse", "High-resolution Raster": "highres"},
            value="coarse",
            sizing_mode="stretch_width",
        )
        self.no_background = pn.widgets.Checkbox(name="No Background", value=False)
        self.coarse_variable = pn.widgets.Select(
            name="Coarse Raster Variable",
            options={f"{key} · {SCHEMA[key].title}": key for key in app.reader.sources},
            value=app.variable.value,
        )
        self.highres_variable = pn.widgets.Select(name="High-resolution Raster Variable", options={})
        self.notice = pn.pane.Markdown("", sizing_mode="stretch_width")
        self.color_note = pn.pane.Markdown("", sizing_mode="stretch_width")
        app.palette.name, app.scale.name = "Colormap", "Color Scale"
        app.auto_limits.name = "Automatic Color Limits"
        app.low.name, app.high.name = "Color Minimum", "Color Maximum"
        self.opacity = pn.widgets.IntSlider(
            name="Background Opacity", start=0, end=100, step=5, value=100, format=PrintfTickFormatter(format="%d%%")
        )
        self.highres_palette = pn.widgets.Select(name="Colormap", options=PALETTES, value="gallery")
        self.highres_scale = pn.widgets.Select(name="Color Scale", options=SCALES, value="gallery")
        self.highres_auto = pn.widgets.Checkbox(name="Automatic Color Limits", value=True)
        self.highres_low = pn.widgets.FloatInput(name="Color Minimum", value=0, width=140)
        self.highres_high = pn.widgets.FloatInput(name="Color Maximum", value=1, width=140)
        self.coarse_palette_min = pn.widgets.FloatSlider(name="Palette Minimum", start=0, end=1, step=0.01, value=0)
        self.coarse_palette_max = pn.widgets.FloatSlider(name="Palette Maximum", start=0, end=1, step=0.01, value=1)
        self.highres_palette_min = pn.widgets.FloatSlider(name="Palette Minimum", start=0, end=1, step=0.01, value=0)
        self.highres_palette_max = pn.widgets.FloatSlider(name="Palette Maximum", start=0, end=1, step=0.01, value=1)
        self.limits_row = pn.Row(app.low, app.high)
        self.coarse_colors = pn.Column(
            app.palette,
            app.scale,
            app.auto_limits,
            self.limits_row,
            self.coarse_palette_min,
            self.coarse_palette_max,
            sizing_mode="stretch_width",
        )
        self.highres_colors = pn.Column(
            self.highres_palette,
            self.highres_scale,
            self.highres_auto,
            pn.Row(self.highres_low, self.highres_high),
            self.highres_palette_min,
            self.highres_palette_max,
            sizing_mode="stretch_width",
        )
        self.color_settings = pn.Column(
            pn.pane.Markdown("#### Color Settings", margin=(0, 0)),
            self.coarse_colors,
            self.highres_colors,
            self.color_note,
            sizing_mode="stretch_width",
        )
        app.terrain_palette.visible = False  # Legacy configuration adapter, not a competing GUI palette.
        self.channel_note = pn.pane.Markdown("", sizing_mode="stretch_width")
        self.view = pn.Column(
            self.no_background,
            app.show_osm,
            app.osm_opacity,
            app.basemap.notice,
            pn.pane.Markdown("#### Raster Type", margin=(0, 0)),
            self.raster_type,
            self.coarse_variable,
            self.highres_variable,
            app.hires_source,
            self.notice,
            self.opacity,
            self.color_settings,
            width=330,
        )
        self.adopt_legacy()
        for widget in (self.raster_type, self.coarse_variable, self.highres_variable, self.no_background):
            widget.param.watch(lambda event: None if self._changing else app._schedule(self.apply), "value")
        for widget in (
            self.opacity,
            self.highres_palette,
            self.highres_scale,
            self.highres_auto,
            self.highres_low,
            self.highres_high,
        ):
            widget.param.watch(lambda event: app._schedule(self.render_style), "value")

        for widget in (
            self.coarse_palette_min,
            self.coarse_palette_max,
            self.highres_palette_min,
            self.highres_palette_max,
        ):
            widget.param.watch(lambda event: app._schedule(lambda: self.palette_changed(event)), "value")

    def palette_changed(self, event):
        from map_layers import validate_palette_range

        low, high = (
            (self.coarse_palette_min, self.coarse_palette_max)
            if event.obj in (self.coarse_palette_min, self.coarse_palette_max)
            else (self.highres_palette_min, self.highres_palette_max)
        )
        try:
            validate_palette_range([low.value, high.value])
        except ValueError as exc:
            updating = self.app._updating
            self.app._updating = True
            try:
                event.obj.value = event.old
            finally:
                self.app._updating = updating
            self.color_note.object = str(exc) + "; previous range retained."
            return
        self.render_style()

    def render_style(self):
        if self.app.background.value == "coarse":
            self.app.update_layer()
        else:
            self.app.render_view()
        if self.app.status.object.startswith("**Error:**"):
            self.app.status.object = "Background display updated; source values unchanged."

    def highres_options(self):
        return dict(
            palette=self.highres_palette.value,
            palette_range=[self.highres_palette_min.value, self.highres_palette_max.value],
            scale=self.highres_scale.value,
            limits=None if self.highres_auto.value else [self.highres_low.value, self.highres_high.value],
        )

    def set_highres_options(self, options):
        value = validate_style(options)
        self.highres_palette.value, self.highres_scale.value = value["palette"], value["scale"]
        self.highres_palette_min.value, self.highres_palette_max.value = value["palette_range"]
        self.highres_auto.value = value["limits"] is None
        if value["limits"] is not None:
            self.highres_low.value, self.highres_high.value = value["limits"]

    def _available(self):
        app = self.app
        tile = app.scene.tiles.get(app.hires_source.value)
        files = tile.files if tile else {}
        modes = {}
        if "catmxy" in files and "uparea" in app.reader.sources:
            modes[HIGHRES_LABELS["catchment"]] = "catchment"
        if "elevtn" in files:
            modes[HIGHRES_LABELS["elevtn"]] = "elevtn"
            if "flddif" in files:
                modes[HIGHRES_LABELS["flddif"]] = "flddif"
            modes[HIGHRES_LABELS["difference"]] = "difference"
        # Legacy JSON may inherit another coarse field. Preserve its exact
        # rendering under an explicit compatibility option, never relabel as uparea.
        current = self.highres_variable.value
        if current and current.startswith("catchment:"):
            variable = current.split(":", 1)[1]
            if "catmxy" in files and variable in app.reader.sources:
                modes[f"Unit-Catchment (legacy inherited {variable})"] = current
        return modes

    def refresh_choices(self):
        available = self._available()
        previous = self.highres_variable.value
        changing = self._changing
        self._changing = True
        try:
            self.highres_variable.options = available
            if previous not in available.values():
                self.highres_variable.value = next(iter(available.values()), None)
            self.raster_type.options = {
                "Coarse Raster": "coarse",
                **({"High-resolution Raster": "highres"} if available else {}),
            }
            if not available and self.raster_type.value == "highres":
                self.raster_type.value = "coarse"
                self.no_background.value = True
        finally:
            self._changing = changing
        return previous, self.highres_variable.value

    def profile_key(self):
        if self.raster_type.value == "coarse":
            return "coarse", self.coarse_variable.value
        return "highres", self.highres_variable.value

    def style(self):
        app = self.app
        return dict(
            scale=app.scale.value,
            palette=app.palette.value,
            auto=app.auto_limits.value,
            low=app.low.value,
            high=app.high.value,
            terrain=app.terrain_palette.value,
            palette_range=[self.coarse_palette_min.value, self.coarse_palette_max.value],
            highres=self.highres_options(),
        )

    def remember(self):
        if self._key is not None:
            self._profiles[self._key] = self.style()

    def restore(self):
        app = self.app
        state = self._profiles.get(
            self.profile_key(), dict(scale="auto", palette="viridis", auto=True, low=0, high=1, terrain="gray")
        )
        app.scale.value, app.palette.value = state["scale"], state["palette"]
        app.auto_limits.value = state["auto"]
        app.low.value, app.high.value = state["low"], state["high"]
        app.terrain_palette.value = state["terrain"]
        self.coarse_palette_min.value, self.coarse_palette_max.value = state.get("palette_range", [0, 1])
        self.set_highres_options(state.get("highres", {}))

    def apply(self):
        if self._changing:
            return
        app = self.app
        self.remember()
        app._updating = True
        try:
            self.refresh_choices()
            mode = self.highres_variable.value
            variable = self.coarse_variable.value
            if self.no_background.value:
                background = "none"
            elif self.raster_type.value == "coarse":
                background = "coarse"
            else:
                background = (mode or "none").split(":", 1)[0]
                if background == "catchment":
                    variable = mode.split(":", 1)[1] if ":" in mode else "uparea"
            app.background.value, app.variable.value = background, variable
            if self.profile_key() != self._key:
                self.restore()
            self._key = self.profile_key()
        finally:
            app._updating = False
        app.update_layer()

    def adopt_legacy(self, data=None):
        """Project existing scientific state into GUI without changing its style."""
        app = self.app
        updating = app._updating
        app._updating = True
        self._changing = True
        try:
            self.notice.object = ""
            saved = (data or {}).get("background_ui", {})
            background = app.background.value
            variable = app.variable.value
            layers = (data or {}).get("layers", {})
            if data is not None:
                self.coarse_palette_min.value, self.coarse_palette_max.value = layers.get(
                    "coarse_palette_range", [0, 1]
                )
                self.opacity.value = int(round(layers.get("background_opacity", 1.0) * 100))
            if "highres_style" in layers:
                self.set_highres_options(layers["highres_style"])
            elif background == "catchment":
                self.set_highres_options(
                    dict(
                        palette="gallery",
                        scale=(
                            "linear"
                            if app.scale.value == "linear"
                            else "gallery" if app.scale.value == "auto" else "log"
                        ),
                        limits=None if app.auto_limits.value else [app.low.value, app.high.value],
                    )
                )
            elif background in ("elevtn", "flddif", "difference"):
                self.set_highres_options({})
            self.no_background.value = background == "none"
            self.raster_type.value = "coarse" if background in ("none", "coarse") else "highres"
            if background == "coarse":
                self.coarse_variable.value = variable
            if background not in ("none", "coarse"):
                self.highres_variable.value = (
                    f"catchment:{variable}" if background == "catchment" and variable != "uparea" else background
                )
            if saved:
                self.raster_type.value = saved["raster_type"]
                self.coarse_variable.value = saved["coarse_variable"]
                self.highres_variable.value = saved["highres_variable"]
                self.no_background.value = saved["no_background"]
            requested, current = self.refresh_choices()
            if background not in ("none", "coarse") and requested != current:
                app.background.value = (current or "none").split(":", 1)[0]
                if current and current.startswith("catchment"):
                    app.variable.value = current.split(":", 1)[1] if ":" in current else "uparea"
                app.scale.value, app.palette.value, app.auto_limits.value = "auto", "viridis", True
                self.notice.object = f"Saved high-resolution variable {requested} unavailable; " + (
                    f"using {HIGHRES_LABELS.get(current,current)}." if current else "background disabled."
                )
            self._key = self.profile_key()
        finally:
            self._changing = False
            app._updating = updating
        self.remember()
        self.refresh_visibility()

    def legacy_changed(self, widget):
        if self._changing:
            return
        app = self.app
        if widget in (app.background, app.variable):
            self.remember()
            # Direct legacy/public widget use remains available for existing code.
            self.adopt_legacy()
        app.update_layer()

    def source_changed(self):
        self.remember()
        previous, current = self.refresh_choices()
        if previous != current:
            self.notice.object = f'High-resolution variable {previous or "(none)"} unavailable in selected tile; ' + (
                f"using {HIGHRES_LABELS.get(current,current)}."
                if current
                else (
                    "no valid high-resolution background; background disabled."
                    if self.no_background.value
                    else "no valid high-resolution background; coarse background unchanged."
                )
            )
        else:
            self.notice.object = ""
        self.apply()

    def refresh_visibility(self):
        app = self.app
        highres = self.raster_type.value == "highres"
        blank = self.no_background.value
        self.coarse_variable.visible = not highres and not blank
        self.highres_variable.visible = highres and not blank
        # The same source also drives independent assignment selection/overlays.
        independent = any("catmxy" in tile.files for tile in app.scene.tiles.values()) or any(
            app.overlay_controls[key].value for key in ("headwater", "catchment_boundaries", "channel_pixels")
        )
        app.hires_source.visible = bool(app.scene.tiles) and (highres or independent or not self._available())
        self.opacity.visible = not blank
        self.color_settings.visible = not blank
        self.coarse_colors.visible = not highres
        self.highres_colors.visible = highres
        app.terrain_palette.visible = False
        categorical = app.background.value == "catchment" and SCHEMA[app.variable.value].categorical
        self.highres_palette.disabled = self.highres_scale.disabled = self.highres_auto.disabled = categorical
        self.highres_low.disabled = self.highres_high.disabled = categorical or self.highres_auto.value
        if highres and app.frame is not None and app.frame.layer is not None and self.highres_auto.value:
            updating = app._updating
            app._updating = True
            try:
                self.highres_low.value, self.highres_high.value = app.frame.layer.low, app.frame.layer.high
            finally:
                app._updating = updating
        channels = app.overlay_controls["channel_pixels"]
        tile = app.scene.tiles.get(app.hires_source.value)
        # Always discoverable in Overlays; moving the control does not change
        # the high-resolution-only scientific rendering contract.
        channels.visible = True
        channels.disabled = not highres or blank or tile is None or "visual" not in tile.files
        self.channel_note.visible = channels.disabled
        self.channel_note.object = (
            "Channel Pixels requires a visible high-resolution background."
            if not highres or blank
            else "Channel Pixels unavailable: selected tile has no visual product." if channels.disabled else ""
        )
        self.coarse_palette_min.disabled = self.coarse_palette_max.disabled = SCHEMA[app.variable.value].categorical
        self.highres_palette_min.disabled = self.highres_palette_max.disabled = categorical
        if highres and categorical:
            self.color_note.object = "Legacy inherited categories retain discrete colors; continuous scales/limits and palette cropping do not apply."
        elif highres:
            log = (
                self.highres_scale.value == "log"
                or self.highres_scale.value == "gallery"
                and app.background.value == "catchment"
                and SCHEMA[app.variable.value].logarithmic
            )
            self.color_note.object = (
                "Assigned coarse-cell attribute [km² for uparea], not a native high-resolution upstream-area field. "
                if app.background.value == "catchment"
                else "Native terrain / 8-neighbor elevation difference [m], not slope. "
            )
            self.color_note.object += (
                "Log clips values below its positive minimum (automatic: 0.01); native values remain unchanged. "
                if log
                else ""
            )
            self.color_note.object += (
                "Gallery Default preserves log-uparea / full-tile assigned-pixel P2/P98 and terrain stretch. "
                if self.highres_scale.value == "gallery"
                else "Custom " + self.highres_scale.value + " normalization. "
            )
            self.color_note.object += (
                "Automatic limits use the full reference, not the viewport; manual limits must be strictly increasing."
            )
        elif SCHEMA[app.variable.value].categorical:
            self.color_note.object = "Stored categories use discrete colors; continuous normalization, limits and palette cropping are disabled."
        else:
            self.color_note.object = "Display transforms only; source values stay unchanged."
        if not self._available() and not self.notice.object:
            self.notice.object = "No supported high-resolution variables in selected tile. Unit-Catchment needs catmxy + coarse uparea; terrain needs native elevtn (and flddif for floodplain height)."
        self._key = self.profile_key()
        self.remember()

    def configuration(self):
        return dict(
            raster_type=self.raster_type.value,
            coarse_variable=self.coarse_variable.value,
            highres_variable=self.highres_variable.value,
            no_background=self.no_background.value,
        )

    def config_for(self, background, variable):
        state = self.configuration()
        state["no_background"] = background == "none"
        if background == "coarse":
            state.update(raster_type="coarse", coarse_variable=variable)
        elif background != "none":
            state.update(
                raster_type="highres",
                highres_variable=(
                    f"catchment:{variable}" if background == "catchment" and variable != "uparea" else background
                ),
            )
        return state
