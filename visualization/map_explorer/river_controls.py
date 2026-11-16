"""Conditional main-network controls; display limits never redefine topology."""

import panel as pn

from map_products import AREA_PALETTES

RIVER_PALETTES = {
    "Shades_rainbow": "shade_rainbow",
    "Turbo": "turbo",
    "Blues": "Blues",
    "YlGnBu": "YlGnBu",
    "plasma": "plasma",
    "Blue → Navy": "blue_navy",
    "Gray → Black": "gray_black",
    "Gray → White": "gray_white",
}

MAPPINGS = {
    "Continuous (log scale)": "continuous",
    "Quantiles (4 groups)": "quartiles",
    "Logarithmic (6 classes)": "six_log",
    "Fixed log range (legacy)": "fixed",
}


class PaletteSelect(pn.widgets.Select):
    # Panel otherwise coerces an out-of-menu legacy value to the first option.
    # Keep no active choice until the user explicitly replaces the loaded palette.
    _allows_none = True


class RiverControls:
    def __init__(self, app):
        self.app = app
        self.color_style = "palette"
        app.network_choice.name = "Network source"
        app.representation.name = "Representation"
        app.representation.options = {
            label: value
            for label, value in [("Grid Center", "grid_center"), ("Outlet Vector", "outlet_vector"), ("Off", "off")]
            if value in app.representation.options
        }
        app.color_mode.name = "Color Mode"
        app.color_mode.options = {
            "Uniform": "uniform",
            "Connection Type": "connection_type",
            "Upstream Area": "upstream_area",
        }
        app.width_mode.name = "Width Mode"
        app.width_mode.options = {"Uniform": "uniform", "Upstream Area": "upstream_area"}
        app.classification.name = "Upstream Area Mapping"
        app.classification.options = MAPPINGS
        app.area_palette.name = "Colormap"
        app.area_palette.options = list(AREA_PALETTES)
        self.palette = PaletteSelect(name="Colormap", options=RIVER_PALETTES)
        self.legacy_palette = pn.pane.Markdown("", sizing_mode="stretch_width")
        self.palette.param.watch(lambda event: app._schedule(self.palette_changed), "value")
        app.width.name = "Base Line Width [px]"
        app.flex_color.name = "Flexible Links Color"
        self.auto = pn.widgets.Checkbox(name="Automatic Area Limits", value=True)
        self.low = pn.widgets.FloatInput(name="Area Minimum [km²]", value=1, width=145)
        self.high = pn.widgets.FloatInput(name="Area Maximum [km²]", value=1e6, width=145)
        self.area_colors = pn.Column(self.palette, self.legacy_palette, self.auto, pn.Row(self.low, self.high))
        self.note = pn.pane.Markdown("", sizing_mode="stretch_width")
        self.view = pn.Column(
            app.network_choice,
            app.representation,
            pn.pane.Markdown("#### COLOR", margin=(0, 0)),
            app.color_mode,
            app.color,
            app.flex_color,
            self.area_colors,
            pn.pane.Markdown("#### WIDTH", margin=(0, 0)),
            app.width_mode,
            app.width,
            app.classification,
            self.note,
            pn.pane.Markdown("#### DIRECTION", margin=(0, 0)),
            app.arrow_size,
            pn.pane.Markdown("0 = Off. Main-network direction follows stored downstream connectivity.", margin=(0, 0)),
            width=330,
        )
        for widget in (self.auto, self.low, self.high):
            widget.param.watch(lambda event: app._schedule(self.render), "value")
        for widget in (app.area_palette, app.classification):
            widget.param.watch(lambda event: app._schedule(self.custom_mapping), "value")
        app.arrow_size.param.watch(lambda event: app._schedule(self.arrow_changed), "value")

    def palette_changed(self):
        if self.palette.value is None:
            return
        self.app._updating = True
        try:
            self.app.area_palette.value = self.palette.value
        finally:
            self.app._updating = False
        self.custom_mapping()

    def render(self):
        self.app.render_view()
        if self.app.status.object.startswith("**Error:**"):
            self.app.status.object = "River display updated; source values unchanged."

    def custom_mapping(self):
        self.color_style = "palette"
        self.render()

    def arrow_changed(self):
        app = self.app
        app._updating = True
        try:
            app.arrows.value = app.arrow_size.value > 0
        finally:
            app._updating = False
        self.render()

    def legacy_arrows(self):
        self.app.arrow_size.value = 7 if self.app.arrows.value else 0

    def refresh(self):
        app = self.app
        updating = app._updating
        app._updating = True
        try:
            current = app.area_palette.value
            self.palette.value = current if current in RIVER_PALETTES.values() else None
            self.legacy_palette.object = (
                "Loaded palette **"
                + current
                + "** is preserved for compatibility (Gallery colors may override it). Choose one of the eight palettes to replace it."
                if current not in RIVER_PALETTES.values()
                else ""
            )
            self.legacy_palette.visible = bool(self.legacy_palette.object)
        finally:
            app._updating = updating
        area = app.color_mode.value == "upstream_area"
        typed = app.color_mode.value == "connection_type"
        app.color.name = "Local Links Color" if typed else "All Links Color"
        app.color.visible = not area
        app.flex_color.visible = typed
        self.area_colors.visible = area
        uses_area = area or app.width_mode.value == "upstream_area"
        app.classification.visible = self.note.visible = uses_area
        editable = app.classification.value in ("continuous", "six_log")
        self.auto.disabled = not editable
        self.low.disabled = self.high.disabled = not editable or self.auto.value
        if self.auto.value and app.network is not None and hasattr(app.network, "_area_summary"):
            _, lo, hi, _ = app.network._area_summary
            app._updating = True
            try:
                self.low.value, self.high.value = 10**lo, 10**hi
            finally:
                app._updating = False
        details = {
            "continuous": "Continuous log-area mapping; color limits clip colors only. Width uses the full reference.",
            "quartiles": "Four groups containing approximately equal numbers of river links, ordered by upstream drainage area. Full-reference quantiles; manual limits do not apply.",
            "six_log": "Six equal log-area intervals (not quantiles). Color intervals may use manual limits; width retains full-reference intervals.",
            "fixed": "Legacy fixed area reference 1–10⁶ km²; manual limits do not apply.",
        }
        self.note.object = details[app.classification.value] + " Contributing drainage area, not discharge."
        if self.color_style != "palette" and area:
            self.note.object += (
                " Gallery historical colors retained; changing Colormap or Mapping selects custom palette colors."
            )
