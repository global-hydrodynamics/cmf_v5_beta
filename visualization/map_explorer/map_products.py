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
        for path in (reader.path / "netcdf/lonlat.nc", reader.path / "lonlat.nc", reader.path / "lonlat.bin"):
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
            (p for p in [reader.path / "netcdf/bifprm.nc", reader.path / "bifprm.nc"] if p.is_file()), None
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
            # Endpoint validity can change the reference population for full-
            # network classes. Do not inherit the grid-center summary cache.
            view.__dict__.pop("_area_summary", None)
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
            var = ds.variables["width"]
            if var.dimensions != ("layer", "path") or getattr(var, "units", "") != "m" or not var.shape[0]:
                raise ValueError("bifprm:width requires (layer,path), units m")
            widths = np.ma.asarray(var[:]).astype(float).filled(np.nan)
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
):
    """Full-network classes are independent of viewport, using source uparea."""
    from matplotlib import colormaps
    from matplotlib.colors import to_hex

    if not hasattr(network, "_areas"):
        raw = (
            reader.read("uparea")[network.rows, network.cols].astype(float).filled(np.nan) * 1e-6
            if "uparea" in reader.sources
            else np.full(len(network.rows), np.nan)
        )
        network._areas = raw
    raw = network._areas
    good = np.isfinite(raw) & (raw > 0)
    if classification not in ("quartiles", "six_log", "continuous", "fixed"):
        raise ValueError("Unknown area classification")
    # Vector normalization uses links with valid endpoints, as in Gallery f03.
    if not hasattr(network, "_area_summary"):
        present = np.unique(network.link_index)
        full = raw[present][good[present]]
        logs = np.log10(full) if len(full) else np.array([0.0, 1.0])
        network._area_summary = (len(full), float(logs.min()), float(logs.max()), np.quantile(logs, (0.25, 0.5, 0.75)))
    count, lo, hi, cuts = network._area_summary
    if (scale_width or color_area) and not count:
        raise ValueError("No positive source-cell upstream areas for network style")
    ids = network.link_index[visible]
    a = raw[ids]
    fraction = np.zeros(len(ids))
    usable = np.isfinite(a) & (a > 0)
    fraction[usable] = np.clip((np.log10(a[usable]) - lo) / max(hi - lo, 1e-12), 0, 1)
    labels = []
    if classification == "quartiles":
        level = np.zeros(len(ids), dtype=int)
        level[usable] = np.digitize(np.log10(a[usable]), cuts)
        positions = level / 3
        palette = np.array(AREA_COLORS, dtype=object)
        colors = palette[level]
        edges = np.r_[lo, cuts, hi]
        labels = [f"Q{i+1}: {10**edges[i]:.3g}–{10**edges[i+1]:.3g} km²" for i in range(4)]
    elif classification == "six_log":
        level = np.minimum((fraction * 6).astype(int), 5)
        positions = level / 5
        colors = np.array([to_hex(colormaps["viridis"](v)) for v in positions])
        edges = np.linspace(lo, hi, 7)
        labels = [f"L{i+1}: {10**edges[i]:.3g}–{10**edges[i+1]:.3g} km²" for i in range(6)]
    else:
        positions = fraction
        if classification == "fixed":
            positions = np.zeros(len(ids))
            positions[usable] = np.clip(np.log10(a[usable]) / 6, 0, 1)
            lo, hi = 0.0, 6.0
        colors = np.array([to_hex(colormaps["viridis"](v)) for v in positions])
        labels = [f"{classification}: log {10**lo:.3g}–{10**hi:.3g} km²"]
    widths = np.full(len(ids), float(width))
    if scale_width:
        widths *= (0.5 + 3 * positions) if classification == "fixed" else (1 + 2 * positions)
    if not color_area:
        colors = np.full(len(ids), color, dtype=object)
        if distinguish:
            colors[network.flexible[ids]] = flexible_color
    legend = (
        (["Upstream contributing area (not discharge); " + classification] + labels)
        if scale_width or color_area
        else ["Local/all links: " + color] + (["Flexible Downstream: " + flexible_color] if distinguish else [])
    )
    swatches = []
    if scale_width or color_area:
        count = 4 if classification == "quartiles" else 6 if classification == "six_log" else 5
        for i, v in enumerate(np.linspace(0, 1, count)):
            c = AREA_COLORS[i] if classification == "quartiles" else to_hex(colormaps["viridis"](v))
            label = labels[i] if len(labels) > 1 else f"{10**(lo+v*(hi-lo)):.3g} km²"
            swatches.append(
                (
                    label,
                    c if color_area else color,
                    (
                        float(width) * (1 + 2 * v if classification != "fixed" else 0.5 + 3 * v)
                        if scale_width
                        else float(width)
                    ),
                )
            )
    else:
        swatches = [("Local / all main links", color, float(width))]
        if distinguish:
            swatches.append(("Flexible Downstream", flexible_color, float(width)))
    return widths, colors, legend, swatches
