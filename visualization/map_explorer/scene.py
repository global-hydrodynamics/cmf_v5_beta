"""Composable scientific scene shared by Bokeh and Matplotlib export."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from hires import assignment, catchment_edges, discover_tiles
from map_layers import DisplayLayer, colorize, layer_colors, make_layer, raster_subset
from map_products import Products, area_style, split_segments
from background_style import PALE_TERRAIN, apply_opacity, highres_layer, neutral_floodplain_color
from river_network import intersects
from map_reader import SCHEMA

OVERLAY_DEFAULTS = dict(
    channel=False,
    overland=False,
    outlets=False,
    headwater=False,
    coarse_grid=False,
    catchment_boundaries=False,
    channel_pixels=False,
    channel_color="#b2182b",
    overland_color="#999999",
    bif_width=1.5,
    bif_classes=True,
)


@dataclass
class Frame:
    images: list = field(default_factory=list)
    main: dict = field(default_factory=lambda: dict(x0=[], y0=[], x1=[], y1=[], width=[], color=[]))
    overlays: list = field(default_factory=list)
    points: np.ndarray = field(default_factory=lambda: np.empty((0, 2)))
    arrows: dict = field(default_factory=lambda: dict(x=[], y=[], angle=[], color=[], size=[]))
    layer: object = None
    legend: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)
    swatches: list = field(default_factory=list)


def visible_segments(segments, extent):
    return intersects(segments[:, 0, 0], segments[:, 0, 1], segments[:, 1, 0], segments[:, 1, 1], extent)


class Scene:
    def __init__(self, reader):
        self.reader = reader
        self.products = Products(reader)
        self.messages = list(self.products.messages)
        self.tiles = discover_tiles(reader.path, self.messages)

    def build(self, extent, name, coarse_layer, network, options, max_side=1200):
        frame = Frame()
        background = options.get("background", "coarse")
        overlays = {**OVERLAY_DEFAULTS, **options.get("overlays", {})}
        selected_tile = options.get("tile")
        tile = self.tiles.get(selected_tile)
        if background == "coarse":
            image, edges = raster_subset(coarse_layer, self.reader.geometry, extent, max_side)
            frame.images.append((colorize(coarse_layer, image), edges))
            frame.layer = coarse_layer
        elif background != "none":
            if tile is None:
                raise ValueError("Select an available high-resolution source")
            self._background(
                frame,
                tile,
                background,
                name,
                coarse_layer,
                extent,
                overlays,
                options.get("terrain_palette", "gray"),
                max_side,
                options.get("highres_style"),
            )
        if frame.images:
            rgba, edges = frame.images[0]
            frame.images[0] = (apply_opacity(rgba, options.get("background_opacity", 1.0)), edges)
        if overlays["catchment_boundaries"]:
            self._catchment_boundaries(frame, tile, extent, max_side)
        if network is not None:
            visible = network.visible(extent)
            widths, colors, legend, frame.swatches = area_style(
                network, self.reader, visible, **options.get("network_style", {})
            )
            order = np.argsort(widths, kind="stable")
            ids = visible[order]
            widths = widths[order]
            colors = colors[order]
            frame.main = dict(
                x0=network.x0[ids],
                y0=network.y0[ids],
                x1=network.x1[ids],
                y1=network.y1[ids],
                width=widths,
                color=colors,
            )
            frame.legend += legend
            arrow_size = options.get("arrow_size", 7 if options.get("arrows") else 0)
            if arrow_size:
                if len(ids) <= 600:
                    dx = network.x1[ids] - network.x0[ids]
                    dy = network.y1[ids] - network.y0[ids]
                    cosine = max(0.05, np.cos(np.deg2rad((extent[2] + extent[3]) / 2)))
                    frame.arrows = dict(
                        x=network.x0[ids] + 0.68 * dx,
                        y=network.y0[ids] + 0.68 * dy,
                        angle=np.arctan2(dy, dx * cosine) - np.pi / 2,
                        color=colors,
                        size=np.full(len(ids), arrow_size),
                    )
                else:
                    frame.diagnostics.append("Direction heads omitted above 600 visible links; zoom in")
        if background == "none":
            frame.legend.append("No background")
        if overlays["coarse_grid"]:
            self._grid(frame, extent)
        if overlays["channel"] or overlays["overland"]:
            self._bifurcations(frame, extent, overlays)
        if overlays["outlets"] or overlays["headwater"]:
            try:
                a, b = self.products.outlets
                g = self.reader.geometry
                if overlays["outlets"]:
                    valid = (
                        np.isfinite(a)
                        & np.isfinite(b)
                        & (a >= extent[0])
                        & (a <= extent[1])
                        & (b >= extent[2])
                        & (b <= extent[3])
                    )
                    points = np.unique(np.column_stack([a[valid], b[valid]]), axis=0)
                    if len(points) <= 20000:
                        frame.points = points
                        frame.legend.append("Stored outlets: hollow circles")
                    else:
                        frame.diagnostics.append("Outlet markers omitted above 20,000 visible nodes")
                if overlays["headwater"]:
                    if g.periodic:
                        raise ValueError("Periodic global headwater centroid guides are not yet supported")
                    if tile is None or "catmxy" not in tile.files or network is None:
                        frame.diagnostics.append("Headwater guides need selected catmxy tile and a main network")
                    else:
                        river = self.reader.read("uparea").astype(float).filled(np.nan) > 0
                        lon, lat, counts = tile.centroids(g, river)
                        incoming = np.bincount(network.dest_rows * g.nx + network.dest_cols, minlength=g.nx * g.ny)
                        ids = np.flatnonzero(
                            river.ravel()
                            & (incoming == 0)
                            & (counts > 0)
                            & np.isfinite(a.ravel())
                            & np.isfinite(b.ravel())
                        )
                        segments = np.stack(
                            [np.column_stack([lon[ids], lat[ids]]), np.column_stack([a.ravel()[ids], b.ravel()[ids]])],
                            axis=1,
                        )
                        segments = segments[visible_segments(segments, extent)]
                        frame.overlays.insert(
                            0,
                            (
                                segments,
                                "#888888",
                                0.65,
                                "Regional no-incoming centroid guides (not confirmed headwaters)",
                            ),
                        )
            except (ValueError, OSError, KeyError) as exc:
                frame.diagnostics.append(f"Outlet/guide overlay unavailable: {exc}")
        return frame

    def _background(
        self, frame, tile, mode, name, coarse_layer, extent, overlays, terrain_palette, max_side, style=None
    ):
        subset = tile.subset(extent, max_side)
        if subset is None:
            frame.diagnostics.append("View lies outside selected high-resolution tile")
            return
        rows, cols, edges, native = subset
        x = y = valid = land = None
        if mode == "catchment" and "catmxy" not in tile.files:
            raise ValueError(f"{tile.key}: no catmxy assignment product")
        if "catmxy" in tile.files and (mode == "catchment" or overlays["channel_pixels"]):
            x, y = tile.sample("catmxy", rows, cols)
            valid, land, invalid = assignment(x, y, self.reader.geometry)
            if np.any(invalid):
                frame.diagnostics.append(f"{int(invalid.sum())} displayed assignment pairs invalid; excluded")
            rr, cc = np.where(valid)
            if "uparea" in self.reader.sources:
                river = self.reader.read("uparea").astype(float).filled(np.nan) > 0
                nonriver = ~river[y[rr, cc] - 1, x[rr, cc] - 1]
                if np.any(nonriver):
                    frame.diagnostics.append(
                        f"{int(nonriver.sum())} displayed assignments target cells without positive uparea; excluded"
                    )
                valid[rr, cc] &= river[y[rr, cc] - 1, x[rr, cc] - 1]
        if mode == "catchment":
            image = np.full(valid.shape, np.nan)
            rr, cc = np.where(valid)
            if SCHEMA[name].categorical:
                source = coarse_layer.image
            else:
                # Retain native finite values for custom Linear; Log masking is
                # a separate display operation, never a source-data edit.
                source = self.reader.read(name).astype(float).filled(np.nan) * SCHEMA[name].factor
            image[rr, cc] = source[y[rr, cc] - 1, x[rr, cc] - 1]
            if SCHEMA[name].categorical:
                layer = DisplayLayer(
                    image,
                    coarse_layer.palette,
                    coarse_layer.low,
                    coarse_layer.high,
                    False,
                    coarse_layer.categories,
                    coarse_layer.label + " inherited by assigned unit catchment",
                )
            else:
                layer = highres_layer(image, self.reader, tile, mode, name, coarse_layer, style, terrain_palette)
            image = layer.image
            rgba = colorize(layer, image)
            rgba[~np.isfinite(image)] = np.uint32(0xFFFFFFFF)
            rgba[land] = np.array([217, 217, 217, 255], dtype="u1").view("<u4")[0]
            frame.legend.append("Unassigned land catmxy=-999: gray; other missing: white")
            frame.legend.append(
                f"{name}: coarse-cell attribute inherited across catchment, not a local pixel measurement"
            )
        else:
            if mode not in ("elevtn", "difference", "flddif"):
                raise ValueError("Unknown high-resolution background")
            image = tile.sample(mode, rows, cols)
            raw_image = image
            layer = highres_layer(image, self.reader, tile, mode, name, coarse_layer, style, terrain_palette)
            image = layer.image
            rgba = colorize(layer, image)
            rgba[~np.isfinite(image)] = np.uint32(0xFFFFFFFF)
            if mode == "flddif":
                elevation = tile.sample("elevtn", rows, cols)
                fill = ~np.isfinite(raw_image) & np.isfinite(elevation)
                rgba[fill] = neutral_floodplain_color(style, terrain_palette)
                frame.legend.append("Missing flddif + valid elevation: neutral fill; both missing: blank")
            reference = "manual limits" if (style or {}).get("limits") is not None else "full-tile P2/P98 reference"
            frame.legend.append(
                f"{tile.key} {reference}: {layer.low:.4g}/{layer.high:.4g} m; "
                + (style or {}).get("scale", "gallery")
                + " display normalization"
            )
        if layer.logarithmic:
            frame.diagnostics.append("Log display masks nonpositive values; native values remain unchanged")
        frame.layer = layer
        frame.images.append((rgba, edges))
        if overlays["channel_pixels"]:
            if "visual" in tile.files:
                visual = tile.sample("visual", rows, cols)
                channel = np.zeros(rgba.shape, dtype="<u4")
                mask = valid if valid is not None else np.ones(rgba.shape, dtype=bool)
                for code, color in [(10, [131, 198, 237, 255]), (7, [199, 166, 221, 255])]:
                    channel[mask & (visual == code)] = np.asarray(color, dtype="u1").view("<u4")[0]
                # A separate image keeps channel opacity independent of raster alpha.
                frame.images.append((channel, edges))
                frame.legend.append("FLOW pixels: blue=main channel (10), lavender=small stream (7)")
                if valid is None:
                    frame.diagnostics.append("Visual codes shown without catmxy; no assignment inferred")
            else:
                frame.diagnostics.append("Selected tile has no signed Int8 visual product")

    def _catchment_boundaries(self, frame, tile, extent, max_side):
        """Assignment-pair overlay independent of the chosen background/variable."""
        if tile is None or "catmxy" not in tile.files:
            frame.diagnostics.append("Unit Catchment Boundaries need catmxy in the selected tile")
            return
        subset = tile.subset(extent, max_side)
        if subset is None:
            frame.diagnostics.append("Unit Catchment Boundaries: outside selected tile")
            return
        rows, cols, edges, native = subset
        if not native:
            frame.diagnostics.append("Catchment outlines omitted in sampled view; zoom in to native detail")
            return
        x, y = tile.sample("catmxy", rows, cols)
        valid, _, _ = assignment(x, y, self.reader.geometry)
        segments = catchment_edges(x, y, valid, edges)
        if len(segments) <= 100000:
            frame.overlays.insert(0, (segments, "#646464", 0.35, "Native unit-catchment assignment boundaries"))
        else:
            frame.diagnostics.append("Catchment outlines omitted above 100,000 native edges; zoom in")

    def _grid(self, frame, extent):
        g = self.reader.geometry
        xs = (
            g.west
            + np.arange(
                max(0, int((extent[0] - g.west) / g.resolution)),
                min(g.nx, int(np.ceil((extent[1] - g.west) / g.resolution))) + 1,
            )
            * g.resolution
        )
        ys = (
            g.south
            + np.arange(
                max(0, int((extent[2] - g.south) / g.resolution)),
                min(g.ny, int(np.ceil((extent[3] - g.south) / g.resolution))) + 1,
            )
            * g.resolution
        )
        if len(xs) + len(ys) > 500:
            frame.diagnostics.append("Coarse grid omitted above 500 lines; zoom in")
            return
        segments = np.asarray(
            [[[x, extent[2]], [x, extent[3]]] for x in xs] + [[[extent[0], y], [extent[1], y]] for y in ys], dtype=float
        )
        frame.overlays.insert(0, (segments, "#b0b0b0", 0.4, "Coarse-grid boundaries"))

    def _bifurcations(self, frame, extent, options):
        try:
            data = self.products.bifurcations
            for channel, label, color in [
                (True, "Channel bifurcations", options["channel_color"]),
                (False, "Overland bifurcations", options["overland_color"]),
            ]:
                if not options["channel" if channel else "overland"]:
                    continue
                mask = data["channel"] == channel
                original = np.flatnonzero(mask)
                s = data["segments"][mask]
                x0, y0, x1, y1, ids = split_segments(
                    self.reader.geometry, s[:, 0, 0], s[:, 0, 1], s[:, 1, 0], s[:, 1, 1], original
                )
                visible = intersects(x0, y0, x1, y1, extent)
                s = np.stack(
                    [np.column_stack([x0[visible], y0[visible]]), np.column_stack([x1[visible], y1[visible]])], axis=1
                )
                widths = np.full(visible.sum(), float(options["bif_width"]))
                if channel and options["bif_classes"] and mask.any():
                    cuts = np.quantile(np.log10(data["first_width"][mask]), (0.25, 0.5, 0.75))
                    classes = np.digitize(np.log10(data["first_width"][ids[visible]]), cuts)
                    widths *= 1 + classes / 2
                order = np.argsort(widths, kind="stable")
                frame.overlays.append((s[order], color, widths[order], label + f" ({int(mask.sum())} unique total)"))
            frame.diagnostics.append("Bifurcations: " + str(data["stats"]))
        except (ValueError, OSError, KeyError) as exc:
            frame.diagnostics.append(f"Bifurcations unavailable: {exc}")

    def inspect(self, lon, lat, tile_key):
        tile = self.tiles.get(tile_key)
        if tile is None:
            return {}, None
        cell = tile.geometry.cell(lon, lat)
        if cell is None:
            return {"high-resolution source": tile.key, "assignment status": "outside selected tile"}, None
        row, col = cell
        result = {
            "high-resolution source": tile.key,
            "native hires ix (1-based)": col + 1,
            "native hires iy (1-based)": row + 1,
        }
        assigned = None
        if "catmxy" in tile.files:
            x, y = tile.sample("catmxy", np.array([row]), np.array([col]))[:, 0, 0]
            valid, land, invalid = assignment(np.asarray(x), np.asarray(y), self.reader.geometry)
            result.update(
                {
                    "assigned coarse ix (1-based)": int(x),
                    "assigned coarse iy (1-based)": int(y),
                    "assignment status": (
                        "assigned"
                        if valid
                        else "unassigned land" if land else "invalid pair" if invalid else "other background"
                    ),
                }
            )
            if valid:
                assigned = int(y) - 1, int(x) - 1
                g = self.reader.geometry
                result.update(
                    {"assigned " + k: v for k, v in self.reader.inspect(g.lon[int(x) - 1], g.lat[int(y) - 1]).items()}
                )
        for name in ("elevtn", "flddif", "visual"):
            if name in tile.files:
                value = tile.sample(name, np.array([row]), np.array([col]))[0, 0]
                result[f"native hires {name}" + (" [m]" if name != "visual" else " [stored code]")] = (
                    float(value) if np.isfinite(value) else None
                )
        if "elevtn" in tile.files:
            value = tile.sample("difference", np.array([row]), np.array([col]))[0, 0]
            result["derived max 8-neighbor elevation difference [m], NOT slope"] = (
                float(value) if np.isfinite(value) else None
            )
        return result, assigned


def export_scene(
    reader,
    frame,
    extent,
    path,
    selected_point=None,
    selected_segments=None,
    selected_boundary=None,
    selected_coarse_outline=None,
):
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.collections import LineCollection
    from matplotlib.cm import ScalarMappable
    from matplotlib.lines import Line2D

    g = reader.geometry
    w, e, s, n = extent
    ratio = (e - w) * max(0.05, np.cos(np.deg2rad((s + n) / 2))) / (n - s)
    figure = Figure(figsize=(float(np.clip(8 * ratio, 6, 15)), 9), layout="constrained")
    FigureCanvasAgg(figure)
    ax = figure.add_subplot()
    ax.set_facecolor("#f5f7fa")
    for rgba, edges in frame.images:
        image = np.ascontiguousarray(rgba).view("u1").reshape((*rgba.shape, 4))
        ax.imshow(image, extent=edges, origin="upper", interpolation="nearest")
    if frame.layer is not None:
        cmap, norm = layer_colors(frame.layer)
        bar = figure.colorbar(ScalarMappable(norm=norm, cmap=cmap), ax=ax, shrink=0.8)
        bar.set_label(frame.layer.label)
        if len(frame.layer.categories):
            ticks = np.unique(
                np.linspace(0, len(frame.layer.categories) - 1, min(16, len(frame.layer.categories))).astype(int)
            )
            bar.set_ticks(ticks, labels=[str(int(frame.layer.categories[i])) for i in ticks])
    m = frame.main
    segments = np.stack([np.column_stack([m["x0"], m["y0"]]), np.column_stack([m["x1"], m["y1"]])], axis=1)
    ax.add_collection(LineCollection(segments, colors=m["color"], linewidths=np.asarray(m["width"]) * 0.75, zorder=3))
    for segments, color, width, label in frame.overlays:
        ax.add_collection(LineCollection(segments, colors=color, linewidths=np.asarray(width) * 0.75, zorder=4))
        ax.plot([], [], color=color, lw=1, label=label)
    if len(frame.points):
        ax.scatter(*frame.points.T, s=9, facecolors="white", edgecolors="#555555", linewidths=0.4, zorder=6)
    if len(frame.arrows["x"]):
        # Same directed point/angle as browser. Matplotlib marker rotation uses
        # display angles, so arrows are explicit rotated triangles.
        for x, y, angle, color, size in zip(
            frame.arrows["x"], frame.arrows["y"], frame.arrows["angle"], frame.arrows["color"], frame.arrows["size"]
        ):
            # scatter area is points²; convert browser-pixel diameter at export160dpi.
            ax.scatter(
                [x], [y], marker=(3, 0, np.degrees(angle)), s=(size * 72 / 160) ** 2, linewidths=0, c=[color], zorder=5
            )
    if selected_point is not None:
        ax.plot(*selected_point, "o", mfc="none", mec="#e11d48", ms=9, mew=2, zorder=8)
    if selected_segments is not None and len(selected_segments):
        ax.add_collection(LineCollection(selected_segments, colors="#e11d48", linewidths=2.2, zorder=8))
    if selected_coarse_outline is not None:
        ax.add_collection(
            LineCollection(selected_coarse_outline, colors="#607d8b", linewidths=0.8, linestyles="dashed", zorder=9)
        )
    if selected_boundary is not None:
        # Same native exposed edges as the dedicated browser selection glyph.
        # Matplotlib clips at axes limits; the viewport never delineates it.
        ax.add_collection(LineCollection(selected_boundary.segments, colors="#ff00a8", linewidths=2.1, zorder=10))
    ax.set(
        xlim=(w, e),
        ylim=(s, n),
        xlabel="Longitude [°]",
        ylabel="Latitude [°]",
        title=f"CaMa-Flood · {reader.path.name}",
    )
    ax.set_aspect(1 / max(0.05, np.cos(np.deg2rad((s + n) / 2))))
    handles = [Line2D([], [], color=color, lw=width, label=label) for label, color, width in frame.swatches]
    handles += [Line2D([], [], color=color, lw=1, label=label) for segments, color, width, label in frame.overlays]
    if len(frame.points):
        handles.append(Line2D([], [], marker="o", mfc="white", mec="#555555", ls="none", label="Stored outlets"))
    if selected_coarse_outline is not None:
        handles.append(
            Line2D([], [], color="#607d8b", lw=0.8, ls="--", label="Selected computational coarse grid cell")
        )
    if selected_boundary is not None:
        handles.append(
            Line2D(
                [],
                [],
                color="#ff00a8",
                lw=2,
                label=f"Selected stored unit catchment ({selected_boundary.pixel_count:,} pixels)",
            )
        )
    if handles:
        ax.legend(handles=handles, loc="lower left", fontsize=6)
    figure.supxlabel("\n".join(frame.legend), fontsize=7)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=160)
    return path
