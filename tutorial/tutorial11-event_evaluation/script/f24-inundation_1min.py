#!/usr/bin/env python3
"""Render only the existing preliminary Step24 simulated-depth product.

Inputs: Step24 verification JSON and its saved flddph NetCDF depth field [m].
Output: the preliminary 1 arc-minute depth PNG.
Workflow:
    1. Read the retained depth and geographic extent.
    2. Distinguish dry zero, positive depth and missing/unmapped pixels.
    3. Annotate saved acquisition/model times and export the figure.
Positive simulated depth includes permanent river water; this renderer performs
no downscaling, satellite comparison or accuracy assessment.
"""
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta

import matplotlib

# Select the noninteractive backend before importing pyplot.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from netCDF4 import Dataset
import numpy as np


def main():
    """Render saved depth [m], dry/NoData classes and retained UTC timing annotations."""

    #*** 1. Read display settings and retained simulated-depth product
    # Preserve the established CLI description while expanding source documentation.
    p = argparse.ArgumentParser(description='Render only the existing preliminary Step24 simulated-depth product.')
    p.add_argument("--tutorial-dir", type=Path, required=True)
    p.add_argument("--fig-width", type=float, default=8.4, help="Canvas width [inches]")
    p.add_argument("--fig-height", type=float, default=7.2, help="Canvas height [inches]")
    p.add_argument("--dpi", type=int, default=200, help="PNG resolution [pixels/inch]")
    p.add_argument("--metadata", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--cmap", default="YlGnBu")
    p.add_argument("--vmin", type=float, default=0)
    p.add_argument("--vmax", type=float, default=10)
    a = p.parse_args()
    t = a.tutorial_dir
    report = json.loads((a.metadata or t / "metadata/24_downscaling_verification.json").read_text())
    with Dataset(t / report["output"]) as d:
        depth = np.ma.asarray(d["flddph"][:])
        lon = d["lon"][:]
        lat = d["lat"][:]
    west, south, east, north = report["extent_west_south_east_north"]

    #*** 2. Draw dry, positive-depth and missing-support classes
    fig, ax = plt.subplots(figsize=(a.fig_width, a.fig_height))
    fig.subplots_adjust(left=.1, right=.88, bottom=.22, top=.87)
    ax.set_facecolor("#b8b8b8")
    extent = [west, east, south, north]
    dry = np.ma.masked_where(np.ma.getmaskarray(depth) | (depth.filled(-1) != 0), np.ones(depth.shape))
    ax.imshow(dry, extent=extent, origin="upper", interpolation="none", cmap=ListedColormap(["#f3efe2"]), vmin=0, vmax=1)
    wet = np.ma.masked_where(depth.filled(-1) <= 0, depth)
    image = ax.imshow(wet, extent=extent, origin="upper", interpolation="none", cmap=a.cmap, vmin=a.vmin, vmax=a.vmax)
    ax.set_aspect(1 / np.cos(np.deg2rad((south + north) / 2)))
    ax.set_xlim(west, east)
    ax.set_ylim(south, north)
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.set_xticks(np.arange(west, east + .1, 1))
    ax.set_yticks(np.arange(south, north + .1, 1))
    fig.colorbar(image, ax=ax, shrink=.78, pad=.035, extend="max", label="Simulated inundation depth (m)")
    ax.legend(
        handles=[Patch(facecolor="#f3efe2", label="Dry (0 m)"),
                 Patch(facecolor="#b8b8b8", label="NoData / unmapped")],
        loc="lower left", fontsize=8, framealpha=.95,
    )
    fig.suptitle("Tutorial 11 Fig. 24 — Preliminary 1 arcmin inundation", fontsize=13, y=.96)

    #*** 3. Annotate saved UTC acquisition/model times and export
    observation = datetime.fromisoformat(report["representative_time_utc"].replace("Z", "+00:00"))
    observation = (observation + timedelta(seconds=.5)).replace(microsecond=0)
    model = datetime.fromisoformat(report["model_time_utc"].replace("Z", "+00:00"))
    delta = round(report["model_minus_observation_seconds"])
    sign = "+" if delta >= 0 else "−"
    minutes, seconds = divmod(abs(delta), 60)
    ax.set_title(
        f"S1A orbit {report['absolute_orbit']:06d} · {model:%d %B %Y}\n"
        f"Observation ≈{observation:%H:%M:%S} UTC → model {model:%H:%M} UTC ({sign}{minutes} min {seconds} s)",
        fontsize=10,
    )
    fig.text(
        .1, .12,
        "Tributary-aware CaMa-Flood downscaling of flddph; Rhine2021.\n"
        "Permanent-water minimum: 0.1 m. Positive depth includes river water.\n"
        "Preliminary simulated product; no satellite comparison or accuracy assessment.",
        fontsize=9, va="top",
    )
    output = a.output or t / "figure/f24-inundation_1min.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=a.dpi)
    plt.close(fig)
    print(output)


if __name__ == "__main__":
    main()
