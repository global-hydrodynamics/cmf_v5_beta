#!/usr/bin/env python3
"""Inspection Figure: catalogue footprints, flood fraction and valid support."""

import argparse
import json
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D
import numpy as np
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gfm_common import protect_old, save_json


def wrapped_title(fig, ax, title):
    """Wrap against measured map width at the final output DPI."""
    words = title.split()
    lines = []
    line = ""
    renderer = fig.canvas.get_renderer()
    for word in words:
        candidate = f"{line} {word}".strip()
        artist = ax.text(0, 1, candidate, fontsize=11)
        too_wide = (
            artist.get_window_extent(renderer).width
            > ax.get_window_extent(renderer).width
        )
        artist.remove()
        if too_wide and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    lines.append(line)
    ax.set_title("\n".join(lines), loc="left", fontsize=11, pad=12)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--work-dir", type=Path, required=True)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--group", required=True)
    p.add_argument("--fig-height", type=float, default=6.6)
    p.add_argument("--dpi", type=int, default=160)
    args = p.parse_args()
    output = protect_old(args.output, args.work_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    items = json.loads((args.data / "metadata/stac_items.json").read_text())
    if isinstance(items, dict):
        items = items.get("features", items.get("items"))
    tile = args.data / "tiles_3sec" / args.group
    provenance = json.loads((tile / "provenance.json").read_text())
    bbox = provenance["bbox"]
    w, s, e, n = bbox
    # Map first: identical physical map and reserved full-height colorbar slots.
    map_h = args.fig_height - 2.15
    map_w = map_h * (e - w) * np.cos(np.deg2rad((n + s) / 2)) / (n - s)
    left, gap, cb_gap, cb_w, right = 0.67, 1.15, 0.10, 0.14, 0.63
    cell_w = map_w + cb_gap + cb_w
    width = left + 3 * cell_w + 2 * gap + right
    fig = plt.figure(figsize=(width, args.fig_height), dpi=args.dpi)
    axes = []
    cbars = []
    for i in range(3):
        x = left + i * (cell_w + gap)
        ax = fig.add_axes(
            [x / width, 1.12 / args.fig_height, map_w / width, map_h / args.fig_height]
        )
        cb = fig.add_axes(
            [
                (x + map_w + cb_gap) / width,
                1.12 / args.fig_height,
                cb_w / width,
                map_h / args.fig_height,
            ]
        )
        ax.set(
            xlim=(w, e), ylim=(s, n), xlabel="Longitude [°E]", ylabel="Latitude [°N]"
        )
        if i > 0:
            ax.set_ylabel(
                ""
            )  # Shared latitude axis; reserve the gap for colorbar labels.
        ax.set_aspect(1 / np.cos(np.deg2rad((s + n) / 2)))
        ax.grid(alpha=0.15, linewidth=0.6)
        ax.set_axisbelow(False)
        ax.set_facecolor("#d9d9d9")
        axes.append(ax)
        cbars.append(cb)
    cbars[0].set_visible(False)
    for item in items:
        morning = "20210715T05" in item["id"]
        color = "#2369a0" if morning else "#d27c30"
        geom = item["geometry"]
        polygons = (
            geom["coordinates"]
            if geom["type"] == "MultiPolygon"
            else [geom["coordinates"]]
        )
        for poly in polygons:
            axes[0].add_patch(
                Polygon(
                    poly[0], facecolor=color, edgecolor=color, alpha=0.14, linewidth=0.8
                )
            )
    axes[0].set_facecolor("white")
    axes[0].legend(
        handles=[
            Line2D([], [], color="#2369a0", label="S1A morning · 11 Items"),
            Line2D([], [], color="#d27c30", label="S1B afternoon · 6 Items"),
        ],
        loc="upper left",
        fontsize=8,
        framealpha=0.95,
    )
    # Inspection-only 6x6 display bins retain maxima, not a new science product.
    factor = 6
    with rasterio.open(tile / "rhine3sec.flood_fraction.tif") as src:
        a = src.read(1)
        valid = a != src.nodata
        reshaped = np.where(valid, a, -1).reshape(600, factor, 800, factor)
        flood = reshaped.max(axis=(1, 3))
        flood = np.ma.masked_less(flood, 0)
    with rasterio.open(tile / "rhine3sec.valid_fraction.tif") as src:
        coverage = src.read(1).reshape(600, factor, 800, factor).mean(axis=(1, 3))
    cmap = plt.get_cmap("Blues").copy()
    cmap.set_bad("#d9d9d9")
    for i, array in [(1, flood), (2, coverage)]:
        im = axes[i].imshow(
            array * 100,
            extent=[w, e, s, n],
            origin="upper",
            cmap=cmap,
            vmin=0,
            vmax=100,
            interpolation="nearest",
            aspect=1 / np.cos(np.deg2rad((s + n) / 2)),
        )
        fig.colorbar(
            im,
            cax=cbars[i],
            label=(
                "Flooded / valid support [%]"
                if i == 1
                else "Valid / complete cell area [%]"
            ),
        )
    fig.canvas.draw()
    for ax, title in zip(
        axes,
        [
            "(a) GFM catalogue footprints · both passes",
            "(b) Morning flood fraction · 3-second product",
            "(c) Morning valid observation coverage",
        ],
    ):
        wrapped_title(fig, ax, title)
    fig.text(
        0.5,
        0.965,
        "Rhine event · 15 July 2021 · S1A 05:49:37–05:51:42 UTC",
        ha="center",
        va="top",
        fontsize=13,
    )
    fig.text(
        left / width,
        0.102,
        "Display bins: 6 × 6 cells; flood = maximum valid fraction, coverage = mean support. Grey = no valid flood observation.",
        fontsize=8,
        va="top",
    )
    fig.text(
        left / width,
        0.075,
        "Footprints are catalogue tiles, not usable SAR coverage. Morning: relative orbit 37, descending; afternoon is not processed.",
        fontsize=8,
        va="top",
    )
    fig.text(
        left / width,
        0.048,
        "Source: Copernicus EMS GFM via EODC · Atlantis 9371dc4 · no model comparison or peak-event inference.",
        fontsize=8,
        va="top",
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    canvas = fig.bbox
    for artist in fig.findobj(matplotlib.text.Text):
        if not artist.get_visible() or not artist.get_text():
            continue
        box = artist.get_window_extent(renderer)
        if (
            box.width
            and box.height
            and (
                box.x0 < -1
                or box.y0 < -1
                or box.x1 > canvas.width + 1
                or box.y1 > canvas.height + 1
            )
        ):
            raise ValueError(f"Text outside canvas: {artist.get_text()}")
    # Colorbar decoration must not collide with the next panel's latitude ticks.
    cbar_right = max(
        t.get_window_extent(renderer).x1
        for t in [cbars[1].yaxis.label, *cbars[1].get_yticklabels()]
        if t.get_visible() and t.get_text()
    )
    next_left = min(
        t.get_window_extent(renderer).x0
        for t in axes[2].get_yticklabels()
        if t.get_visible() and t.get_text()
    )
    assert cbar_right + 8 < next_left, "Colorbar / next-panel label collision"
    geometry = [list(ax.get_window_extent(renderer).bounds) for ax in axes]
    assert np.allclose([b[2:] for b in geometry], geometry[0][2:], atol=1e-7)
    for ax, cb in zip(axes[1:], cbars[1:]):
        assert np.allclose(
            ax.get_window_extent(renderer).bounds[1::2],
            cb.get_window_extent(renderer).bounds[1::2],
            atol=1e-7,
        )
    fig.savefig(output, dpi=args.dpi, facecolor="white")
    save_json(
        args.work_dir / "logs/gfm_figure_geometry.json",
        dict(
            canvas_pixels=list(canvas.bounds),
            map_axes_pixels=geometry,
            extent=bbox,
            dpi=args.dpi,
            display_bin=6,
        ),
    )
    plt.close(fig)
    print(output)


if __name__ == "__main__":
    main()
