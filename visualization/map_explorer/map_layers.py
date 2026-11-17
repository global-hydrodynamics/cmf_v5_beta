"""Shared display-only transforms and PNG export; native map values stay intact."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from matplotlib import colormaps
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.collections import LineCollection
from matplotlib.colors import BoundaryNorm, ListedColormap, LogNorm, Normalize, to_hex
from matplotlib.figure import Figure

from map_reader import SCHEMA


@dataclass
class DisplayLayer:
    image: np.ndarray
    palette: list
    low: float
    high: float
    logarithmic: bool
    categories: np.ndarray
    label: str


LOG_DISPLAY_MINIMUM = 0.01


def log_display_limits(low, high):
    """Compatibility helper only; Explorer Auto no longer uses this legacy fallback.

    An all-nonpositive reference still needs a positive, nondegenerate colorbar;
    its finite data use the lower-end color, never invented scientific values.
    """
    low = float(low) if low is not None and np.isfinite(low) and low > 0 else LOG_DISPLAY_MINIMUM
    high = float(high) if high is not None and np.isfinite(high) and high > low else low * 10
    return low, high


def log_display_values(values, minimum, mask_nonpositive=True):
    """Mask nonpositive Log pixels; saturate positive under-range values, without data edits."""
    values = np.ma.asarray(values).astype(float).filled(np.nan)
    return np.where(np.isfinite(values) & ((values > 0) if mask_nonpositive else True), np.maximum(values, minimum), np.nan)


def resolve_color_limits(low, high, logarithmic=False, *, manual=False):
    """Physical display bounds, never a transformation of scientific data.

    Automatic percentiles include valid nonpositive values before the Log floor.
    Manual bounds are authoritative. A degenerate Log range is an error rather
    than an invented positive upper value. Constant Linear fields retain the
    historical small display-only expansion needed by continuous colorbars.
    """
    low, high = float(low), float(high)
    if not np.isfinite([low, high]).all() or high < low:
        raise ValueError("Color limits must be finite and ordered")
    if logarithmic:
        low = LOG_DISPLAY_MINIMUM if not manual and low <= 0 else low
        if low <= 0 or high <= low:
            raise ValueError("Cannot construct a valid logarithmic color range: require 0 < lower < upper")
    elif high == low:
        if manual:
            raise ValueError("Manual Color Maximum must exceed Color Minimum")
        high = low + max(abs(low)*.01, .01)
    return low, high


def percentile_limits(values, logarithmic=False):
    values = np.ma.asarray(values).astype(float).filled(np.nan)
    valid = values[np.isfinite(values)]
    if not valid.size:
        raise ValueError("No valid finite reference values for automatic color limits")
    return resolve_color_limits(*np.percentile(valid, (5,95)), logarithmic)


def layer_colors(layer):
    """One normalization contract shared by browser pixels and PNG export."""
    cmap = ListedColormap(layer.palette).with_extremes(bad='#f5f7fa')
    if len(layer.categories):
        norm = BoundaryNorm(np.arange(len(layer.categories)+1)-.5, len(layer.palette))
    else:
        norm = (LogNorm if layer.logarithmic else Normalize)(layer.low, layer.high)
    return cmap, norm


def colorize(layer, image):
    """Pack RGBA pixels for Bokeh; avoid stale mapper/selection-glyph state."""
    cmap, norm = layer_colors(layer)
    rgba = np.ascontiguousarray((cmap(norm(np.ma.masked_invalid(image)))*255).astype(np.uint8))
    return rgba.view('<u4').reshape(image.shape)


def validate_palette_range(value=None):
    value = [0.0, 1.0] if value is None else value
    if not isinstance(value, (list, tuple)) or len(value) != 2 or any(isinstance(v, bool) for v in value):
        raise ValueError("Palette range needs minimum and maximum in [0,1]")
    lo, hi = map(float, value)
    if not np.isfinite([lo, hi]).all() or not 0 <= lo < hi <= 1:
        raise ValueError("Palette Minimum must be below Palette Maximum within [0,1]")
    return [lo, hi]



def make_layer(reader, name, scale='auto', palette='viridis', limits=None, palette_range=None, reference_policy="percentile"):
    spec = SCHEMA[name]
    raw = reader.read(name)
    values = raw.astype(float).filled(np.nan) * spec.factor
    label = f'{name} — {spec.title} [{spec.display_units}]'
    if spec.categorical:
        if palette in ('basin_pastel','subcol_pastel','subcol_gray'):
            # Gallery palettes classify stored display IDs, never interpolate
            # or infer basin identity from color. Zero has a defined subcol gray.
            minimum=1 if palette=='basin_pastel' else 0
            categories=np.arange(minimum,11)
            valid=np.isfinite(values)&(values>=minimum)&(values<=10)&(values==np.floor(values))
            image=np.full(values.shape,np.nan);image[valid]=values[valid]-minimum
            if palette=='subcol_gray':
                colors=[to_hex((v,v,v)) for v in [.50,*np.linspace(.45,.10,10)]]
            else:
                rgba=colormaps['tab10'](np.arange(10));rgba[:,:3]=.4*rgba[:,:3]+.6
                colors=[to_hex(v) for v in rgba]
                if minimum==0:
                    colors=['#b2b2b2',*colors]
            return DisplayLayer(image,colors,-.5,len(categories)-.5,False,categories,label)
        # IDs are categorical, including zero if supplied as a valid value.
        # Dense display slots are internal; ticks and inspection retain raw IDs.
        finite = np.isfinite(values)
        categories = np.unique(values[finite])
        if np.any(categories != np.floor(categories)):
            raise ValueError(f'{name}: non-integer categorical value')
        if not len(categories):
            raise ValueError(f'{name}: no valid categories')
        image = np.full(values.shape, np.nan)
        image[finite] = np.searchsorted(categories, values[finite])
        cmap = colormaps['tab20']
        colors = [to_hex(cmap(int(c) % cmap.N)) for c in categories]
        return DisplayLayer(image, colors, -.5, len(categories)-.5, False, categories, label)
    logarithmic = spec.logarithmic if scale == 'auto' else scale == 'log'
    finite = values[np.isfinite(values)]
    if not finite.size:
        raise ValueError(f'{name}: no values usable with this color scale')
    # Gallery palettes and transfer curves remain independent of Auto statistics.
    # Legacy JSON policy flags are accepted but no longer bypass the valid P5/P95 reference.
    if limits is None:
        low, high = percentile_limits(finite, logarithmic)
    else:
        low, high = resolve_color_limits(*limits, logarithmic, manual=True)
    if logarithmic:
        values = log_display_values(values, low)
    lo, hi = validate_palette_range(palette_range)
    colors = [to_hex(colormaps[palette](lo + (i/255)*(hi-lo))) for i in range(256)]
    return DisplayLayer(values, colors, low, high, logarithmic, np.array([]), label)


def raster_subset(layer, geometry, extent, max_side=1200):
    """Crop first, then choose representative native cells; never average IDs."""
    w, e, s, n = extent
    g = geometry
    c0 = max(0, int(np.floor((w-g.west)/g.resolution)))
    c1 = min(g.nx, int(np.ceil((e-g.west)/g.resolution)))
    r0 = max(0, int(np.floor((g.north-n)/g.resolution)))
    r1 = min(g.ny, int(np.ceil((g.north-s)/g.resolution)))
    if c1 <= c0 or r1 <= r0:
        return np.full((1, 1), np.nan), (w, e, s, n)
    rows = np.minimum(r1-1, r0+((np.arange(min(r1-r0, max_side))+.5)*(r1-r0)/min(r1-r0, max_side)).astype(int))
    cols = np.minimum(c1-1, c0+((np.arange(min(c1-c0, max_side))+.5)*(c1-c0)/min(c1-c0, max_side)).astype(int))
    # This image summarizes the viewport only. Native values remain available
    # on tap; resampling is explicitly not a new scientific map product.
    image = layer.image[np.ix_(rows, cols)]
    edges = (g.west+c0*g.resolution, g.west+c1*g.resolution,
             g.north-r1*g.resolution, g.north-r0*g.resolution)
    return image, edges


def network_style(network, reader, visible, width=1, color='#172b4d', flexible_color='#e67e22',
                  distinguish=True, scale_width=False, color_area=False):
    links = network.link_index[visible]
    widths = np.full(len(visible), width, dtype=float)
    colors = np.full(len(visible), color, dtype=object)
    if distinguish:
        colors[network.flexible[links]] = flexible_color
    if (scale_width or color_area) and 'uparea' in reader.sources:
        # Upstream contributing area is not discharge. This log display factor
        # is a visual style only, with a fixed reference range of 1..1e6 km².
        area = reader.read('uparea')[network.rows[links], network.cols[links]].astype(float).filled(np.nan)*1e-6
        fraction = np.clip(np.log10(np.maximum(area, 1))/6, 0, 1)
        fraction = np.nan_to_num(fraction)
        if scale_width:
            widths *= .5 + 3*fraction
        if color_area:
            colors = np.array([to_hex(colormaps['viridis'](v)) for v in fraction])
    return widths, colors


def export_png(reader, name, extent, path, layer=None, network=None, network_options=None, selected=None):
    """Export current extent/styles with Agg; no browser or source-map writes."""
    reader.geometry.validate_extent(extent)
    g = reader.geometry
    layer = layer or make_layer(reader, name)
    image, edges = raster_subset(layer, g, extent, max_side=2400)
    w, e, s, n = extent
    aspect = 1/max(.05, np.cos(np.deg2rad((s+n)/2)))
    width = float(np.clip(8*(e-w)/((n-s)*aspect), 5, 16))
    fig = Figure(figsize=(width, 8), layout='constrained')
    FigureCanvasAgg(fig)
    ax = fig.add_subplot()
    cmap, norm = layer_colors(layer)
    art = ax.imshow(np.ma.masked_invalid(image), extent=edges, origin='upper', cmap=cmap, norm=norm, interpolation='nearest')
    bar = fig.colorbar(art, ax=ax, shrink=.85)
    bar.set_label(layer.label)
    if len(layer.categories):
        ticks = np.unique(np.linspace(0, len(layer.categories)-1, min(16, len(layer.categories))).astype(int))
        bar.set_ticks(ticks, labels=[str(int(layer.categories[i])) for i in ticks])
    options = network_options or {}
    if network is not None:
        visible = network.visible(extent)
        widths, colors = network_style(network, reader, visible, **options)
        segments = np.stack([np.column_stack([network.x0[visible], network.y0[visible]]),
                             np.column_stack([network.x1[visible], network.y1[visible]])], axis=1)
        ax.add_collection(LineCollection(segments, colors=colors, linewidths=widths*.75))
        if options.get('color_area'):
            ax.plot([], [], color='#444444', label='Links: contributing area, log 1–10⁶ km²')
        else:
            ax.plot([], [], color=options.get('color', '#172b4d'), label='Local / all links')
            if options.get('distinguish', True):
                ax.plot([], [], color=options.get('flexible_color', '#e67e22'), label='Flexible Downstream')
        ax.legend(loc='lower left', fontsize=8)
    if selected is not None:
        row, col = selected
        ax.plot(g.lon[col], g.lat[row], 'o', ms=9, mfc='none', mec='#e11d48', mew=2)
        if network:
            ids = np.flatnonzero((network.rows[network.link_index] == row) & (network.cols[network.link_index] == col))
            for i in ids:
                ax.plot([network.x0[i], network.x1[i]], [network.y0[i], network.y1[i]], color='#e11d48', lw=3)
    ax.set(xlim=(w, e), ylim=(s, n), xlabel='Longitude [°]', ylabel='Latitude [°]', title=f'CaMa-Flood · {reader.path.name}\n{layer.label}')
    ax.set_aspect(aspect)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, metadata={'Description': f'MAP_DIR={reader.path}; extent={extent}; variable={name}'})
    return path
