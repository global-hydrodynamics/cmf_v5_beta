"""Optional coarse products: stored outlets and unique bifurcation pathways."""

from copy import copy
from functools import cached_property

import numpy as np
from netCDF4 import Dataset

from map_reader import Source
from river_network import intersects


def split_segments(geometry, x0, y0, x1, y1, indices):
    """Split periodic seam geometry while retaining each scientific record ID."""
    seam = (np.abs(x1 - x0) > 180) if geometry.periodic else np.zeros(len(x0), dtype=bool)
    adjusted = x1[seam] + np.where(x1[seam] < x0[seam], 360, -360)
    edge = np.where(adjusted > x0[seam], geometry.east, geometry.west)
    fraction = (edge - x0[seam]) / (adjusted - x0[seam])
    crossing = y0[seam] + fraction * (y1[seam] - y0[seam])
    other = np.where(edge == geometry.east, geometry.west, geometry.east)
    return (
        np.concatenate([x0[~seam], x0[seam], other]),
        np.concatenate([y0[~seam], y0[seam], crossing]),
        np.concatenate([x1[~seam], edge, x1[seam]]),
        np.concatenate([y1[~seam], crossing, y1[seam]]),
        np.concatenate([indices[~seam], indices[seam], indices[seam]]),
    )


class Products:
    def __init__(self, reader):
        self.reader = reader
        self.messages = []
        self.outlet_source = None
        # Longitude and latitude have different units; validate separately.
        for path in (reader.path / "lonlat.nc", reader.path / "netcdf/lonlat.nc", reader.path / "binary/lonlat.bin", reader.path / "lonlat.bin"):
            if not path.is_file():
                continue
            try:
                if path.suffix == ".nc":
                    with Dataset(path) as ds:
                        for name, units in [("outlon", "degrees_east"), ("outlat", "degrees_north")]:
                            reader._nc_variable(ds, ds.variables[name], "<f4", units)
                elif path.stat().st_size != reader.geometry.nx * reader.geometry.ny * 8:
                    raise ValueError("wrong two-record Float32 outlet size")
                self.outlet_source = Source(path, path.suffix == ".nc", ("outlon", "outlat"))
                break
            except (OSError, ValueError, KeyError) as exc:
                self.messages.append(f"Outlets skipped: {exc}")
        self.bif_path = next(
            (p for p in [reader.path / "bifprm.nc", reader.path / "netcdf/bifprm.nc"] if p.is_file()), None
        )
        self._views = {}

    @cached_property
    def outlets(self):
        if self.outlet_source is None:
            raise ValueError("No supported lonlat outlet product")
        source = self.outlet_source
        if source.netcdf:
            a, b = (
                self.reader._load(source, name, i).astype(float).filled(np.nan) for i, name in enumerate(source.names)
            )
        else:
            g = self.reader.geometry
            raw = np.memmap(source.path, mode="r", dtype="<f4", shape=(2, g.ny, g.nx))
            a, b = raw[0].astype(float), raw[1].astype(float)
        valid = np.isfinite(a) & np.isfinite(b) & (a >= -180) & (a <= 360) & (b >= -90) & (b <= 90)
        g = self.reader.geometry
        # Regional stored outlets can lie slightly outside the raster extent.
        # Preserve those actual coordinates; wrapping them would invent links
        # displaced by 360 degrees. Only a complete global grid is periodic.
        if g.periodic:
            a = g.west + (a - g.west) % 360
        a[~valid] = np.nan
        b[~valid] = np.nan
        return a, b

    def network_view(self, network, representation):
        if representation == "grid_center":
            return network
        if representation != "outlet_vector":
            raise ValueError("Unsupported network representation")
        if network.product not in self._views:
            a, b = self.outlets
            sr, sc, dr, dc = network.rows, network.cols, network.dest_rows, network.dest_cols
            x0, y0, x1, y1 = a[sr, sc], b[sr, sc], a[dr, dc], b[dr, dc]
            valid = np.isfinite(x0) & np.isfinite(y0) & np.isfinite(x1) & np.isfinite(y1)
            view = copy(network)
            view.representation = "outlet_vector"
            # Endpoint validity can change the reference population for full-
            # network classes. Do not inherit the grid-center summary cache.
            view.__dict__.pop("_area_summary", None)
            view.__dict__.pop("_area_range_summary", None)
            view.x0, view.y0, view.x1, view.y1, view.link_index = split_segments(
                network.geometry, x0[valid], y0[valid], x1[valid], y1[valid], np.flatnonzero(valid)
            )
            self._views[network.product] = view
        return self._views[network.product]

    @cached_property
    def bifurcations(self):
        if self.bif_path is None:
            raise ValueError("No NetCDF bifurcation table")
        with Dataset(self.bif_path) as ds:
            index = []
            for name in ("ix", "iy", "jx", "jy"):
                v = ds.variables[name]
                if v.dimensions != ("path",) or v.dtype.kind not in "iu":
                    raise ValueError(f"bifprm:{name} must contain integer path indices")
                index.append(np.ma.asarray(v[:]).astype("i8").filled(-9999))
            river_var = ds.variables["riv_width"]
            if river_var.dimensions != ("path",) or getattr(river_var, "units", "") != "m":
                raise ValueError("bifprm:riv_width requires (path), units m")
            widths = np.ma.asarray(river_var[:]).astype(float).filled(np.nan)[np.newaxis, :]
            if "ovl_width" in ds.variables:
                overland_var = ds.variables["ovl_width"]
                if (overland_var.dimensions != ("layer", "path") or
                        getattr(overland_var, "units", "") != "m" or not overland_var.shape[0]):
                    raise ValueError("bifprm:ovl_width requires non-empty (layer,path), units m")
                overland = np.ma.asarray(overland_var[:]).astype(float).filled(np.nan)
                if overland.shape[1] != widths.shape[1]:
                    raise ValueError("Bifurcation overland layer/path dimensions disagree")
                widths = np.concatenate((widths, overland), axis=0)
            elif "layer" in ds.dimensions:
                raise ValueError("bifprm:layer dimension requires ovl_width")
            endpoints = {
                name: np.ma.asarray(ds.variables[name][:]).astype(float).filled(np.nan)
                for name in ("end_lon", "end_lat")
                if name in ds.variables
            }
        ix, iy, jx, jy = index
        g = self.reader.geometry
        if widths.shape[1] != len(ix):
            raise ValueError("Bifurcation layer/path dimensions disagree")
        good_index = (
            (ix >= 1) & (ix <= g.nx) & (iy >= 1) & (iy <= g.ny) & (jx >= 1) & (jx <= g.nx) & (jy >= 1) & (jy <= g.ny)
        )
        good_width = np.all(np.isfinite(widths) & (widths >= 0), axis=0)
        ids = np.flatnonzero(good_index & good_width)
        a, b = self.outlets
        x0, y0, x1, y1 = (
            a[iy[ids] - 1, ix[ids] - 1],
            b[iy[ids] - 1, ix[ids] - 1],
            a[jy[ids] - 1, jx[ids] - 1],
            b[jy[ids] - 1, jx[ids] - 1],
        )
        good = np.isfinite(x0) & np.isfinite(y0) & np.isfinite(x1) & np.isfinite(y1)
        ids, x0, y0, x1, y1 = (v[good] for v in (ids, x0, y0, x1, y1))
        if "end_lon" in endpoints and "end_lat" in endpoints:
            expected_x = endpoints["end_lon"][ids]
            if g.periodic:
                expected_x = g.west + (expected_x - g.west) % 360
            if not (
                np.allclose(x1, expected_x, rtol=0, atol=1e-5)
                and np.allclose(y1, endpoints["end_lat"][ids], rtol=0, atol=1e-5)
            ):
                raise ValueError("Bifurcation destination indices disagree with recorded outlet coordinates")
        # Gallery f04 keeps the first valid directed endpoint pair. Preserve
        # direction: reversed endpoints are a different recorded connection.
        unique, seen, conflicts = [], {}, 0
        for n, path_id in enumerate(ids):
            pair = tuple(int(v[path_id]) for v in index)
            if pair not in seen:
                seen[pair] = path_id
                unique.append(n)
            elif not np.array_equal(widths[:, path_id], widths[:, seen[pair]]):
                conflicts += 1
        u = np.asarray(unique, dtype=int)
        stats = dict(
            invalid_indices=int((~good_index).sum()),
            invalid_widths=int((good_index & ~good_width).sum()),
            invalid_outlets=int((~good).sum()),
            duplicates=len(ids) - len(u),
            conflicting_duplicates=conflicts,
        )
        ids = ids[u]
        first = widths[0, ids]
        return dict(
            ids=ids,
            segments=np.stack([np.column_stack([x0[u], y0[u]]), np.column_stack([x1[u], y1[u]])], axis=1),
            first_width=first,
            widths=widths[:, ids],
            indices=np.asarray(index)[:, ids],
            channel=first > 0,
            stats=stats,
        )


AREA_COLORS = ("#5E88BE", "#4F80BF", "#285A9B", "#103A70")


RIVER_GRADIENTS = {
    "blue_navy": AREA_COLORS,  # Exactly the p01-f03a/f04b Gallery quartet.
    "gray_black": ("#BDBDBD", "#969696", "#525252", "#111111"),
    "gray_white": ("#777777", "#A0A0A0", "#CCCCCC", "#F5F5F5"),
}
AREA_PALETTES = (
    "viridis",
    "plasma",
    "magma",
    "cividis",
    "YlGnBu",
    "YlGn",
    "Blues",
    "turbo",
    "shade_rainbow",
    *RIVER_GRADIENTS,
)
AREA_COLOR_STYLES = ("palette", "gallery_quartiles", "gallery_continuous")


def validate_area_limits(limits):
    if limits is None:
        return None
    if not isinstance(limits, (list, tuple)) or len(limits) != 2:
        raise ValueError("Area limits require minimum and maximum [km²]")
    try:
        low, high = map(float, limits)
    except (TypeError, ValueError) as exc:
        raise ValueError("Area limits must be numeric") from exc
    if not np.isfinite([low, high]).all() or not 0 < low < high:
        raise ValueError("Area limits must be finite and positive, with maximum greater than minimum")
    return [low, high]


def area_style(
    network,
    reader,
    visible,
    width=1,
    color="#172b4d",
    flexible_color="#e67e22",
    distinguish=True,
    scale_width=False,
    color_area=False,
    classification="quartiles",
    area_palette="viridis",
    area_limits=None,
    area_color_style="palette",
    area_scale="log",
):
    """Source-area mapping over complete valid links; color limits never change width/topology."""
    from matplotlib import colormaps
    from matplotlib.colors import to_hex, LinearSegmentedColormap

    if area_palette not in AREA_PALETTES or area_color_style not in AREA_COLOR_STYLES:
        raise ValueError("Unknown network area palette/style")
    limits = validate_area_limits(area_limits)
    if area_scale not in ("linear", "log"):
        raise ValueError("Unknown network area scale")
    # Approved cmf_colormap shade_rainbow v1.0.0 linear-sRGB controls.
    cmap = (
        LinearSegmentedColormap.from_list(
            "shade_rainbow",
            [
                "#AAAAAA",
                "#C3ADC8",
                "#B49DE3",
                "#6096F4",
                "#00B7E7",
                "#00D5BD",
                "#1BF607",
                "#D2F500",
                "#F6D800",
                "#FF9914",
                "#F22F29",
                "#EB00ED",
            ],
        )
        if area_palette == "shade_rainbow"
        else (
            LinearSegmentedColormap.from_list(area_palette, RIVER_GRADIENTS[area_palette])
            if area_palette in RIVER_GRADIENTS
            else colormaps[area_palette]
        )
    )
    if classification not in ("quartiles", "six_log", "continuous", "fixed"):
        raise ValueError("Unknown area classification")
    if not hasattr(network, "_areas"):
        network._areas = (
            reader.read("uparea")[network.rows, network.cols].astype(float).filled(np.nan) * 1e-6
            if "uparea" in reader.sources
            else np.full(len(network.rows), np.nan)
        )
    raw = network._areas
    good = np.isfinite(raw) & (raw > 0)
    # Unique scientific links avoid counting periodic seam display pieces twice.
    # Outlet views use only valid endpoints, not the grid-center population.
    if not hasattr(network, "_area_range_summary"):
        present = np.unique(network.link_index)
        full = raw[present][good[present]]
        network._area_range_summary = (
            len(full), float(full.min()) if len(full) else 1.0,
            float(full.max()) if len(full) else 10.0,
        )
    count, minimum, maximum = network._area_range_summary
    lo, hi = np.log10([minimum, maximum])
    # Kept for UI/reference introspection; these are equal Log cuts, not quantiles.
    network._area_summary = (count, lo, hi, np.linspace(lo, hi, 5)[1:-1])
    if (scale_width or color_area) and not count:
        raise ValueError("No positive source-cell upstream areas for network style")
    ids = network.link_index[visible]
    a = raw[ids]
    usable = np.isfinite(a) & (a > 0)
    effective_scale = "log" if classification == "fixed" else area_scale
    transformed = np.zeros(len(a))
    transformed[usable] = np.log10(a[usable]) if effective_scale == "log" else a[usable]

    def physical(value):
        return 10**value if effective_scale == "log" else value

    def mapping(lower, upper):
        fraction = np.zeros(len(a))
        if upper > lower:
            fraction[usable] = np.clip((transformed[usable] - lower) / (upper - lower), 0, 1)
        if classification in ("quartiles", "six_log"):
            # Legacy serialized IDs now mean 4/6 equal value-range intervals.
            # Population frequency and viewport never determine class boundaries.
            classes = 4 if classification == "quartiles" else 6
            edges = np.linspace(lower, upper, classes + 1)
            levels = np.zeros(len(a), dtype=int)
            if upper > lower:
                levels[usable] = np.searchsorted(edges[1:-1], transformed[usable], side="right")
            positions = levels / (classes - 1)
            labels = [f"{effective_scale.title()} {i+1}: {physical(edges[i]):.3g}–{physical(edges[i+1]):.3g} km²"
                      for i in range(classes)]
        else:
            positions = fraction
            labels = [f"{effective_scale}: {physical(lower):.3g}–{physical(upper):.3g} km²"]
        return fraction, positions, labels

    width_lo, width_hi = ((0.0, 6.0) if classification == "fixed" else
                          (lo, hi) if effective_scale == "log" else (minimum, maximum))
    _, positions, width_labels = mapping(width_lo, width_hi)
    widths = np.full(len(a), float(width))
    if scale_width:
        widths *= 0.5 + 3 * positions if classification == "fixed" else 1 + 2 * positions
        widths[~usable] = 0.5 * width if classification == "fixed" else width
    # Manual COLOR limits deliberately do not enter the WIDTH calculation.
    color_lo, color_hi = ((np.log10(limits) if effective_scale == "log" else limits)
                          if limits is not None and classification != "fixed" else (width_lo, width_hi))
    fraction, color_positions, color_labels = mapping(color_lo, color_hi)
    if area_color_style == "gallery_continuous" and classification in ("six_log", "quartiles"):
        color_positions = fraction
        color_labels = [
            f"continuous {effective_scale}: {physical(color_lo):.3g}–{physical(color_hi):.3g} km² "
            f"(Gallery; {4 if classification=='quartiles' else 6} equal-range width classes)"
        ]
    colors = np.array([to_hex(cmap(v)) for v in color_positions], dtype=object)
    if classification == "quartiles" and (area_color_style == "gallery_quartiles" or (area_color_style == "palette" and area_palette == "blue_navy")):
        colors = np.asarray(AREA_COLORS, dtype=object)[np.rint(color_positions * 3).astype(int)]
    if area_color_style == "palette" and classification != "fixed":
        colors[~usable] = "#888888"
    if not color_area:
        colors = np.full(len(a), color, dtype=object)
        if distinguish:
            colors[network.flexible[ids]] = flexible_color
    legend, swatches = [], []
    if color_area or scale_width:
        method = {"quartiles": "4 equal intervals", "six_log": "6 equal intervals",
                  "continuous": "continuous", "fixed": "legacy fixed range"}[classification]
        legend.append(f"Upstream contributing drainage area (not discharge); {method}; {effective_scale}")
        if (~usable).any():
            legend.append(
                "Missing/nonpositive area: historical minimum width/color; links retained"
                if classification == "fixed"
                else "Missing/nonpositive area: base width; gray for generic area colors; links retained"
            )
    for kind, enabled, lower, upper, labels in [
        ("Color", color_area, color_lo, color_hi, color_labels),
        ("Width", scale_width, width_lo, width_hi, width_labels),
    ]:
        if not enabled:
            continue
        legend += [kind + ": " + label for label in labels]
        classes = (
            4
            if classification == "quartiles" and not (kind == "Color" and area_color_style == "gallery_continuous")
            else (
                6
                if classification == "six_log" and not (kind == "Color" and area_color_style == "gallery_continuous")
                else 5
            )
        )
        for i, v in enumerate(np.linspace(0, 1, classes)):
            c = (
                (
                    AREA_COLORS[i]
                    if classification == "quartiles" and (area_color_style == "gallery_quartiles" or (area_color_style == "palette" and area_palette == "blue_navy"))
                    else to_hex(cmap(v))
                )
                if kind == "Color"
                else color
            )
            line_width = width * (0.5 + 3 * v if classification == "fixed" else 1 + 2 * v) if kind == "Width" else width
            label = labels[i] if len(labels) > 1 else f"{physical(lower+v*(upper-lower)):.3g} km²"
            swatches.append((kind + ": " + label, c, float(line_width)))
    if not color_area:
        legend += ["All/local links: " + color] + (["Flexible Downstream: " + flexible_color] if distinguish else [])
        swatches.insert(0, ("Local / all main links", color, float(width)))
        if distinguish:
            swatches.insert(1, ("Flexible Downstream", flexible_color, float(width)))
    return widths, colors, legend, swatches
