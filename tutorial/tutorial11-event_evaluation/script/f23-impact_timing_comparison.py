#!/usr/bin/env python3
"""Render Step 23 model hydrographs and reported flood-timing summary."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
import re
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

RIVER_COLORS = {
    "Ahr": "#d62728", "Erft/Swist": "#9467bd", "Kyll": "#ff7f0e",
    "Prüm": "#8c564b", "Vesdre/Meuse": "#1f77b4", "Meuse": "#17a2a4",
    "Meuse basin / Geul": "#00a6a6", "Gete": "#2ca02c", "Dyle": "#bcbd22",
}
TYPE_MARKERS = {"discharge_peak": "o", "water_level_peak": "^"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def parse_time(value: str) -> datetime | None:
    if not value:
        return None
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(text)
    if parsed.utcoffset() is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def cell_id(row: dict[str, str]) -> tuple[int, int] | None:
    if not row.get("model_row_0based") or not row.get("model_col_0based"):
        return None
    return int(row["model_row_0based"]), int(row["model_col_0based"])


def river_color(groups: str) -> str:
    first = groups.split(";")[0].strip() if groups else ""
    return RIVER_COLORS.get(first, "#4e79a7")


def plot_hydrographs(series: list[dict[str, str]], comparisons: list[dict[str, str]], output: Path) -> None:
    cells = sorted({cell_id(row) for row in series if cell_id(row) is not None})
    records_by_cell: dict[tuple[int, int], list[dict[str, str]]] = {cell: [] for cell in cells}
    for row in comparisons:
        cell = cell_id(row)
        if cell in records_by_cell:
            records_by_cell[cell].append(row)
    groups_by_cell = {}
    for row in series:
        cell = cell_id(row)
        if cell is not None:
            groups_by_cell[cell] = row.get("river_groups", "")

    ncols = 3
    nrows = int(np.ceil(len(cells) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(15, 3.0 * nrows), sharex=True, squeeze=False)
    start, end = datetime(2021, 7, 13), datetime(2021, 7, 17)
    grouped_series: dict[tuple[int, int], list[dict[str, str]]] = {cell: [] for cell in cells}
    for row in series:
        cell = cell_id(row)
        if cell is not None:
            grouped_series[cell].append(row)

    for index, cell in enumerate(cells):
        ax = axes[index // ncols][index % ncols]
        records = records_by_cell[cell]
        values = sorted(grouped_series[cell], key=lambda row: row["datetime_utc"])
        times = [parse_time(row["datetime_utc"]) for row in values]
        flow = np.asarray([float(row["outflw_m3s"]) for row in values])
        visible = np.asarray([start <= value < end for value in times])
        ax.plot(np.asarray(times, dtype=object)[visible], flow[visible], color="#2f6f9f", linewidth=1.55,
                label="Model outflw")

        peak_time = max(zip(flow, times), key=lambda pair: pair[0])[1]
        ax.axvline(peak_time, color="#c73e3a", linewidth=1.1, linestyle="--", zorder=3)
        if not (start <= peak_time < end):
            ax.text(0.98, 0.94, f"Search max {peak_time:%d Jul %H:%M} UTC\n(outside display)",
                    transform=ax.transAxes, ha="right", va="top", fontsize=7,
                    bbox=dict(facecolor="white", alpha=.85, edgecolor="none", pad=1.5))

        seen: set[tuple[str, str]] = set()
        for record in records:
            observed_start = parse_time(record["observed_start_time_utc"])
            observed_end = parse_time(record["observed_end_time_utc"])
            marker = TYPE_MARKERS.get(record["timing_type"])
            if observed_start is None or observed_end is None or marker is None:
                continue
            token = (record["timing_type"], observed_start.isoformat())
            if token in seen:
                continue
            seen.add(token)
            color = "#d88900" if record["timing_type"] == "discharge_peak" else "#7b4ab5"
            ax.axvline(observed_start, color=color, linewidth=1.0,
                       linestyle="-" if marker == "o" else ":", alpha=.9, zorder=2)
            ax.scatter([observed_start], [ax.get_ylim()[1] * .92], marker=marker,
                       s=26, color=color, edgecolor="white", linewidth=.4, clip_on=False, zorder=5)

        names = ", ".join(dict.fromkeys(row["location_name"] for row in records))
        river_groups = "; ".join(dict.fromkeys(row["river_group"] for row in records if row["river_group"]))
        statuses = ", ".join(dict.fromkeys(row["river_allocation_status"] for row in records if row["river_allocation_status"]))
        ax.set_title(f"Grid {cell[0]},{cell[1]} — {river_groups or groups_by_cell.get(cell, '')}", fontsize=9)
        ax.text(.02, .96, textwrap.fill(names, width=39), transform=ax.transAxes, va="top", fontsize=6.3,
                bbox=dict(facecolor="white", alpha=.8, edgecolor="none", pad=1.4))
        ax.text(.98, .04, f"River status: {statuses or 'not assessed'}" + ("; upstream proxy" if any(r.get("model_cell_basis") == "one_step_upstream_tributary_proxy" for r in records) else ""), transform=ax.transAxes,
                ha="right", va="bottom", fontsize=6.3, color="#555555")
        ax.set_xlim(start, end)
        ax.set_ylabel("Discharge (m³/s)", fontsize=8)
        ax.grid(axis="y", color="#d9dee3", linewidth=.55)
        ax.tick_params(labelsize=7)
    for index in range(len(cells), nrows * ncols):
        axes[index // ncols][index % ncols].set_visible(False)
    for ax in axes[-1]:
        if ax.get_visible():
            ax.xaxis.set_major_locator(mdates.DayLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d Jul"))
            ax.set_xlabel("Time (UTC)", fontsize=8)

    legend = [
        Line2D([0], [0], color="#2f6f9f", lw=1.6, label="Model outflw (hourly)"),
        Line2D([0], [0], color="#c73e3a", lw=1.1, ls="--", label="Model maximum, Jul 12–18"),
        Line2D([0], [0], color="#d88900", lw=1.0, label="Reported discharge peak (UTC)"),
        Line2D([0], [0], color="#7b4ab5", lw=1.0, ls=":", label="Reported water-level peak (UTC; reference)"),
    ]
    fig.legend(handles=legend, loc="lower center", ncols=4, frameon=False, fontsize=8,
               bbox_to_anchor=(.5, .005))
    fig.suptitle("Fig. 23a — Impact-location Hydrograph Comparison", fontsize=14, y=.998)
    fig.text(.5, .025, "Final Step 21 cells; Ahr upstream proxies omit downstream area. Water-level peaks are reference only.",
             ha="center", fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, .045, 1, .978))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_timing_summary(comparisons: list[dict[str, str]], output: Path) -> None:
    records = sorted(comparisons, key=lambda row: (row["river_group"], row["location_name"], row["report_id"]))
    fig, ax = plt.subplots(figsize=(15, max(8.0, len(records) * .39)))
    start, end = datetime(2021, 7, 13), datetime(2021, 7, 17)
    fig.subplots_adjust(left=.34, right=.72, bottom=.11, top=.94)
    y_positions = np.arange(len(records))
    for y, row in zip(y_positions, records):
        notes = []
        if row.get("model_cell_basis") == "one_step_upstream_tributary_proxy":
            notes.append("Upstream tributary proxy")
        if row.get("comparison_status") in {
            "river_not_represented_context_only",
            "river_match_unresolved_context_only",
        }:
            notes.append("Model context only")
        model_time = parse_time(row["model_peak_time_utc"])
        if model_time is not None:
            if start <= model_time < end:
                ax.scatter(model_time, y, marker="D", s=31, color="#c73e3a", edgecolor="white",
                           linewidth=.45, zorder=4)
            else:
                boundary = start if model_time < start else end
                direction = -1 if model_time < start else 1
                ax.scatter(boundary, y, marker="<" if direction < 0 else ">", s=38,
                           color="#c73e3a", clip_on=False, zorder=4)
                notes.append(f"Model max {model_time:%d Jul %H:%M} UTC (outside view)")

        observed_start = parse_time(row["observed_start_time_utc"])
        observed_end = parse_time(row["observed_end_time_utc"])
        marker = TYPE_MARKERS.get(row["timing_type"])
        if observed_start is not None and observed_end is not None and marker:
            obs_color = "#d88900" if row["timing_type"] == "discharge_peak" else "#7b4ab5"
            if observed_start == observed_end:
                ax.scatter(observed_start, y, marker=marker, s=33, color=obs_color,
                           edgecolor="white", linewidth=.45, zorder=5)
            else:
                ax.hlines(y, observed_start, observed_end, color=obs_color, linewidth=5, alpha=.35, zorder=2)
                ax.scatter([observed_start, observed_end], [y, y], marker=marker, s=22,
                           color=obs_color, zorder=3)
        elif row.get("time_original"):
            timezone_note = row.get("timezone_original", "").casefold()
            has_clock = re.search(r"\b\d{1,2}:\d{2}\b", row["time_original"]) is not None
            notes.append("Timezone not confirmed" if has_clock and (
                "not stated" in timezone_note or "unknown" in timezone_note
            ) else "Timing unavailable")
        else:
            notes.append("Timing unavailable")
        if notes:
            ax.text(1.04, y, "; ".join(notes), transform=ax.get_yaxis_transform(),
                    ha="left", va="center", fontsize=6.4, color="#777777")

    labels = [f"{row['river_group']} — {row['location_name']} [{row['timing_type']}]" for row in records]
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(start, end)
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d Jul"))
    ax.set_xlabel("UTC date (July 13–16; end exclusive July 17)")
    ax.set_title("Fig. 23b — Flood Peak Timing Summary", fontsize=14, pad=12)
    ax.grid(axis="x", color="#d9dee3", linewidth=.6)
    ax.spines[["top", "right"]].set_visible(False)
    legend = [
        Line2D([0], [0], marker="D", color="none", markerfacecolor="#c73e3a",
               markeredgecolor="white", label="Model search-window maximum"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#d88900",
               label="Reported discharge peak (UTC)"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor="#7b4ab5",
               label="Reported water-level peak (UTC; reference only)"),
    ]
    ax.legend(handles=legend, loc="lower center", bbox_to_anchor=(.5, -0.10), ncols=3,
              frameon=False, fontsize=8)
    fig.text(.5, .025, "Timezone-unknown source labels remain in the metadata and are not plotted on this UTC axis. Red boundary arrows denote model maxima outside the display period.",
             ha="center", fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, .045, 1, 1))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeseries-csv", type=Path, required=True)
    parser.add_argument("--comparison-csv", type=Path, required=True)
    parser.add_argument("--hydrographs-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()
    series = read_csv(args.timeseries_csv)
    comparisons = read_csv(args.comparison_csv)
    plot_hydrographs(series, comparisons, args.hydrographs_output)
    plot_timing_summary(comparisons, args.summary_output)
    print(f"Wrote {args.hydrographs_output}")
    print(f"Wrote {args.summary_output}")


if __name__ == "__main__":
    main()
