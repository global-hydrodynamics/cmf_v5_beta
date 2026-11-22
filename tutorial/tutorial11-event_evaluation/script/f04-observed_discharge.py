#!/usr/bin/env python3
"""Plot the original supplied July 2021 discharge observations, points only."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tutorial-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.tutorial_dir.resolve()
    data = root / "observation" / "stations_data"
    metadata_path = data / "allstations.csv"
    series_path = data / "Qobs_06_2021_st153_63_28.csv"
    for path in (metadata_path, series_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    with metadata_path.open(newline="", encoding="utf-8-sig") as stream:
        station_rows = {int(row["Id"]): row for row in csv.DictReader(stream)}
    with series_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        station_ids = [int(key) for key in reader.fieldnames[1:]]
        records = list(reader)
    times = [datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M") for row in records]
    start, end = datetime(2021, 7, 1), datetime(2021, 8, 1)
    keep = [i for i, timestamp in enumerate(times) if start < timestamp <= end]
    if len(keep) != 124:
        raise ValueError(f"Expected 124 July interval-end records per station, got {len(keep)}")
    values = {sid: np.array([float(records[i][str(sid)]) for i in keep]) for sid in station_ids}
    global_top = max(float(series.max()) for series in values.values()) * 1.08

    plt.rcParams.update({"font.size": 10, "axes.titlesize": 12, "axes.labelsize": 10})
    fig, axes = plt.subplots(3, 1, figsize=(11.5, 8), sharex=True, sharey=True, constrained_layout=True)
    colors = ["#2b6f9c", "#d97927", "#39845b"]
    for ax, station_id, color in zip(axes, station_ids, colors):
        station = station_rows[station_id]
        series = values[station_id]
        station_times = [times[i] for i in keep]
        ax.scatter(station_times, series, s=18, color=color, alpha=0.9, edgecolors="white", linewidths=0.35,
                   label="Supplied 6-hour values", zorder=3)
        peak_idx = int(np.argmax(series))
        ax.scatter([station_times[peak_idx]], [series[peak_idx]], marker="*", s=115, color="#8e3d76",
                   edgecolors="white", linewidths=0.6, zorder=4, label="July maximum")
        ax.annotate(f"max {series[peak_idx]:,.3f}\n{station_times[peak_idx]:%b %d %H:%M}",
                    (station_times[peak_idx], series[peak_idx]), xytext=(8, -30), textcoords="offset points",
                    fontsize=8, color="#552642", bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#c7b6c0", "alpha": .9})
        ax.set_title(f"{station['Name']} ({station_id}) · {station['River']}, {station['Country']}", loc="left", fontweight="bold")
        ax.set_ylabel("Discharge\n(unit not declared)")
        ax.set_ylim(0, global_top)
        ax.yaxis.set_major_locator(MaxNLocator(5))
        ax.grid(True, color="#cfd6da", linewidth=0.65, alpha=0.8)
        ax.spines[["top", "right"]].set_visible(False)
    axes[-1].set_xlim(start, end)
    axes[-1].xaxis.set_major_locator(mdates.DayLocator(interval=4))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    axes[-1].set_xlabel("Timestamp as supplied (timezone unspecified; interval-end convention per provider correspondence)")
    axes[0].legend(loc="upper left", ncols=2, frameon=True, fontsize=8)
    fig.suptitle("Observed Rhine Discharge · July 2021", fontsize=15, fontweight="bold")
    fig.text(0.5, -0.005, "124 original CSV values per station; points only, with no interpolation, connecting lines, smoothing or resampling.",
             ha="center", fontsize=9, color="#444444")
    out = root / "figure" / "f04-observed_discharge.png"
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {out.relative_to(root)}")


if __name__ == "__main__":
    main()
