"""Scientific unit-catchment summaries; native assignments remain controller-owned."""

from __future__ import annotations

from collections import deque
from functools import cached_property
from html import escape

import numpy as np
import panel as pn
from netCDF4 import Dataset

from map_reader import Source, canonical_units


class UpstreamIndex:
    """Distinct reachability counts for a functional, possibly cyclic nextxy graph.

    Each supplied cell has at most one stored downstream destination. Peel leaves
    once to accumulate tree populations; remaining nodes form disjoint cycles.
    A cycle node can be reached by every node feeding any node of its cycle.
    No recursive per-click traversal, viewport filtering or area approximation.
    """

    def __init__(self, nextx, nexty, geometry):
        g = geometry
        x = np.ma.asarray(nextx).astype("i8").filled(-9999).ravel()
        y = np.ma.asarray(nexty).astype("i8").filled(-9999).ravel()
        size = g.nx * g.ny
        if len(x) != size or len(y) != size:
            raise ValueError("nextxy size disagrees with map geometry")
        valid = (x >= 1) & (x <= g.nx) & (y >= 1) & (y <= g.ny)
        self.destination = dest = np.full(size, -1, dtype=np.int64)
        dest[valid] = (y[valid] - 1) * g.nx + x[valid] - 1
        self.direct = np.bincount(dest[valid], minlength=size)
        pending = self.direct.copy()
        population = np.ones(size, dtype=np.int64)
        queue = deque(np.flatnonzero(pending == 0).tolist())
        while queue:
            node = queue.popleft()
            target = dest[node]
            if target >= 0:
                population[target] += population[node]
                pending[target] -= 1
                if pending[target] == 0:
                    queue.append(int(target))
        self.in_cycle = pending > 0
        self.total = population - 1  # Always exclude the selected node itself.
        seen = np.zeros(size, dtype=bool)
        for first in np.flatnonzero(self.in_cycle):
            if seen[first]:
                continue
            cycle = []
            node = int(first)
            while not seen[node]:
                seen[node] = True
                cycle.append(node)
                node = int(dest[node])
            self.total[cycle] = population[cycle].sum() - 1


class InspectorProducts:
    """Inspector-only registry contracts: NLFP profile and true segment IDs.

    fldhgt is height-profile thresholds in metres, NOT simulated fldfrc.
    Binary has NLFP Float32 records (x fastest); NetCDF uses layer/lat/lon.
    Neither physical layer percentages nor an alternative field are invented.
    """

    def __init__(self, reader):
        self.reader = reader
        self.messages = []
        self.profile_source = None
        self._profile_map = None
        self.subbasin_source = reader._discover("subbsn", ("subbsn",), "<i4", "1")
        if self.subbasin_source is None:
            self.subbasin_source = reader._discover("subbsn-sample", ("subbsn",), "<i4", "1")
        g = reader.geometry
        for path in (reader.path / "netcdf/fldhgt.nc", reader.path / "fldhgt.nc", reader.path / "fldhgt.bin"):
            if not path.is_file():
                continue
            try:
                if path.suffix == ".nc":
                    with Dataset(path) as ds:
                        self._profile_layout(ds)
                elif path.stat().st_size != g.nx * g.ny * g.layers * 4:
                    raise ValueError("wrong Float32 NX*NY*NLFP record size")
                self.profile_source = Source(path, path.suffix == ".nc", ("fldhgt",))
                break
            except (OSError, KeyError, ValueError) as exc:
                self.messages.append(f"fldhgt skipped {path.name}: {exc}")

    def _profile_layout(self, ds):
        axes = self.reader._nc_layout(ds)
        var = ds.variables["fldhgt"]
        spatial = [a[0] for a in axes]
        if var.ndim != 3 or set(var.dimensions) != {"layer", *spatial}:
            raise ValueError("fldhgt requires layer and the native latitude/longitude dimensions")
        if len(ds.dimensions["layer"]) != self.reader.geometry.layers:
            raise ValueError("fldhgt layer count disagrees with params.txt NLFP")
        if var.dtype.kind != "f" or var.dtype.itemsize != 4 or canonical_units(getattr(var, "units", "")) != "m":
            raise ValueError("fldhgt requires Float32 metres")
        if any(hasattr(var, key) for key in ("scale_factor", "add_offset")):
            raise ValueError("packed fldhgt is unsupported")
        if "layer" in ds.variables:
            layer = ds.variables["layer"]
            if layer.dimensions != ("layer",) or not np.array_equal(
                np.ma.asarray(layer[:]).filled(-9999), np.arange(1, self.reader.geometry.layers + 1)
            ):
                raise ValueError("layer coordinates must preserve native 1..NLFP order")
        return axes

    def profile(self, row, col):
        source = self.profile_source
        if source is None:
            return None
        if source.netcdf:
            with Dataset(source.path) as ds:
                axes = self._profile_layout(ds)
                x = self.reader.geometry.nx - 1 - col if axes[0][1] else col
                y = self.reader.geometry.ny - 1 - row if axes[1][1] else row
                var = ds.variables["fldhgt"]
                values = np.ma.asarray(
                    var[
                        tuple(
                            slice(None) if dim == "layer" else x if dim == axes[0][0] else y for dim in var.dimensions
                        )
                    ]
                )
        else:
            if self._profile_map is None:
                g = self.reader.geometry
                self._profile_map = np.memmap(source.path, mode="r", dtype="<f4", shape=(g.layers, g.ny, g.nx))
            values = self._profile_map[:, row, col]
        values = np.ma.asarray(values).astype(float)
        return np.ma.array(values, mask=np.ma.getmaskarray(values) | ~np.isfinite(values.data) | (values.data == -9999))

    @cached_property
    def subbasins(self):
        return None if self.subbasin_source is None else self.reader._load(self.subbasin_source, "subbsn", 0)


def native_label(key):
    labels = {
        "selection method": "Selection method",
        "selection status": "Selected Unit Catchment status",
        "clicked longitude": "Clicked location · Lon [°]",
        "clicked latitude": "Clicked location · Lat [°]",
        "clicked coarse ix (1-based)": "Clicked Coarse Grid ix (1-based, Fortran)",
        "clicked coarse iy (1-based)": "Clicked Coarse Grid iy (1-based, Fortran)",
        "native hires ix (1-based)": "High-resolution ix (1-based, Fortran)",
        "native hires iy (1-based)": "High-resolution iy (1-based, Fortran)",
        "assigned coarse ix (1-based)": "Native assignment catmx [stored code]",
        "assigned coarse iy (1-based)": "Native assignment catmy [stored code]",
        "ix (1-based)": "Selected river-map Grid ix (1-based, Fortran)",
        "iy (1-based)": "Selected river-map Grid iy (1-based, Fortran)",
    }
    return labels.get(key, key.replace("(1-based)", "(1-based, Fortran)"))


def number(value, factor=1):
    if value is None or np.ma.is_masked(value) or not np.isfinite(value):
        return "Unavailable"
    return f"{float(value)*factor:,.3f}".rstrip("0").rstrip(".")


def table(rows):
    return (
        '<table style="width:100%;font-size:12px">'
        + "".join(
            f'<tr><td style="padding:3px 5px;border-bottom:1px solid #ddd">{escape(str(label))}</td><td style="padding:3px 5px;border-bottom:1px solid #ddd">{escape(str(value))}</td></tr>'
            for label, value in rows
        )
        + "</table>"
    )


class CellInspector:
    """Mounted panes/accordions update contents without resetting expansion state."""

    def __init__(self, reader, products):
        self.reader = reader
        self.products = products
        self.native = InspectorProducts(reader)
        self._graphs = {}
        self.summary = pn.pane.HTML("<p>Select a Unit Catchment on the map.</p>", sizing_mode="stretch_width")
        self.method = pn.pane.Markdown("", margin=(0, 0), sizing_mode="stretch_width")
        self.geometry = pn.pane.HTML("", sizing_mode="stretch_width")
        self.connectivity = pn.pane.HTML("", sizing_mode="stretch_width")
        self.profile = pn.pane.HTML("", sizing_mode="stretch_width")
        self.profile_section = pn.Accordion(
            ("Floodplain elevation profile · fldhgt [m]", self.profile), active=[], sizing_mode="stretch_width"
        )
        self.advanced = pn.pane.HTML("<p>Native values appear after selection.</p>", sizing_mode="stretch_width")
        self.advanced_section = pn.Accordion(
            ("Advanced / Native Values", self.advanced), active=[], sizing_mode="stretch_width"
        )
        self.view = pn.Column(
            self.summary,
            self.method,
            pn.pane.Markdown("#### River and Floodplain Geometry", margin=(5, 0)),
            self.geometry,
            self.profile_section,
            pn.pane.Markdown("#### River Network Connectivity", margin=(5, 0)),
            self.connectivity,
            self.advanced_section,
            sizing_mode="stretch_width",
        )

    @cached_property
    def outlet_coordinates(self):
        # Native inspection keeps the stored longitude convention. The renderer
        # may wrap a global outlet by 360 degrees for display; that is not raw I/O.
        source = self.products.outlet_source
        if source is None:
            return None
        g = self.reader.geometry
        if source.netcdf:
            a, b = (
                self.reader._load(source, name, i).astype(float).filled(np.nan) for i, name in enumerate(source.names)
            )
        else:
            raw = np.memmap(source.path, mode="r", dtype="<f4", shape=(2, g.ny, g.nx))
            a, b = raw[0].astype(float), raw[1].astype(float)
        valid = np.isfinite(a) & np.isfinite(b) & (a >= -180) & (a <= 360) & (b >= -90) & (b <= 90)
        return np.where(valid, a, np.nan), np.where(valid, b, np.nan)

    @cached_property
    def bifurcation_counts(self):
        # Reuse renderer's first-valid directed-pair deduplication, native first
        # width and validity filters. Never count seam-split graphic segments.
        data = self.products.bifurcations
        ix, iy, jx, jy = data["indices"]
        g = self.reader.geometry
        result = {}
        for kind, mask in [("Channel", data["channel"]), ("Overland", ~data["channel"])]:
            result[kind] = (
                np.bincount((jy[mask] - 1) * g.nx + jx[mask] - 1, minlength=g.nx * g.ny),
                np.bincount((iy[mask] - 1) * g.nx + ix[mask] - 1, minlength=g.nx * g.ny),
            )
        return result

    def graph(self, network):
        if network.product not in self._graphs:
            self._graphs[network.product] = UpstreamIndex(network.nextx, network.nexty, self.reader.geometry)
        return self._graphs[network.product]

    def clear(self, message):
        self.summary.object = f"<p>{escape(message)}</p>"
        self.method.object = ""
        self.geometry.object = self.connectivity.object = "Unavailable"
        self.profile.object = "Unavailable"
        self.advanced.object = escape(message)

    def update(self, state, data, network):
        diagnostics = []
        rowcol = state.river_cell
        coords = lambda lat, lon: (
            "Unavailable"
            if lat is None or lon is None or not np.isfinite([lat, lon]).all()
            else f"Lat {lat:.5f}° · Lon {lon:.5f}°"
        )
        outlet = "Unavailable"
        profile = None
        geometry = []
        connectivity = []
        if rowcol is not None:
            row, col = rowcol
            if self.products.outlet_source is not None:
                try:
                    a, b = self.outlet_coordinates
                    outlet = coords(b[row, col], a[row, col])
                    data["source outlet longitude"] = float(a[row, col]) if np.isfinite(a[row, col]) else None
                    data["source outlet latitude"] = float(b[row, col]) if np.isfinite(b[row, col]) else None
                except (ValueError, OSError) as exc:
                    diagnostics.append(str(exc))
            for label, key, factor, unit in [
                ("Elevation", "elevtn", 1, "m"),
                ("River channel width", "rivwth", 1, "m"),
                ("River channel depth", "rivhgt", 1, "m"),
                ("River channel length", "rivlen", 0.001, "km"),
                ("Distance to downstream", "nxtdst", 0.001, "km"),
                ("Unit-catchment area", "ctmare", 1e-6, "km²"),
            ]:
                value = self.reader.read_cell(key, row, col) if key in self.reader.sources else None
                geometry.append((f"{label} · {key} [{unit}]", number(value, factor)))
            try:
                profile = self.native.profile(row, col)
                data["fldhgt [m]"] = (
                    None if profile is None else [None if np.ma.is_masked(v) else float(v) for v in profile]
                )
                if self.native.subbasins is not None:
                    sub = self.native.subbasins[row, col]
                    data["subbsn [1]"] = None if np.ma.is_masked(sub) else int(sub)
                    source = self.native.subbasin_source.path.name
                    connectivity.append(
                        (
                            f"Subbasin ID · {source}",
                            int(sub) if not np.ma.is_masked(sub) and sub > 0 else "Unavailable (unassigned)",
                        )
                    )
            except (OSError, ValueError, KeyError) as exc:
                diagnostics.append(str(exc))
            if network is not None:
                identity = network.product
                graph = self.graph(network)
                node = row * self.reader.geometry.nx + col
                data["total upstream Unit Catchments"] = int(graph.total[node])
                data["direct upstream Unit Catchments"] = int(graph.direct[node])
                x, y = int(network.nextx[row, col]), int(network.nexty[row, col])
                g = self.reader.geometry
                downstream = (
                    f"({x}, {y})"
                    if 1 <= x <= g.nx and 1 <= y <= g.ny
                    else f'{network.inspect(row,col)["downstream status"]} · stored ({x}, {y})'
                )
                connectivity[:0] = [
                    ("Downstream Unit Catchment ID (ix, iy)", downstream),
                    ("Total upstream Unit Catchments", f"{graph.total[node]:,}"),
                    ("Direct upstream Unit Catchments", f"{graph.direct[node]:,}"),
                ]
                diagnostics.append(
                    f"Connectivity product: {identity}; self-links retained in graph in-degree; total excludes selected node."
                )
                if graph.in_cycle[node]:
                    diagnostics.append(
                        "Selected node belongs to a stored cycle; counts include distinct reachable cycle/tree nodes only."
                    )
            else:
                connectivity[:0] = [
                    (label, "Unavailable (no stored nextxy product)")
                    for label in (
                        "Downstream Unit Catchment ID (ix, iy)",
                        "Total upstream Unit Catchments",
                        "Direct upstream Unit Catchments",
                    )
                ]
            bif = []
            for kind in ("Channel", "Overland"):
                try:
                    incoming, outgoing = self.bifurcation_counts[kind]
                    node = row * self.reader.geometry.nx + col
                    value = f"Incoming {incoming[node]:,} · Outgoing {outgoing[node]:,}"
                except (OSError, ValueError, KeyError) as exc:
                    value = "Unavailable"
                    if str(exc) not in diagnostics:
                        diagnostics.append(str(exc))
                bif.append((kind + " bifurcation connections", value))
            connectivity[3:3] = bif
            basin = data.get("basin [1]")
            connectivity.insert(5, ("Basin ID · basin", "Unavailable" if basin is None else str(basin)))
        clicked = coords(state.clicked[1], state.clicked[0]) if state.clicked is not None else "Unavailable"
        identity = f"({rowcol[1]+1}, {rowcol[0]+1})" if rowcol is not None else "Unavailable"
        fields = [
            ("Outlet coordinates", outlet),
            ("Upstream Area [km²]", number(data.get("uparea [m2]"), 1e-6)),
            ("Unit Catchment ID (ix, iy)", identity),
            ("Clicked Location", clicked),
        ]
        self.summary.object = (
            '<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;font-size:12px">'
            + "".join(
                f'<div style="padding:6px;background:#f0f2f7;border-radius:4px;overflow-wrap:anywhere"><div>{escape(label)}</div><strong>{escape(value)}</strong></div>'
                for label, value in fields
            )
            + "</div><small>Unit Catchment ID: 1-based Fortran river-map indices; not a rectangular catchment boundary.</small>"
        )
        method = (
            "High-resolution catmxy assignment"
            if state.method == "High-resolution catmxy assignment"
            else "Geographic coarse-grid containment"
        )
        self.method.object = "Selection: " + method + (" · " + state.status if rowcol is None else "")
        self.geometry.object = table(geometry) if geometry else "Unavailable — no selected Unit Catchment"
        self.profile.object = (
            "Unavailable — no readable fldhgt profile."
            if profile is None
            else table(("Layer " + str(i + 1), number(value)) for i, value in enumerate(profile))
            + "<small>Native layer index; fldhgt height thresholds [m], not fldfrc. No area percentages inferred.</small>"
        )
        note = "Counts cover only the supplied regional network; upstream connectivity outside it may be unknown. Bifurcations: distinct stored incoming/outgoing directed paths (positive first-layer width = Channel; zero = Overland)."
        if self.native.subbasin_source is None:
            note += " Subbasin ID unavailable: no true subbsn product; subcol is a display-color category."
        elif "sample" in self.native.subbasin_source.path.stem:
            note += " Subbasin IDs are sample segmentation identifiers, not universal basin identifiers."
        self.connectivity.object = (
            table(connectivity) if connectivity else "Unavailable — no selected Unit Catchment"
        ) + f'<p style="font-size:11px">{escape(note)}</p>'
        rows = []
        for key, value in data.items():
            if isinstance(value, list):
                value = ", ".join("Unavailable" if v is None else str(v) for v in value)
            rows.append((native_label(key), "Unavailable" if value is None else value))
        self.advanced.object = table(rows) + "".join(
            "<p>" + escape(message) + "</p>" for message in diagnostics + self.native.messages + self.reader.messages
        )
