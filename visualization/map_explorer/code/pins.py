"""Session Pins: immutable scientific snapshots, separate from visualization JSON.

Snapshots come from Explorer.inspect / CellInspector.update structured values, never
HTML. Inclusion and renaming only rebuild small tables, not scenes or graph indexes.
"""

from __future__ import annotations

from copy import deepcopy
import csv
from dataclasses import dataclass, replace
from html import escape
import io
from pathlib import Path

import numpy as np
import panel as pn
from bokeh.models import ColumnDataSource, LabelSet

# label, stable CSV name, shared Inspector key, conversion to physical display unit
FIELDS = [
    ("Outlet longitude [°]", "outlet_lon", "source outlet longitude", 1),
    ("Outlet latitude [°]", "outlet_lat", "source outlet latitude", 1),
    ("Upstream area [km²]", "uparea_km2", "uparea [m2]", 1e-6),
    ("Unit-catchment area [km²]", "ctmare_km2", "ctmare [m2]", 1e-6),
    ("Elevation [m]", "elevtn_m", "elevtn [m]", 1),
    ("River width [m]", "rivwth_m", "rivwth [m]", 1),
    ("River depth [m]", "rivhgt_m", "rivhgt [m]", 1),
    ("River length [km]", "rivlen_km", "rivlen [m]", 0.001),
    ("Downstream distance [km]", "nxtdst_km", "nxtdst [m]", 0.001),
    ("Manning roughness (source units unspecified)", "rivman", "rivman []", 1),
    ("Basin ID", "basin_id", "basin [1]", 1),
    ("Subbasin ID (true product)", "subbasin_id", "subbsn [1]", 1),
    ("Downstream ix (stored)", "downstream_ix", "downstream ix (1-based)", 1),
    ("Downstream iy (stored)", "downstream_iy", "downstream iy (1-based)", 1),
    ("Direct upstream count", "direct_upstream_count", "direct upstream Unit Catchments", 1),
    ("Total distinct upstream count", "total_upstream_count", "total upstream Unit Catchments", 1),
] + [
    (
        f"{direction} {kind} bifurcations",
        f"{kind.lower()}_{direction.lower()}_count",
        f"{direction.lower()} {kind.lower()} bifurcations",
        1,
    )
    for kind in ("Channel", "Overland")
    for direction in ("Incoming", "Outgoing")
]
NATIVE = [
    ("High-res ix (1-based)", "native hires ix (1-based)"),
    ("High-res iy (1-based)", "native hires iy (1-based)"),
    ("High-res catmx (stored)", "assigned coarse ix (1-based)"),
    ("High-res catmy (stored)", "assigned coarse iy (1-based)"),
    ("High-res elevtn [m]", "native hires elevtn [m]"),
    ("High-res catmz100 (signed code)", "native hires catmz100 [stored code]"),
    ("High-res rivwth [m]", "native hires rivwth [m]"),
    ("High-res uparea [km²] (native product only)", "native hires uparea [km²]"),
    ("Assigned Unit Catchment uparea [km²]", "clicked assigned catchment uparea [km²]"),
]


def scalar(value, factor=1):
    if value is None or np.ma.is_masked(value):
        return None
    if isinstance(value, (int, float, np.number)):
        return float(value) * factor if np.isfinite(value) else None
    return value


def letter(number):
    result = ""
    while number:
        number, digit = divmod(number - 1, 26)
        result = chr(65 + digit) + result
    return result


def fingerprint(app, tile_key):
    """Paths and size/mtime identity; no content rescans of large scientific files."""
    paths = {app.reader.path / "params.txt"}
    for source in list(app.reader.sources.values()) + list(app.reader.network_sources.values()):
        paths.add(source.path)
    tile = app.scene.tiles.get(tile_key)
    if tile is not None:
        paths.update(tile.files.values())
    # Also cover optional Inspector/outlet/bifurcation products in the map root.
    paths.update(p for p in app.reader.path.iterdir() if p.is_file())
    netcdf = app.reader.path / "netcdf"
    if netcdf.is_dir():
        paths.update(p for p in netcdf.iterdir() if p.is_file())
    return tuple(
        (str(Path(p).resolve()), Path(p).stat().st_size, Path(p).stat().st_mtime_ns) for p in sorted(paths, key=str)
    )


@dataclass(frozen=True)
class Pin:
    id: str
    label: str
    name: str
    mode: str
    clicked: tuple
    river_ix: int  # Persisted Pin identity is explicitly one-based Fortran.
    river_iy: int
    map_path: str
    tile: str
    identity: tuple
    values: dict
    included: bool = True

    @property
    def cell(self):
        return self.river_iy - 1, self.river_ix - 1

    @property
    def key(self):
        return self.mode, self.cell, self.tile, self.identity

    def record(self):
        row, col = self.cell
        result = dict(
            pin_id=self.id,
            pin_name=self.name,
            selection_mode=self.mode,
            clicked_lon=self.clicked[0],
            clicked_lat=self.clicked[1],
            river_ix=col + 1,
            river_iy=row + 1,
            map_source=self.map_path,
            highres_source=self.tile,
            network_source=self.values.get("network product"),
            assigned_pixel_count=self.values.get("unit catchment assigned pixel count"),
            assigned_pixel_scope=self.values.get("unit catchment pixel count scope"),
        )
        result.update({column: scalar(self.values.get(key), factor) for _, column, key, factor in FIELDS})
        if result["subbasin_id"] is not None and result["subbasin_id"] <= 0:
            result["subbasin_id"] = None
        return result


def csv_bytes(rows):
    out = io.StringIO(newline="")
    csv.writer(out).writerows(rows)
    return out.getvalue().encode("utf-8-sig")


class PinControls:
    def __init__(self, app):
        self.app = app
        self.pins = []
        self.serial = 0
        self.active = None
        self._syncing = False
        self.name = pn.widgets.TextInput(name="Pin name", placeholder="Optional; defaults to Pin 1")
        self.add_button = pn.widgets.Button(name="Add Pin", button_type="primary")
        self.list = pn.widgets.Select(name="Pinned locations", options={})
        self.rename_button = pn.widgets.Button(name="Rename Pin")
        self.delete_button = pn.widgets.Button(name="Delete Pin", button_type="danger")
        self.include = pn.widgets.CheckBoxGroup(name="Include in comparison", options={})
        self.message = pn.pane.Markdown("Pins last for this browser session. Markers show original clicked locations.")
        self.core = pn.pane.HTML(sizing_mode="stretch_width")
        self.profiles = pn.pane.HTML(sizing_mode="stretch_width")
        self.native = pn.pane.HTML(sizing_mode="stretch_width")
        self.profile_group = pn.Accordion(("Floodplain elevation profiles [m]", self.profiles), active=[])
        self.native_group = pn.Accordion(("High-resolution pixel values", self.native), active=[])
        self.comparison = pn.Accordion(
            (
                "Pinned Locations Comparison",
                pn.Column(self.include, self.core, self.profile_group, self.native_group, sizing_mode="stretch_width"),
            ),
            active=[],
            sizing_mode="stretch_width",
        )
        self.download_pins = pn.widgets.FileDownload(
            label="Export Pins CSV", filename="pins.csv", callback=lambda: self.download(False)
        )
        self.download_comparison = pn.widgets.FileDownload(
            label="Export Comparison CSV", filename="comparison.csv", callback=lambda: self.download(True)
        )
        self.view = pn.Column(
            "### Pins",
            self.name,
            self.add_button,
            self.list,
            pn.Row(self.rename_button, self.delete_button),
            self.download_pins,
            self.download_comparison,
            self.message,
            sizing_mode="stretch_width",
            styles={"flex-shrink": "0", "max-height": "none"},
        )
        self.source = ColumnDataSource(dict(x=[], y=[], label=[], name=[], color=[], size=[]))
        self.renderer = app.plot.scatter(
            "x", "y", source=self.source, size="size", fill_color="color", line_color="white", line_width=2
        )
        self.renderer.nonselection_glyph = self.renderer.glyph.clone()
        app.plot.add_layout(
            LabelSet(
                x="x",
                y="y",
                text="label",
                source=self.source,
                x_offset=9,
                y_offset=6,
                text_color="#3B1464",
                text_font_style="bold",
                background_fill_color="white",
                background_fill_alpha=0.85,
            )
        )
        self.add_button.on_click(lambda e: self._action(self.add))
        self.rename_button.on_click(lambda e: self._action(self.rename))
        self.delete_button.on_click(lambda e: self._action(self.delete))
        self.list.param.watch(self._list_changed, "value")
        self.include.param.watch(self._include_changed, "value")
        self.refresh()

    def _action(self, function):
        # Panel widget watchers may run outside the Bokeh document lock.
        # Queue every direct source/range mutation on the same locked tick as
        # Explorer controls. Report errors beside Pins even in Inspector mode.
        def run():
            try:
                function()
            except (ValueError, OSError, KeyError, TypeError) as exc:
                self.message.object = f"**Pin error:** {escape(str(exc))}"

        self.app._schedule(run)

    def current(self):
        return next((p for p in self.pins if p.id == self.active), None)

    def add(self):
        state = self.app.selection
        if state.river_cell is None or state.clicked is None:
            raise ValueError("Select a valid Grid or assigned Unit Catchment before adding a Pin.")
        mode = self.app.point_select.value
        identity = fingerprint(self.app, state.tile_key)
        key = mode, state.river_cell, state.tile_key, identity
        duplicate = next((p for p in self.pins if p.key == key), None)
        if duplicate is not None:
            self.active = duplicate.id
            self.refresh()
            self.message.object = f"Already pinned as {duplicate.label}. Selected the existing Pin; no duplicate added."
            return duplicate
        self.serial += 1
        pin = Pin(
            f"pin-{self.serial:04d}",
            letter(self.serial),
            (self.name.value_input or self.name.value).strip() or f"Pin {self.serial}",
            mode,
            state.clicked,
            state.river_cell[1] + 1,
            state.river_cell[0] + 1,
            str(self.app.reader.path.resolve()),
            state.tile_key,
            identity,
            deepcopy(self.app._selection_values),
        )
        self.pins.append(pin)
        self.active = pin.id
        self.name.value = ""
        self.refresh()
        self.message.object = f"Added Pin {pin.label}."
        return pin

    def select(self, identifier):
        pin = next((p for p in self.pins if p.id == identifier), None)
        if pin is None:
            raise ValueError("Pin no longer exists.")
        app = self.app
        try:
            if fingerprint(app, pin.tile) != pin.identity:
                raise ValueError("Pin source changed; its saved scientific selection cannot be restored.")
        except OSError as exc:
            raise ValueError(f"Pin source unavailable: {exc}") from exc
        if pin.tile not in app.scene.tiles and pin.mode == "catchment":
            raise ValueError("Saved high-resolution source is unavailable.")
        if pin.mode != app.point_select.value:
            self.message.object = "This Pin uses " + pin.mode + " selection; adjust zoom/background until that automatic mode is available. Stored values are retained."
            return
        if pin.mode == "catchment":
            _, assigned = app.scene.inspect(*pin.clicked, pin.tile, cog_only=True)
        else:
            assigned = app.reader.geometry.cell(*pin.clicked)
        if assigned != pin.cell:
            raise ValueError("Saved assignment no longer matches. No geographic fallback was used.")
        previous_tile = app.hires_source.value
        app._updating = True
        try:
            app.point_select.value = pin.mode
            if pin.tile is not None:
                app.hires_source.value = pin.tile
        finally:
            app._updating = False
        app._update_assignment_controls()
        if previous_tile != pin.tile:
            app.render_view()
        # Inspector connectivity uses the saved network product, independently of
        # current River visibility/style; markers and other visualization controls persist.
        app.inspect(*pin.clicked, network_product=pin.values.get("network product"))
        w, e, s, n = app.extent
        x, y = pin.clicked
        if not (w <= x <= e and s <= y <= n):
            from view_controls import translated_extent

            app.set_extent(translated_extent(app.extent, app.reader.geometry, x, y), preserve_aspect=True)
        self.active = pin.id
        self.refresh()
        self.message.object = f"Selected Pin {pin.label}; saved {pin.mode} and source restored."

    def _list_changed(self, event):
        if not self._syncing and event.new:
            self._action(lambda: self.select(event.new))

    def rename(self):
        pin = self.current()
        name = (self.name.value_input or self.name.value).strip()
        if pin is None or not name:
            raise ValueError("Select a Pin and enter a nonempty new name.")
        self.pins = [replace(p, name=name) if p.id == pin.id else p for p in self.pins]
        self.name.value = ""
        self.refresh()

    def delete(self):
        if self.active is None:
            return
        self.pins = [p for p in self.pins if p.id != self.active]
        self.active = None
        self.refresh()
        self.message.object = "Pin deleted. Current ordinary map selection retained."

    def _include_changed(self, event):
        if not self._syncing:
            selected = list(event.new)

            def update():
                self.pins = [replace(p, included=p.id in selected) for p in self.pins]
                self.refresh()

            self._action(update)

    def marker_data(self):
        return dict(
            x=[p.clicked[0] for p in self.pins],
            y=[p.clicked[1] for p in self.pins],
            label=[f"{p.label} · {p.name[:28]}" for p in self.pins],
            name=[p.name for p in self.pins],
            color=["#8E24AA" if p.id == self.active else "#0097A7" for p in self.pins],
            size=[18 if p.id == self.active else 14 for p in self.pins],
        )

    def hit(self, x, y):
        w, e, s, n = self.app.extent
        width = self.app.plot.frame_width or 800
        height = self.app.plot.frame_height or 650
        candidates = [
            (((p.clicked[0] - x) * width / (e - w)) ** 2 + ((p.clicked[1] - y) * height / (n - s)) ** 2, p)
            for p in self.pins
        ]
        if candidates:
            distance, pin = min(candidates, key=lambda item: item[0])
            if distance <= 11**2:
                self.select(pin.id)
                return True
        return False

    def matrix(self, group="core"):
        pins = [p for p in self.pins if p.included]
        records = [p.record() for p in pins]
        if group == "core":
            fields = [
                ("Pin ID", "pin_id"),
                ("Name", "pin_name"),
                ("Selection mode", "selection_mode"),
                ("Clicked longitude [°]", "clicked_lon"),
                ("Clicked latitude [°]", "clicked_lat"),
                ("Selected ix (1-based)", "river_ix"),
                ("Selected iy (1-based)", "river_iy"),
                ("Map source", "map_source"),
                ("High-resolution source", "highres_source"),
                ("Network source", "network_source"),
                ("Assigned pixel count (visible window, not area)", "assigned_pixel_count"),
            ]
            fields += [(label, column) for label, column, _, _ in FIELDS]
            rows = [[label] + [r.get(column) for r in records] for label, column in fields]
        elif group == "profiles":
            count = max((len(p.values.get("fldhgt [m]") or []) for p in pins), default=0)
            rows = [
                [f"fldhgt Layer {i+1} [m]"]
                + [
                    scalar((p.values.get("fldhgt [m]") or [])[i]) if i < len(p.values.get("fldhgt [m]") or []) else None
                    for p in pins
                ]
                for i in range(count)
            ]
        else:
            rows = [[label] + [scalar(p.values.get(key)) for p in pins] for label, key in NATIVE]
        return [["Parameter"] + [f"{p.id} · {p.label} · {p.name}" for p in pins]] + rows

    def html(self, group):
        rows = self.matrix(group)

        def value(v):
            return "Unavailable" if v is None else f"{v:,.9g}" if isinstance(v, float) else str(v)

        return (
            '<div style="overflow-x:auto;max-width:100%"><table style="border-collapse:collapse;white-space:nowrap">'
            + "".join(
                "<tr>"
                + "".join(
                    f'<{"th" if i==0 or j==0 else "td"} style="padding:5px;border:1px solid #ddd;'
                    + ("position:sticky;left:0;background:#f2f4f8;" if j == 0 else "")
                    + '">'
                    + escape(value(v))
                    + f'</{"th" if i==0 or j==0 else "td"}>'
                    for j, v in enumerate(row)
                )
                + "</tr>"
                for i, row in enumerate(rows)
            )
            + "</table></div>"
        )

    def refresh(self):
        self._syncing = True
        try:
            options = {f"{p.label} · {p.name} · {p.mode} ({p.cell[1]+1}, {p.cell[0]+1})": p.id for p in self.pins}
            self.list.options = options
            self.list.value = self.active
            self.include.options = {f"{p.label} · {p.name}": p.id for p in self.pins}
            self.include.value = [p.id for p in self.pins if p.included]
            self.source.data = self.marker_data()
            self.core.object = (
                self.html("core") if self.pins else "<p>No Pins yet. Add a valid selection in Inspector.</p>"
            )
            self.profiles.object = self.html("profiles")
            self.native.object = self.html("native")
            self.download_pins.disabled = not self.pins
            self.download_comparison.disabled = not any(p.included for p in self.pins)
        finally:
            self._syncing = False

    def export(self, comparison=False):
        if comparison:
            rows = self.matrix() + self.matrix("profiles")[1:] + self.matrix("native")[1:]
        else:
            records = [p.record() for p in self.pins]
            # Header is stable even for an empty programmatic export.
            columns = list(records[0]) if records else ["pin_id", "pin_name", "selection_mode"]
            rows = [columns] + [[r.get(k) for k in columns] for r in records]
        path = self.app._output("-comparison.csv" if comparison else "-pins.csv")
        path.write_bytes(csv_bytes(rows))
        self.message.object = f"**CSV saved:** `{path}`"
        return path

    def download(self, comparison):
        path = self.export(comparison)
        widget = self.download_comparison if comparison else self.download_pins
        widget.filename = path.name
        return io.BytesIO(path.read_bytes())
