"""Physical high-resolution limits/norms, palette transfer and raster alpha."""

from __future__ import annotations

import numpy as np
from matplotlib import colormaps
from matplotlib.colors import LinearSegmentedColormap, to_hex

from map_layers import (
    DisplayLayer,
    log_display_limits,
    log_display_values,
    validate_palette_range,
    resolve_color_limits,
)
from map_reader import SCHEMA

# Approved cmf_colormap/data/pale_terrain.json v1.0.0 linear-sRGB controls.
# Existing Gallery palettes; runtime does not import Gallery scripts.
PALE_TERRAIN = ("#E8FAFA", "#EEFBF6", "#F4F9E8", "#FFFCE9", "#FFF4E5", "#FCEBE5", "#F9DADB", "#F6C9CE")
CATCHMENT_GREEN = ("#FFFFD4", "#D9F0A3", "#78C679", "#31A354")
PALETTES = {
    "Gallery Default": "gallery",
    "Gray": "gray",
    "Gray (reversed)": "gray_r",
    "Pale Terrain": "pale_terrain",
    "Viridis": "viridis",
    "YlGn": "YlGn",
    "YlGnBu": "YlGnBu",
    "Terrain": "terrain",
    "Plasma": "plasma",
    "Magma": "magma",
    "Blues": "Blues",
}
SCALES = {"Gallery Default": "gallery", "Linear": "linear", "Log": "log"}


def validate_style(style=None, gallery_log=False):
    if not isinstance(style, (dict, type(None))):
        raise ValueError("highres_style must be an object")
    result = {"palette": "gallery", "scale": "gallery", "limits": None, "palette_range": [0.0, 1.0], **(style or {})}
    if set(result) != {"palette", "scale", "limits", "palette_range"}:
        raise ValueError("highres_style must contain only palette, scale, limits and palette_range")
    if result["palette"] not in PALETTES.values() or result["scale"] not in SCALES.values():
        raise ValueError("Unsupported high-resolution palette/scale")
    result["palette_range"] = validate_palette_range(result["palette_range"])
    limits = result["limits"]
    if limits is not None:
        if not isinstance(limits, (list, tuple)) or len(limits) != 2:
            raise ValueError("High-resolution limits need minimum and maximum")
        try:
            low, high = map(float, limits)
        except (ValueError, TypeError) as exc:
            raise ValueError("High-resolution limits must be numeric") from exc
        if not np.isfinite([low, high]).all() or not low < high:
            raise ValueError("Color Maximum must be greater than Color Minimum; both must be finite")
        if result["scale"] == "log" or result["scale"] == "gallery" and gallery_log:
            low, high = resolve_color_limits(low, high, True, manual=True)
        result["limits"] = [low, high]
    return result


def apply_opacity(rgba, opacity=1.0):
    """Multiply existing alpha, never make originally transparent pixels opaque."""
    if not isinstance(opacity, (float, int)) or not np.isfinite(opacity) or not 0 <= opacity <= 1:
        raise ValueError("Background opacity must be between 0 and 1")
    if opacity == 1:
        return rgba
    result = np.ascontiguousarray(rgba).copy()
    channels = result.view("u1").reshape((*result.shape, 4))
    channels[..., 3] = np.rint(channels[..., 3].astype(float) * opacity).astype("u1")
    return result


def highres_layer(
    image, reader, tile, mode, name, coarse_layer, style=None, terrain_palette="gray", reference_policy="percentile"
):
    """Build one physical-unit DisplayLayer; full-reference limits never use view."""
    catchment = mode == "catchment"
    gallery_log = catchment and SCHEMA[name].logarithmic
    options = validate_style(style, gallery_log)
    logarithmic = options["scale"] == "log" or options["scale"] == "gallery" and gallery_log
    values = np.asarray(image, dtype=float).copy()
    legacy = reference_policy == "gallery" and options["scale"] == "gallery" and options["limits"] is None
    if options["limits"] is not None:
        low, high = resolve_color_limits(*options["limits"], logarithmic, manual=True)
    elif catchment and legacy:
        reference = reader.read(name).astype(float).filled(np.nan) * SCHEMA[name].factor
        good = np.isfinite(reference) & ((reference > 0) if logarithmic else True)
        if not good.any() and not logarithmic:
            raise ValueError("No finite catchment values")
        low, high = (float(reference[good].min()), float(reference[good].max())) if good.any() else (None, None)
        if not logarithmic and high <= low:
            high = low + max(abs(low) * 0.01, 0.01)
    else:
        inherited = reader.read(name).astype(float).filled(np.nan) * SCHEMA[name].factor if catchment else None
        low, high = tile.percentiles(
            name if catchment else mode,
            positive=legacy and logarithmic,
            allow_empty=legacy and logarithmic,
            coarse=reader.geometry,
            quantiles=(2, 98) if legacy else (3, 97),
            inherited=inherited,
        )
        if not legacy:
            low, high = resolve_color_limits(low, high, logarithmic)
    if logarithmic:
        if legacy:
            low, high = log_display_limits(None, high)
        values = log_display_values(values, low, mask_nonpositive=not legacy)
    t = np.linspace(0, 1, 256)
    pmin, pmax = options["palette_range"]
    crop = lambda positions: pmin + positions * (pmax - pmin)
    chosen = options["palette"]
    gallery = options["scale"] == "gallery"
    if chosen == "gallery" and catchment:
        if name == "uparea":
            cmap = LinearSegmentedColormap.from_list("catchment", CATCHMENT_GREEN)
            palette = [to_hex(cmap(v)) for v in crop(t)]
        else:
            palette = coarse_layer.palette  # preserve legacy inherited-field colors
            if options["palette_range"] != [0.0, 1.0]:
                cmap = LinearSegmentedColormap.from_list("legacy", palette)
                palette = [to_hex(cmap(v)) for v in crop(t)]
    else:
        effective = terrain_palette if chosen == "gallery" else chosen
        cmap = (
            LinearSegmentedColormap.from_list("pale_terrain", PALE_TERRAIN)
            if effective == "pale_terrain"
            else colormaps[effective]
        )
        transfer = t
        if gallery and not catchment:
            transfer = t**0.2 if effective == "pale_terrain" else np.sqrt(t)
        if chosen == "gallery" and effective == "gray" and not catchment:
            transfer = 0.16 + 0.42 * transfer  # original subdued Gallery gray range
        palette = [to_hex(cmap(v)) for v in crop(transfer)]
    title = (
        coarse_layer.label + " inherited by assigned unit catchment"
        if catchment
        else (
            "Maximum 8-neighbor elevation difference [m], not slope"
            if mode == "difference"
            else f"High-resolution {mode} [m]"
        )
    )
    return DisplayLayer(values, palette, float(low), float(high), bool(logarithmic), np.array([]), title)


def neutral_floodplain_color(style=None, terrain_palette="gray"):
    """Preserve original missing-flddif neutral fill; it is never measured data."""
    options = validate_style(style)
    if options["palette"] == "gallery":
        if terrain_palette == "gray":
            return np.array(np.round(np.asarray(colormaps["gray"](0.5)) * 255), dtype="u1").view("<u4")[0]
        cmap = LinearSegmentedColormap.from_list("pale_terrain", PALE_TERRAIN)
        intensity = ((0.5 - 0.16) / 0.42) ** 0.4
        return np.array(np.round(np.asarray(cmap(intensity)) * 255), dtype="u1").view("<u4")[0]
    return np.array([128, 128, 128, 255], dtype="u1").view("<u4")[0]
