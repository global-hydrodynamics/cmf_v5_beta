"""Local Panel/Bokeh map explorer; every browser session owns its state."""
from __future__ import annotations

import argparse
from datetime import datetime
from html import escape
from pathlib import Path
import sys

import numpy as np
import panel as pn
from bokeh.events import RangesUpdate, Tap
from bokeh.models import (ColorBar, ColumnDataSource, CustomJS, Div, FixedTicker,
                          HoverTool, LinearColorMapper, LogColorMapper, Range1d)
from bokeh.plotting import figure

from config import load_settings, save_settings
from map_layers import colorize, export_png, make_layer, network_style, raster_subset
from map_reader import MapReader, SCHEMA
from river_network import RiverNetwork

pn.extension()


class Explorer:
    def __init__(self, map_dir, output_dir=None):
        self.reader = MapReader(map_dir)
        if not self.reader.sources:
            raise ValueError('No supported readable rasters. ' + '; '.join(self.reader.messages))
        self.output_dir = Path(output_dir or Path(__file__).parent/'output').resolve()
        # Even an explicitly supplied export directory must not be inside input.
        if self.output_dir == self.reader.path or self.reader.path in self.output_dir.parents:
            raise ValueError('Output directory must be outside MAP_DIR')
        self.network = None
        self.selected = None
        self.layer = None
        self._updating = False
        self._network_cache = None
        self.status = pn.pane.Markdown('', width=295)
        self.network_summary = pn.pane.Markdown('')
        self.inspection = pn.pane.HTML('<p>Click a cell to inspect native values and stored downstream indices.</p>', width=320)
        self.variable = pn.widgets.Select(name='Raster variable', options={f'{k} · {SCHEMA[k].title}': k for k in self.reader.sources})
        self.scale = pn.widgets.Select(name='Color scale (continuous only)', options=['auto', 'linear', 'log'])
        self.palette = pn.widgets.Select(name='Continuous palette', options=['viridis', 'terrain', 'magma', 'Blues'])
        self.auto_limits = pn.widgets.Checkbox(name='Automatic color limits', value=True)
        self.low = pn.widgets.FloatInput(name='Color minimum', value=0, width=140)
        self.high = pn.widgets.FloatInput(name='Color maximum', value=1, width=140)
        self.network_choice = pn.widgets.Select(name='Stored network', options=['off', *self.reader.network_sources], value='nextxy' if 'nextxy' in self.reader.network_sources else 'off')
        self.width = pn.widgets.FloatSlider(name='Link width', start=.2, end=4, step=.2, value=1)
        self.color = pn.widgets.ColorPicker(name='Local / all links', value='#172b4d', width=140)
        self.flex_color = pn.widgets.ColorPicker(name='Flexible links', value='#e67e22', width=140)
        self.distinguish = pn.widgets.Checkbox(name='Distinguish Flexible Downstream', value=True)
        self.area_width = pn.widgets.Checkbox(name='Width by upstream area (not discharge)', value=False, disabled='uparea' not in self.reader.sources)
        self.area_color = pn.widgets.Checkbox(name='Color by upstream area (overrides type)', value=False, disabled='uparea' not in self.reader.sources)
        self.extent_inputs = [pn.widgets.FloatInput(name=k, value=v, width=140) for k, v in zip(['West', 'East', 'South', 'North'], self.reader.geometry.extent)]
        self.apply_extent_button = pn.widgets.Button(name='Apply extent', button_type='primary')
        self.reset_button = pn.widgets.Button(name='Full map')
        self.export_button = pn.widgets.Button(name='Export current view · PNG', button_type='primary')
        self.save_button = pn.widgets.Button(name='Save settings · JSON')
        self.upload = pn.widgets.FileInput(name='Load settings JSON', accept='.json')
        self.coordinate = Div(text='Pointer: longitude / latitude', width=300)
        self.selection_summary = pn.pane.Markdown('Click a map cell; detailed native values appear in **Cell inspector**.')
        g = self.reader.geometry
        self.plot = figure(x_range=Range1d(g.west, g.east), y_range=Range1d(g.south, g.north),
                           tools='pan,wheel_zoom,box_zoom,reset,tap,save', active_scroll='wheel_zoom',
                           title='CaMa-Flood · Map Explorer', x_axis_label='Longitude [°]', y_axis_label='Latitude [°]',
                           background_fill_color='#f5f7fa', toolbar_location='above',
                           sizing_mode='stretch_width', max_width=1000, min_width=260)
        self.plot.toolbar.logo = None
        resize = CustomJS(args={'plot': self.plot}, code='''
            const w = plot.x_range.end - plot.x_range.start;
            const h = plot.y_range.end - plot.y_range.start;
            const mid = (plot.y_range.start + plot.y_range.end) / 2;
            const ratio = w * Math.max(0.05, Math.cos(mid * Math.PI / 180)) / h;
            if (plot.inner_width > 0 && ratio > 0)
                plot.frame_height = Math.max(1, Math.round(plot.inner_width / ratio));
        ''')
        self.plot.js_on_change('inner_width', resize)
        self.image_source = ColumnDataSource(dict(image=[], x=[], y=[], dw=[], dh=[]))
        self.mapper = LinearColorMapper(palette=['#ffffff', '#000000'], low=0, high=1, nan_color='#f5f7fa')
        self.raster = self.plot.image_rgba(image='image', x='x', y='y', dw='dw', dh='dh', source=self.image_source)
        self.raster.nonselection_glyph = self.raster.glyph
        self.raster.selection_glyph = self.raster.glyph
        self.bar = ColorBar(color_mapper=self.mapper, title='')
        self.plot.add_layout(self.bar, 'right')
        self.link_source = ColumnDataSource(dict(x0=[], y0=[], x1=[], y1=[], width=[], color=[]))
        self.plot.segment('x0', 'y0', 'x1', 'y1', line_width='width', line_color='color', source=self.link_source)
        self.selected_source = ColumnDataSource(dict(x=[], y=[]))
        self.plot.scatter('x', 'y', source=self.selected_source, size=15, line_color='#e11d48', fill_alpha=0, line_width=3)
        self.selected_link = ColumnDataSource(dict(x0=[], y0=[], x1=[], y1=[]))
        self.plot.segment('x0', 'y0', 'x1', 'y1', source=self.selected_link, line_color='#e11d48', line_width=3)
        self.plot.add_tools(HoverTool(tooltips=[('lon', '$x{0.0000}'), ('lat', '$y{0.0000}')], renderers=[self.raster]))
        self.plot.js_on_event('mousemove', CustomJS(args={'target': self.coordinate}, code="target.text = `Pointer: ${cb_obj.x.toFixed(4)}°, ${cb_obj.y.toFixed(4)}°`;"))
        self.plot.on_event(Tap, self._tap)
        self.plot.on_event(RangesUpdate, self._navigation)
        self.apply_extent_button.on_click(lambda event: self._schedule(self.apply_extent))
        self.reset_button.on_click(lambda event: self._schedule(lambda: self.set_extent(g.extent)))
        self.export_button.on_click(lambda event: self._schedule(self.export))
        self.save_button.on_click(lambda event: self._schedule(self.save))
        self.upload.param.watch(lambda event: self._schedule(lambda: self.load(event.new)), 'value')
        for widget in (self.variable, self.scale, self.palette, self.auto_limits, self.low, self.high):
            widget.param.watch(lambda event: self._schedule(self.update_layer), 'value')
        for widget in (self.network_choice, self.width, self.color, self.flex_color, self.distinguish, self.area_width, self.area_color):
            widget.param.watch(lambda event: self._schedule(self.update_network), 'value')
        self.variable.value = 'uparea' if 'uparea' in self.reader.sources else next(iter(self.reader.sources))
        self._guard(self.update_layer)
        self._guard(self.update_network)
        controls = pn.Column(
            pn.pane.Markdown('## Display settings\nNative grid · read-only'),
            self.scale, self.palette, self.auto_limits, pn.Row(self.low, self.high),
            pn.layout.Divider(), self.width, pn.Row(self.color, self.flex_color),
            self.distinguish, self.area_width, self.area_color,
            pn.pane.Markdown('Area styling: log 1–10⁶ km²; no discharge inference.'),
            pn.layout.Divider(), pn.pane.Markdown('### Geographic extent'),
            pn.Row(*self.extent_inputs[:2]), pn.Row(*self.extent_inputs[2:]),
            pn.Row(self.apply_extent_button, self.reset_button),
            pn.layout.Divider(), self.export_button, self.save_button, self.upload,
            self.status, width=315, styles={'background': '#f4f7fb', 'padding': '12px'})
        diagnostics = '<br>'.join(escape(v) for v in self.reader.messages) or 'All supported products passed metadata checks.'
        header = pn.pane.HTML(f'<h1 style="margin-bottom:4px">CaMa-Flood <span style="color:#39758a">Map Explorer</span></h1><p>{escape(str(self.reader.path))} · {g.nx} × {g.ny} · {g.resolution:g}° · local & read-only</p>')
        details = pn.Column(pn.pane.Markdown('## Cell inspector\nFortran indices start at **1**.'), self.inspection,
                            pn.pane.Markdown('### Source diagnostics'), pn.pane.HTML(diagnostics, width=300), width=340)
        # Tabs keep the map and controls usable in a narrow desktop side panel
        # as well as a normal browser. Native aspect follows actual frame width.
        selectors = pn.FlexBox(self.variable, self.network_choice, flex_wrap='wrap')
        self.view = pn.Column(header, selectors, pn.Tabs(
            ('Explore', pn.Column(self.coordinate, self.selection_summary, self.network_summary, self.plot, sizing_mode='stretch_width')),
            ('Display & export', controls), ('Cell inspector', details), sizing_mode='stretch_width'), sizing_mode='stretch_width')

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
        extent = (max(g.west, self.plot.x_range.start), min(g.east, self.plot.x_range.end),
                  max(g.south, self.plot.y_range.start), min(g.north, self.plot.y_range.end))
        if extent[0] >= extent[1] or extent[2] >= extent[3]:
            extent = g.extent
        self._guard(lambda: self.set_extent(extent))

    def update_layer(self):
        name = self.variable.value
        layer = make_layer(self.reader, name, self.scale.value, self.palette.value,
                           None if self.auto_limits.value else (self.low.value, self.high.value))
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
        cls = LogColorMapper if layer.logarithmic else LinearColorMapper
        self.mapper = cls(palette=layer.palette, low=layer.low, high=layer.high, nan_color='#f5f7fa')
        self.bar.color_mapper = self.mapper
        self.bar.title = name + f' [{SCHEMA[name].display_units}]'
        if len(layer.categories):
            ticks = np.unique(np.linspace(0, len(layer.categories)-1, min(16, len(layer.categories))).astype(int))
            self.bar.ticker = FixedTicker(ticks=ticks.tolist())
            self.bar.major_label_overrides = {int(i): str(int(layer.categories[i])) for i in ticks}
        else:
            from bokeh.models import BasicTicker, LogTicker
            self.bar.ticker = LogTicker() if layer.logarithmic else BasicTicker()
            self.bar.major_label_overrides = {}
        self.plot.title.text = layer.label
        self.status.object = f'**Source:** `{self.reader.sources[name].path.name}`\n\n' + ('Discrete categories; colors may repeat.' if SCHEMA[name].categorical else 'Color transforms affect display only.')
        self.render_view()

    def network_options(self):
        return dict(width=self.width.value, color=self.color.value, flexible_color=self.flex_color.value,
                    distinguish=self.distinguish.value, scale_width=self.area_width.value, color_area=self.area_color.value)

    def update_network(self):
        name = self.network_choice.value
        if name == 'off':
            self.network = None
            self.network_summary.object = 'Network overlay hidden; stored connectivity remains inspectable.'
        else:
            if self._network_cache is None or self._network_cache.product != name:
                self._network_cache = RiverNetwork(self.reader, name)
            self.network = self._network_cache
            net = self.network
            self.network_summary.object = (f'**{name}:** {len(net.rows):,} links · {int(net.flexible.sum()):,} flexible. '
                                           f'Excluded: {net.counts["out_of_map"]} outside-map, {net.counts["mixed_codes"]} mixed-code, '
                                           f'{net.counts["self_links"]} self links. Terminal pairs: {net.counts["terminal_pairs"]}.')
        self.render_view()
        if self.selected:
            row, col = self.selected
            self.inspect(self.reader.geometry.lon[col], self.reader.geometry.lat[row])

    def render_view(self):
        if self.layer is None:
            return
        self._size_map()
        image, edges = raster_subset(self.layer, self.reader.geometry, self.extent)
        w, e, s, n = edges
        # Bokeh image row zero is southern: flip exactly once at this boundary.
        self.image_source.data = dict(image=[colorize(self.layer, image)[::-1]], x=[w], y=[s], dw=[e-w], dh=[n-s])
        if self.network is None:
            self.link_source.data = dict(x0=[], y0=[], x1=[], y1=[], width=[], color=[])
            self.selected_link.data = dict(x0=[], y0=[], x1=[], y1=[])
        else:
            net = self.network
            ids = net.visible(self.extent)
            widths, colors = network_style(net, self.reader, ids, **self.network_options())
            self.link_source.data = dict(x0=net.x0[ids], y0=net.y0[ids], x1=net.x1[ids], y1=net.y1[ids], width=widths, color=colors)

    def inspect(self, lon, lat):
        result = self.reader.inspect(lon, lat)
        row, col = self.reader.geometry.cell(lon, lat)
        self.selected = row, col
        self.selected_source.data = dict(x=[self.reader.geometry.lon[col]], y=[self.reader.geometry.lat[row]])
        # Inspection remains available when network visibility is off.
        net = self.network or self._network_cache
        if net is None and self.reader.network_sources:
            name = 'nextxy' if 'nextxy' in self.reader.network_sources else next(iter(self.reader.network_sources))
            self._network_cache = net = RiverNetwork(self.reader, name)
        if net is not None:
            result['network product'] = net.product
            result.update(net.inspect(row, col))
            ids = np.flatnonzero((net.rows[net.link_index] == row) & (net.cols[net.link_index] == col)) if self.network else np.array([], dtype=int)
            self.selected_link.data = dict(x0=net.x0[ids], y0=net.y0[ids], x1=net.x1[ids], y1=net.y1[ids])
        rows = ''.join(f'<tr><td style="padding:5px;border-bottom:1px solid #ddd">{escape(k)}</td><td style="padding:5px;border-bottom:1px solid #ddd">{escape("missing" if v is None else str(v))}</td></tr>' for k, v in result.items())
        self.inspection.object = f'<table style="width:100%;font-size:12px">{rows}</table><p>Raw source values; area units here are m². Pink ring = selected cell; pink line = its downstream link.</p>'
        self.selection_summary.object = f'**Selected cell (1-based):** ix={col+1}, iy={row+1} · {result.get("downstream status", "no network")} · Details in **Cell inspector**.'
        return result

    def _tap(self, event):
        self._guard(lambda: self.inspect(event.x, event.y))

    def _output(self, suffix):
        return self.output_dir / f'map-explorer-{datetime.now():%Y%m%d-%H%M%S-%f}{suffix}'

    def export(self):
        path = export_png(self.reader, self.variable.value, self.extent, self._output('.png'), layer=self.layer,
                          network=self.network, network_options=self.network_options(), selected=self.selected)
        self.status.object = f'**PNG saved:** `{path}`'
        return path

    def settings(self):
        return dict(version=1, map_path=str(self.reader.path), variable=self.variable.value, extent=list(self.extent),
                    scale=self.scale.value, palette=self.palette.value, limits=None if self.auto_limits.value else [self.low.value, self.high.value],
                    network=self.network_choice.value, network_options=self.network_options())

    def save(self):
        path = save_settings(self._output('.json'), self.settings())
        self.status.object = f'**Settings saved:** `{path}`'
        return path

    def load(self, content):
        if not content:
            return
        data = load_settings(content, self.reader)
        # Validate the complete display before mutating widgets/session state.
        make_layer(self.reader, data['variable'], data['scale'], data['palette'], data['limits'])
        self._updating = True
        try:
            self.variable.value, self.scale.value, self.palette.value = data['variable'], data['scale'], data['palette']
            self.auto_limits.value = data['limits'] is None
            if data['limits'] is not None:
                self.low.value, self.high.value = data['limits']
            self.network_choice.value = data['network']
            options = data['network_options']
            for widget, key in [(self.width, 'width'), (self.color, 'color'), (self.flex_color, 'flexible_color'),
                                (self.distinguish, 'distinguish'), (self.area_width, 'scale_width'), (self.area_color, 'color_area')]:
                widget.value = options[key]
        finally:
            self._updating = False
        self.set_extent(data['extent'])
        self.update_layer()
        self.update_network()
        self.status.object = '**Settings loaded.**'


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


if __name__ == '__main__':
    main()
