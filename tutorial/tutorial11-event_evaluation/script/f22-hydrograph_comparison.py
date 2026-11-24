#!/usr/bin/env python3
"""Plot the Step 22 model–observation hydrograph overlay from its CSV handoff."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

STATIONS = [(153, "Lobith"), (63, "Speyer"), (28, "Maxau")]


def parse_plot_time(value: str) -> datetime:
    """Use nominal timestamp labels without shifting uncertain observation times."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tutorial-dir", type=Path, required=True)
    parser.add_argument("--timeseries-csv", type=Path, required=True)
    parser.add_argument("--summary-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fig-width", type=float, default=11, help="Canvas width [inches]")
    parser.add_argument("--fig-height", type=float, default=8, help="Canvas height [inches]")
    parser.add_argument("--dpi", type=int, default=180, help="PNG resolution [pixels/inch]")
    parser.add_argument("--display-start")
    parser.add_argument("--display-end")
    parser.add_argument("--ymin", type=float, default=0)
    parser.add_argument("--ymax", type=float)
    parser.add_argument("--model-color", default="#2369a1")
    parser.add_argument("--observation-color", default="#d87524")
    args = parser.parse_args()
    with args.timeseries_csv.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"No time-series records in {args.timeseries_csv}")

    plt.rcParams.update({"font.size": 10, "axes.titlesize": 12, "axes.labelsize": 10})
    fig, axes = plt.subplots(3, 1, figsize=(args.fig_width, args.fig_height), sharex=True, constrained_layout=True)
    colors = {"model": args.model_color, "observation": args.observation_color}
    labels = {"model": "Model (m³/s)", "observation": "Observation (unit unspecified)"}
    for ax, (station_id, station_name), panel in zip(axes, STATIONS, "abc"):
        selected = [row for row in rows if int(row["station_id"]) == station_id]
        for source in ("model", "observation"):
            series = [row for row in selected if row["source"] == source]
            times = [parse_plot_time(row["datetime_comparison"]) for row in series]
            values = [float(row["discharge"]) for row in series]
            if source == "model":
                ax.plot(times, values, color=colors[source], linewidth=1.8, label=labels[source], zorder=2)
            else:
                ax.plot(times, values, color=colors[source], linewidth=1.2, marker="o", markersize=4.0,
                        label=labels[source], zorder=3)
        ax.set_title(f"({panel}) {station_name} (Station {station_id})", loc="left", fontweight="bold")
        ax.set_ylabel("Discharge\n(m³/s model; obs unit unknown)")
        ax.set_ylim(bottom=args.ymin, top=args.ymax)
        ax.grid(True, color="#d1d8dc", linewidth=0.65, alpha=0.85)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(loc="upper left", ncols=2, frameon=True, fontsize=8)
    summary = json.loads(args.summary_json.read_text(encoding="utf-8"))
    period = summary["comparison_period"]
    start = datetime.fromisoformat(period["start_inclusive"])
    end = datetime.fromisoformat(period["end_exclusive"])
    start = datetime.fromisoformat(args.display_start) if args.display_start else start
    end = datetime.fromisoformat(args.display_end) if args.display_end else end
    if end <= start:
        raise ValueError("Display end must follow start")
    axes[-1].set_xlim(start, end)
    axes[-1].xaxis.set_major_locator(mdates.DayLocator(interval=1))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    axes[-1].set_xlabel("Nominal timestamp (model UTC; observation timezone unknown, labels as supplied)")
    fig.suptitle("Tutorial 11 Fig. 22 — Model–Observation Hydrograph Comparison", fontsize=14, fontweight="bold")
    fig.text(0.5, -0.012,
             "Provisional overlay: observation times are unadjusted source labels; discharge units are not declared. "
             "No temporal averaging, interpolation, or value conversion was applied.",
             ha="center", fontsize=8.5, color="#444444")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=args.dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
