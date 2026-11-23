#!/usr/bin/env python3
"""Map observed Rhine gauges and their selected CaMa-Flood outlets."""

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
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    tutorial = args.tutorial_dir.resolve()
    map_dir = args.map_dir.resolve()
    records = read_allocations(args.allocation_csv.resolve())
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

    fig = plt.figure(figsize=(11.0, 9.0), constrained_layout=True)
    grid = fig.add_gridspec(3, 2, width_ratios=(1.25, 0.75))
    overview = fig.add_subplot(grid[:, 0])
    draw_network(overview, segments, area)
    add_stations(overview, records, labels=False)
    style_axes(overview, overview_extent)
    overview.set_title("Rhine_15min map — regional context", fontsize=10, pad=8)
    for row in records:
        x, y = float(row["observed_lon_deg"]), float(row["observed_lat_deg"])
        overview.annotate(row["station_name"], (x, y), xytext=(5, 5),
                          textcoords="offset points", fontsize=8,
                          bbox=dict(facecolor="white", alpha=.82, edgecolor="none", pad=1.2), zorder=9)

    for index, row in enumerate(records):
        ax = fig.add_subplot(grid[index, 1])
        draw_network(ax, segments, area)
        add_stations(ax, [row], labels=True)
        observed = (float(row["observed_lon_deg"]), float(row["observed_lat_deg"]))
        outlet = (float(row["model_outlet_lon_deg"]), float(row["model_outlet_lat_deg"]))
        span = max(abs(observed[0] - outlet[0]), abs(observed[1] - outlet[1]), 0.22) + 0.16
        center_x = (observed[0] + outlet[0]) / 2
        center_y = (observed[1] + outlet[1]) / 2
        extent = (center_x - span, center_x + span, center_y - span, center_y + span)
        style_axes(ax, extent)
        ax.set_title(
            f"{row['station_name']} ({row['station_id']}) — {row['observed_to_outlet_great_circle_km']} km",
            fontsize=9, pad=5,
        )

    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#f28e2b",
               markeredgecolor="white", markersize=7, label="Observed gauge"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor="#2676b8",
               markeredgecolor="white", markersize=7, label="CaMa unit-catchment outlet"),
        Line2D([0], [0], color="#626262", linestyle=(0, (2, 2)), linewidth=0.8,
               label="Gauge-to-outlet distance"),
        Line2D([0], [0], color="#4c7694", linewidth=1.1, label="CaMa-Flood river network"),
    ]
    overview.legend(handles=handles, loc="lower left", fontsize=7.2, framealpha=0.92)
    fig.suptitle("Tutorial 11 Fig. 21 — Discharge gauge allocation", fontsize=14)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=args.dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Wrote {args.output}; map={map_dir}; grid={nx}x{ny} at {resolution:g}°")


if __name__ == "__main__":
    main()
