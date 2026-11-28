"""One active Explorer per browser session; replace only a fully prepared map."""

from html import escape
from pathlib import Path

import panel as pn

from map_datasets import REPOSITORY, discover_maps, resolve_map
from map_reader import Geometry


class ExplorerSession:
    def __init__(self, map_dir=None, output_dir=None, repository=REPOSITORY, factory=None):
        if factory is None:
            from app import Explorer
            factory = Explorer
        self.repository = Path(repository).resolve()
        self.factory = factory
        self.output_dir = output_dir
        self.active = None
        self._loading = False
        self._closed = False
        self._syncing = False
        self._pending_path = None
        self._load_callback = None
        maps = discover_maps(self.repository)
        self.available = pn.widgets.Select(
            name="Available Maps", options={"Custom directory": None, **{m.label: str(m.path) for m in maps}},
            sizing_mode="stretch_width",
        )
        self.directory = pn.widgets.TextInput(name="Map Directory", sizing_mode="stretch_width")
        self.current = pn.pane.HTML(sizing_mode="stretch_width", margin=(0, 0))
        self.load_button = pn.widgets.Button(name="Load Map", button_type="primary")
        self.status = pn.pane.Markdown("", sizing_mode="stretch_width")
        self.confirm_button = pn.widgets.Button(name="Switch Map and Clear Pins", button_type="warning")
        self.cancel_button = pn.widgets.Button(name="Cancel map switch")
        self.confirmation = pn.Column(
            pn.pane.Markdown("**Switching maps will clear the current Pins. Export them to CSV first if needed.**"),
            self.confirm_button, self.cancel_button, visible=False, sizing_mode="stretch_width",
        )
        self.controls = pn.Column(
            pn.pane.Markdown("### Map Dataset", margin=(0, 0)), self.current, self.available, self.directory,
            self.load_button, self.status, self.confirmation, sizing_mode="stretch_width",
            visible=False, max_width=900,
        )
        self.dataset_toggle = pn.widgets.Toggle(name="Map dataset", value=False, width=135)
        self.dataset_toggle.param.watch(
            self._toggle_dataset, "value"
        )
        self.host = pn.Column(sizing_mode="stretch_width")
        self.view = self.host
        self.available.param.watch(self._choose, "value")
        self.directory.param.watch(self._edit_path, "value")
        self.load_button.on_click(lambda event: self.load_map(defer=True))
        self.confirm_button.on_click(lambda event: self._confirm_switch())
        self.cancel_button.on_click(lambda event: self.cancel_switch())
        initial = self._prepare(resolve_map(map_dir, self.repository))
        self._adopt(initial)

    def _toggle_dataset(self, event):
        self.controls.visible = event.new
        if self.active is not None:
            # Closing the drawer moves the map without resizing its own DOM box.
            self.active.map_viewport.layout_revision += 1

    def _choose(self, event):
        if not self._syncing and event.new:
            self.directory.value = event.new

    def _edit_path(self, event):
        if self._syncing:
            return
        self.cancel_switch(message=False)
        self._syncing = True
        try:
            path = str(resolve_map(event.new, self.repository)) if event.new.strip() else None
            self.available.value = path if path in self.available.options.values() else None
        finally:
            self._syncing = False

    def _confirm_switch(self):
        if self._pending_path is not None:
            self.load_map(self._pending_path, confirm_pins=True, defer=True)

    def cancel_switch(self, message=True):
        self._pending_path = None
        self.confirmation.visible = False
        if message:
            self.status.object = "Map switch cancelled; current map and Pins retained."

    def _prepare(self, path):
        if not path.is_dir():
            raise ValueError(f"Map directory not found: {path}. Enter a server-side map directory.")
        try:
            Geometry.read(path)
        except (OSError, ValueError) as exc:
            raise ValueError(f"Map geometry metadata is missing or invalid: {path}: {exc}") from exc
        explorer = self.factory(path, self.output_dir)
        try:
            if explorer.frame is None or explorer.layer is None or explorer._background_error:
                raise ValueError(f"Cannot render a supported core raster: {explorer.status.object}")
            # Apply the same method to every map; only bundled Mekong uses
            # the Gallery's geographic extent. Other datasets retain their domain.
            if path == resolve_map(None, self.repository):
                explorer.apply_startup_defaults()
            else:
                explorer.set_extent(explorer.reader.geometry.extent)
                explorer.apply_startup_defaults(use_gallery_extent=False)
            return explorer
        except Exception:
            explorer.close()
            raise

    def _adopt(self, explorer):
        previous = self.active
        mode = previous.panel_mode.value if previous else "Visualization"
        visible = previous.settings_toggle.value if previous else True
        try:
            if previous is not None:
                previous.view.remove(self.controls)
                previous.header_bar.remove(self.dataset_toggle)
            explorer.view.insert(1, self.controls)
            explorer.header_bar.insert(len(explorer.header_bar.objects) - 1, self.dataset_toggle)
            explorer.panel_mode.value = mode
            explorer.settings_toggle.value = visible
            self.active = explorer
            self.host.objects = [explorer.view]
            self._syncing = True
            try:
                path = str(explorer.reader.path)
                self.directory.value = path
                self.available.value = path if path in self.available.options.values() else None
            finally:
                self._syncing = False
            g = explorer.reader.geometry
            self.current.object = f"<small><b>Current:</b> {escape(explorer.reader.path.name)} · {g.nx} × {g.ny}</small>"
            self.status.object = f"**{escape(explorer.reader.path.name)} loaded.**"
            if explorer.scene.tiles:
                self.status.object += " High-resolution: " + ", ".join(sorted({t.storage for t in explorer.scene.tiles.values()})) + "."
            else:
                self.status.object += " High-resolution products unavailable; optional high-res/Catchment features are disabled."
        except Exception:
            # Roll back a view/model mount failure as well as a preparation failure.
            self.active = previous
            if self.controls in explorer.view.objects:
                explorer.view.remove(self.controls)
            if self.dataset_toggle in explorer.header_bar.objects:
                explorer.header_bar.remove(self.dataset_toggle)
            if previous is not None:
                if self.controls not in previous.view.objects:
                    previous.view.insert(1, self.controls)
                if self.dataset_toggle not in previous.header_bar.objects:
                    previous.header_bar.insert(len(previous.header_bar.objects) - 1, self.dataset_toggle)
            self.host.objects = [previous.view] if previous is not None else []
            explorer.close()
            raise
        if previous is not None:
            previous.close()

    def load_map(self, value=None, confirm_pins=False, defer=False):
        """Button requests defer Bokeh changes to its document lock; tests can run directly."""
        if self._loading or self._closed:
            return False
        try:
            text = value if value is not None else self.directory.value.strip()
            if not text:
                raise ValueError("Enter a Map Directory or choose an Available Map.")
            path = resolve_map(text, self.repository)
            if path == self.active.reader.path:
                self.status.object = "This map is already loaded; current selection and Pins retained."
                return False
            if self.active.pins.pins and not confirm_pins:
                self._pending_path = path
                self.confirmation.visible = True
                self.status.object = "Confirm the map switch below, or export Pins CSV in Inspector first."
                return False
            self.cancel_switch(message=False)
            self._loading = True
            self.load_button.loading = True
            for widget in (self.load_button, self.available, self.directory):
                widget.disabled = True
            self.status.object = f"Loading **{escape(path.name)}**… Current map remains active until validation succeeds."
            document = self.active.plot.document
            if defer and document is not None and document.session_context is not None:
                def execute():
                    self._load_callback = None
                    self._replace(path)
                self._load_callback = (document, document.add_next_tick_callback(execute))
                return True
            return self._replace(path)
        except (ValueError, OSError) as error:
            self.status.object = f"**Cannot load map:** {escape(str(error).rstrip('.'))}. Current map and Pins retained."
            return False

    def _replace(self, path):
        candidate = None
        try:
            if self._closed:
                return False
            candidate = self._prepare(path)
            self._adopt(candidate)
            return True
        except Exception as error:
            if candidate is not None and candidate is not self.active:
                candidate.close()
            self.status.object = f"**Cannot load map:** {escape(str(error).rstrip('.'))}. Current map and Pins retained."
            return False
        finally:
            self._loading = False
            self.load_button.loading = False
            for widget in (self.load_button, self.available, self.directory):
                widget.disabled = False

    def close(self, context=None):
        self._closed = True
        if self._load_callback is not None:
            document, handle = self._load_callback
            try:
                document.remove_next_tick_callback(handle)
            except ValueError:
                pass
            self._load_callback = None
        if self.active is not None:
            self.active.close()
