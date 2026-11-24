#!/usr/bin/env python3
"""Map Rhine gauges and reported flood-impact locations against the current model grid."""

from __future__ import annotations

import argparse
import csv
import importlib.util
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
import numpy as np
from netCDF4 import Dataset


def load_helper(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load existing river-network helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def read_allocations(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 3:
        raise ValueError(f"{path}: expected three gauge allocation rows, found {len(rows)}")
    return rows


def read_impact_allocations(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def read_map(map_dir: Path):
    netcdf = map_dir / "netcdf"
    with Dataset(netcdf / "lonlat.nc") as data:
        lon = np.asarray(data.variables["lon"][:], dtype=np.float64)
        lat = np.asarray(data.variables["lat"][:], dtype=np.float64)
        outlon = np.ma.asarray(data.variables["outlon"][:], dtype=np.float64).filled(np.nan)
        outlat = np.ma.asarray(data.variables["outlat"][:], dtype=np.float64).filled(np.nan)
    with Dataset(netcdf / "uparea.nc") as data:
        uparea = np.ma.asarray(data.variables["uparea"][:], dtype=np.float64).filled(np.nan)
    with Dataset(netcdf / "nextxy.nc") as data:
        nextx = np.ma.asarray(data.variables["nextx"][:]).filled(-9999).astype(np.int32)
        nexty = np.ma.asarray(data.variables["nexty"][:]).filled(-9999).astype(np.int32)
    return lon, lat, uparea, nextx, nexty, outlon, outlat


def build_river_segments(map_dir: Path, map_data):
    root = map_dir.parents[1]
    helper_path = root / "visualization/output_analysis/script/f02-discharge_vector.py"
    vector = load_helper(helper_path, "tutorial11_gauge_vector_helper")
    lon, lat, uparea, nextx, nexty, outlon, outlat = map_data
    links = vector.NETWORK.downstream_links(lon, lat, uparea, nextx, nexty)
    _, _, sr, sc, dr, dc, _, _, invalid = links
    valid = (
        np.isfinite(outlon[sr, sc]) & np.isfinite(outlat[sr, sc]) &
        np.isfinite(outlon[dr, dc]) & np.isfinite(outlat[dr, dc]) &
        (outlon[sr, sc] != -9999) & (outlat[sr, sc] != -9999) &
        (outlon[dr, dc] != -9999) & (outlat[dr, dc] != -9999)
    )
    segments = np.stack((
        np.column_stack((outlon[sr[valid], sc[valid]], outlat[sr[valid], sc[valid]])),
        np.column_stack((outlon[dr[valid], dc[valid]], outlat[dr[valid], dc[valid]])),
    ), axis=1)
    area = uparea[sr[valid], sc[valid]] / 1_000_000.0
    return segments, area, invalid


def draw_network(ax, segments: np.ndarray, area: np.ndarray, extent=None) -> None:
    visible = np.ones(len(segments), dtype=bool)
    if extent is not None:
        west, east, south, north = extent
        visible = (
            (segments[:, :, 0].max(axis=1) >= west) &
            (segments[:, :, 0].min(axis=1) <= east) &
            (segments[:, :, 1].max(axis=1) >= south) &
            (segments[:, :, 1].min(axis=1) <= north)
        )
    selected_segments, selected_area = segments[visible], area[visible]
    classes = np.digitize(np.log10(np.maximum(selected_area, 1)), [2, 3.5, 4.7])
    widths = np.asarray([0.35, 0.48, 0.68, 0.92])[classes]
    ax.add_collection(LineCollection(
        selected_segments, colors="#4c7694", linewidths=widths,
        alpha=0.78, capstyle="round", zorder=2,
    ))


def add_stations(ax, records: list[dict[str, str]], labels: bool = True) -> None:
    for row in records:
        observed = (float(row["observed_lon_deg"]), float(row["observed_lat_deg"]))
        outlet = (float(row["model_outlet_lon_deg"]), float(row["model_outlet_lat_deg"]))
        ax.plot([observed[0], outlet[0]], [observed[1], outlet[1]],
                color="#626262", linewidth=0.8, linestyle=(0, (2, 2)), zorder=4)
        ax.scatter(*observed, s=46, marker="o", facecolor="#f28e2b",
                   edgecolor="white", linewidth=0.8, zorder=6)
        ax.scatter(*outlet, s=45, marker="s", facecolor="#2676b8",
                   edgecolor="white", linewidth=0.8, zorder=7)
        if labels:
            name = row["station_name"]
            gauge_offset, gauge_ha = ((-8, -16), "right") if name == "Maxau" else ((7, 9), "left")
            outlet_offset = (8, 13) if name == "Maxau" else (7, -16)
            ax.annotate("gauge", observed, xytext=gauge_offset,
                        textcoords="offset points", fontsize=7.2, ha=gauge_ha,
                        bbox=dict(facecolor="white", alpha=0.86, edgecolor="none", pad=1.2), zorder=8)
            ax.annotate("outlet", outlet, xytext=outlet_offset,
                        textcoords="offset points", fontsize=6.8, color="#17527c", ha="left",
                        bbox=dict(facecolor="white", alpha=0.86, edgecolor="none", pad=1.0), zorder=8)


RIVER_COLORS = {
    "Ahr": "#d62728",
    "Erft/Swist": "#9467bd",
    "Kyll": "#ff7f0e",
    "Prüm": "#8c564b",
    "Vesdre/Meuse": "#1f77b4",
    "Meuse": "#17a2a4",
    "Meuse basin / Geul": "#00a6a6",
    "Gete": "#2ca02c",
    "Dyle": "#bcbd22",
}


def add_impact_allocations(ax, records: list[dict[str, str]], label_impacts: bool = False,
                           label_details: bool = False) -> None:
    """Show source locations, assigned model outlets and their separation."""
    # Repeated reports can refer to one town or one grid cell. Draw each
    # coordinate-to-outlet connector only once to avoid artificial emphasis.
    connectors = set()
    river_candidates = set()
    for row in records:
        if row["allocation_status"] != "assigned_to_containing_grid_cell":
            continue
        observed = (float(row["observed_lon"]), float(row["observed_lat"]))
        outlet = (float(row["model_outlet_lon"]), float(row["model_outlet_lat"]))
        key = tuple(round(v, 6) for v in (*observed, *outlet))
        if key not in connectors:
            ax.plot([observed[0], outlet[0]], [observed[1], outlet[1]],
                    color="#3d3d3d", linewidth=0.55, linestyle=(0, (1.5, 2)),
                    alpha=0.42, zorder=3)
            connectors.add(key)
        if (row.get("river_allocation_status") in {"confirmed", "plausible"}
                and row.get("river_model_outlet_lon") and row.get("river_model_outlet_lat")):
            candidate = (float(row["river_model_outlet_lon"]),
                         float(row["river_model_outlet_lat"]))
            candidate_key = tuple(round(value, 6) for value in candidate)
            if candidate_key not in river_candidates:
                ax.scatter(*candidate, s=58, marker="D", facecolor="#df3f93",
                           edgecolor="white", linewidth=0.75, zorder=10)
                river_candidates.add(candidate_key)

    for row in records:
        if not row["observed_lon"] or not row["observed_lat"]:
            continue
        observed = (float(row["observed_lon"]), float(row["observed_lat"]))
        color = RIVER_COLORS.get(row["river_group"], "#555555")
        is_impact = row["report_id"].startswith("impact-")
        marker = "o" if is_impact else "^"
        size = 36 if is_impact else 44
        ax.scatter(*observed, s=size, marker=marker, facecolor=color,
                   edgecolor="white", linewidth=0.65, zorder=7)
        if row["allocation_status"] == "assigned_to_containing_grid_cell":
            outlet = (float(row["model_outlet_lon"]), float(row["model_outlet_lat"]))
            ax.scatter(*outlet, s=27, marker="s", facecolor="#152c3d",
                       edgecolor="white", linewidth=0.5, zorder=8)
        impact_offsets = {
            "ahr-schuld": (-38, -7), "ahr-altenahr": (-45, 17),
            "ahr-bad-neuenahr": (10, -20), "ahr-sinzig": (17, 8),
            "erft-bad-muenstereifel": (-52, -15), "erft-euskirchen": (-40, 9),
            "erft-blessem": (8, 14), "kyll-kordel": (-35, 8),
            "pruem-pruemzurlay": (10, 14), "vesdre-verviers": (-43, 11),
            "vesdre-pepinster": (12, -17), "meuse-valkenburg": (-42, 8),
            "gete-halen": (7, 5), "dyle-wavre": (7, 5),
        }
        if is_impact and label_impacts:
            offset = impact_offsets.get(row["location_id"], (4, 4))
            ax.annotate(row["location_name"], observed, xytext=offset,
                        textcoords="offset points", fontsize=5.6,
                        bbox=dict(facecolor="white", alpha=.88, edgecolor="none", pad=.6),
                        zorder=9)
        # Detailed Step 01 sites remain distinct triangle markers and are
        # traceable by report_id in the allocation CSV. Their long names are
        # intentionally omitted from the already dense local panels.


def impact_legend_handles():
    return [
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#d62728",
               markeredgecolor="white", markersize=6.5, label="Reported impact locality"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor="#1f77b4",
               markeredgecolor="white", markersize=6.5, label="Step 01 detailed site"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor="#152c3d",
               markeredgecolor="white", markersize=6, label="Outlet of containing model cell"),
        Line2D([0], [0], marker="D", color="none", markerfacecolor="#df3f93",
               markeredgecolor="white", markersize=6, label="Reviewed river-assessment candidate"),
        Line2D([0], [0], color="#3d3d3d", linestyle=(0, (1.5, 2)), linewidth=.7,
               label="Reported point to model outlet"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#f28e2b",
               markeredgecolor="white", markersize=6.5, label="Discharge gauge"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor="#2676b8",
               markeredgecolor="white", markersize=6, label="Gauge model outlet"),
        Line2D([0], [0], color="#4c7694", linewidth=1.1, label="CaMa-Flood river network"),
    ]


def style_axes(ax, extent) -> None:
    west, east, south, north = extent
    ax.set_xlim(west, east)
    ax.set_ylim(south, north)
    ax.set_aspect(1 / np.cos(np.deg2rad((south + north) / 2)))
    ax.set_facecolor("#f7f8f8")
    ax.set_xlabel("Longitude (°E)", fontsize=8)
    ax.set_ylabel("Latitude (°N)", fontsize=8)
    ax.tick_params(labelsize=7, direction="out", length=3)
    ax.grid(color="#d8dfe3", linewidth=0.45, alpha=0.7, zorder=1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tutorial-dir", type=Path, required=True)
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--allocation-csv", type=Path, required=True)
    parser.add_argument("--impact-allocation-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    tutorial = args.tutorial_dir.resolve()
    map_dir = args.map_dir.resolve()
    records = read_allocations(args.allocation_csv.resolve())
    impact_records = read_impact_allocations(args.impact_allocation_csv.resolve())
    map_data = read_map(map_dir)
    lon, lat = map_data[0], map_data[1]
    segments, area, invalid_links = build_river_segments(map_dir, map_data)
    print(f"River links drawn: {len(segments)}; invalid links omitted by shared helper: {invalid_links}")

    params = (map_dir / "params.txt").read_text(encoding="utf-8").splitlines()
    dims = [int(params[i].split()[0]) for i in range(3)]
    nx, ny = dims[:2]
    resolution = float(params[3].split()[0])
    west = float(params[4].split()[0]); east = float(params[5].split()[0])
    south = float(params[6].split()[0]); north = float(params[7].split()[0])
    if (len(lon), len(lat)) != (nx, ny):
        raise ValueError("Map coordinate dimensions differ from params.txt")
    overview_extent = (west, east, south, north)

    fig = plt.figure(figsize=(13.0, 9.2), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, width_ratios=(1.15, 0.85), height_ratios=(1, 1))
    overview = fig.add_subplot(grid[:, 0])
    draw_network(overview, segments, area)
    add_impact_allocations(overview, impact_records)
    add_stations(overview, records, labels=False)
    style_axes(overview, overview_extent)
    overview.set_title("Rhine_15min map — regional context", fontsize=10, pad=8)
    # Two regional detail views expose the dense impact-location clusters
    # without shrinking the complete Rhine map.
    local_views = [
        ("Vesdre–Meuse–Gete–Dyle", (4.25, 6.35, 49.45, 51.15)),
        ("Ahr–Erft–Kyll–Prüm", (6.25, 7.65, 49.70, 51.10)),
    ]
    for index, (title, extent) in enumerate(local_views):
        ax = fig.add_subplot(grid[index, 1])
        draw_network(ax, segments, area)
        in_view_impacts = [r for r in impact_records if r["observed_lon"] and
                           extent[0] <= float(r["observed_lon"]) <= extent[1] and
                           extent[2] <= float(r["observed_lat"]) <= extent[3]]
        add_impact_allocations(ax, in_view_impacts, label_impacts=True)
        in_view_gauges = [r for r in records if
                          extent[0] <= float(r["observed_lon_deg"]) <= extent[1] and
                          extent[2] <= float(r["observed_lat_deg"]) <= extent[3]]
        add_stations(ax, in_view_gauges, labels=True)
        style_axes(ax, extent)
        ax.set_title(title, fontsize=9, pad=4)

    overview.legend(handles=impact_legend_handles(), loc="lower left", ncols=2,
                    fontsize=6.8, framealpha=0.94)
    fig.suptitle("Fig. 21 — Gauge and Flood Impact Location Allocation", fontsize=14)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=args.dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Wrote {args.output}; map={map_dir}; grid={nx}x{ny} at {resolution:g}°")


if __name__ == "__main__":
    main()
