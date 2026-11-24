#!/usr/bin/env python3
"""Render Step 23 model hydrographs and reported flood-timing summary.

Inputs: Step23 saved series/comparisons and the existing summary display JSON.
Outputs: hydrograph and timing-summary PNGs, plus display-review JSON.
Workflow:
    1. Read analysis handoffs without recomputing allocation or peak searches.
    2. Plot model series and reported discharge/water-level timing context.
    3. Render the configured summary and record display/layout diagnostics.
Water-level peaks are reference context. Out-of-view arrows retain actual times;
marker fills describe observation availability, not agreement or model skill.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import textwrap

import matplotlib

# Select the noninteractive backend before importing pyplot.
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
    """Read saved handoff rows without recomputing analysis fields."""
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def parse_time(value: str) -> datetime | None:
    """Normalize explicit offsets to naive UTC; leave naive supplied labels unchanged."""
    if not value:
        return None
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(text)
    if parsed.utcoffset() is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def cell_id(row: dict[str, str]) -> tuple[int, int] | None:
    """Return the saved zero-based (row, col), or None when either field is absent."""
    if not row.get("model_row_0based") or not row.get("model_col_0based"):
        return None
    return int(row["model_row_0based"]), int(row["model_col_0based"])


def river_color(groups: str) -> str:
    """Choose the first recorded river-group color with the existing neutral fallback."""
    first = groups.split(";")[0].strip() if groups else ""
    return RIVER_COLORS.get(first, "#4e79a7")


def plot_hydrographs(series: list[dict[str, str]], comparisons: list[dict[str, str]], output: Path, width=15, row_height=3, dpi=200) -> None:
    """Plot saved unique-cell flows [m3/s] and reported peak-time markers.

    The display window is distinct from the saved wider peak-search series.
    Reported water-level peaks are timing context, not discharge observations."""

    #*** 1. Group saved series and comparison records by model cell
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

    #*** 2. Plot the fixed view while retaining wider search maxima
    ncols = 3
    nrows = int(np.ceil(len(cells) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(width, row_height * nrows), sharex=True, squeeze=False)
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

    #*** 3. Explain timing context and export the hydrographs
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
    fig.savefig(output, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def wrap_figure_text(text, renderer, max_width, fontsize=8):
    """Wrap decorations using rendered text width at the final output DPI."""
    from matplotlib.font_manager import FontProperties
    font = FontProperties(size=fontsize)
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and renderer.get_text_width_height_descent(candidate, font, False)[0] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines)


def plot_timing_summary(comparisons, output: Path, settings_path: Path):
    """Render saved peak times; display settings never change search-window values."""

    #*** 1. Read display bounds, palette and retained timing records
    settings = json.loads(settings_path.read_text())
    palette_path = (settings_path.parent / settings["basin_colors_file"]).resolve()
    palette = json.loads(palette_path.read_text())[settings["basin_colors_section"]]["plot_group_colors"]
    aliases = settings.get("basin_aliases", {})
    neutral = settings.get("neutral_color", "#888888")
    start, end = parse_time(settings["display_start_utc"]), parse_time(settings["display_end_utc"])
    if start is None or end is None or end <= start:
        raise ValueError("Summary display bounds must be an increasing UTC period")
    records = sorted(comparisons, key=lambda row: (row["river_group"], row["location_name"], row["report_id"]))
    # Fixed physical plot area; text columns and legends occupy their own margins.
    left, bottom, plot_width = 3.35, 2.35, 6.75
    plot_height = max(5.6, len(records) * .255)
    width, height, dpi = settings.get("fig_width", 11.65), (settings.get("fig_height") or bottom + plot_height + .65), settings.get("dpi", 200)
    fig = plt.figure(figsize=(width, height), dpi=dpi)
    ax = fig.add_axes([left / width, bottom / height, plot_width / width, plot_height / height])
    ax.set_xlim(start, end)
    ax.set_ylim(len(records) - .5, -.5)
    ax.set_yticks([])
    ax.tick_params(axis="x", labelsize=8, length=3)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=int(settings.get("tick_hours", 6))))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b\n%H:%M"))
    ax.set_xlabel("Time (UTC)", fontsize=9, labelpad=7)
    ax.grid(axis="x", color="#d9dee3", linewidth=.55)
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.text(.5, 1 - .25 / height, settings.get("title", "Flood Peak Timing Summary"),
             ha="center", va="top", fontsize=13)
    transform = ax.get_yaxis_transform()
    label_x, color_x = (.66 - left) / plot_width, (.47 - left) / plot_width
    note_x = 1 + .14 / plot_width
    ax.text(label_x, -.95, "Location / station", transform=transform, fontsize=9, weight="bold")
    ax.text(note_x, -.95, "Notes", transform=transform, fontsize=8, weight="bold")
    measured_labels, note_texts = [], []
    unresolved, outside, basin_rows, label_rows = [], [], [], []
    previous_group = None

    def draw_time(value, y, color, marker, size, filled=True):
        """Outside arrows are display indicators, with actual times retained in row notes."""
        if start <= value < end:
            ax.scatter(value, y, marker=marker, s=size,
                       facecolors=color if filled else "none", edgecolors=color if not filled else "white",
                       linewidths=.75 if not filled else .5, zorder=5)
            return None
        side = "<" if value < start else ">"
        # Put the arrow just outside the plotting area, not at a data timestamp.
        edge_x = -.008 if side == "<" else 1.008
        ax.scatter(edge_x, y, transform=transform, marker=side, s=40,
                   color=color, clip_on=False, zorder=5)
        return f"{side}{value:%d %b %H:%M}"

    #*** 2. Render per-report timing with explicit missing/outside-view indicators
    for y, row in enumerate(records):
        group = row["river_group"]
        canonical = aliases.get(group, group)
        basin_color = palette.get(canonical, neutral)
        if canonical not in palette:
            unresolved.append(group)
        basin_rows.append({"report_id": row["report_id"], "group": group,
                           "palette_group": canonical, "color": basin_color})
        if previous_group is not None and group != previous_group:
            ax.axhline(y - .5, color="#c9cdd1", linewidth=.6, zorder=1)
        previous_group = group
        observed_start = parse_time(row["observed_start_time_utc"])
        observed_end = parse_time(row["observed_end_time_utc"])
        marker = TYPE_MARKERS.get(row["timing_type"])
        has_utc_peak = observed_start is not None and observed_end is not None and marker is not None
        label = settings.get("short_labels", {}).get(row["report_id"], row["location_name"])
        measured_labels.append(ax.text(label_x, y, label, transform=transform, ha="left", va="center",
                                       fontsize=8.6, color="#222222" if has_utc_peak else "#666666",
                                       weight="bold" if has_utc_peak else "normal"))
        ax.scatter(color_x, y, transform=transform, marker="s", s=23,
                   c=basin_color, edgecolors="none", clip_on=False, zorder=6)
        label_rows.append({"report_id": row["report_id"], "label": label, "utc_peak_emphasized": has_utc_peak})
        codes = []
        if row.get("model_cell_basis") == "one_step_upstream_tributary_proxy":
            codes.append("P")
        if row.get("comparison_status") in {"river_not_represented_context_only", "river_match_unresolved_context_only"}:
            codes.append("C")
        model_time = parse_time(row["model_peak_time_utc"])
        if model_time is not None:
            indicator = draw_time(model_time, y + .1 if has_utc_peak else y, "#c73e3a", "D", 32 if has_utc_peak else 25, filled=has_utc_peak)
            if indicator:
                codes.append(indicator)
                outside.append({"report_id": row["report_id"], "kind": "model", "actual_time_utc": row["model_peak_time_utc"]})
        else:
            codes.append("N")
        if has_utc_peak:
            obs_color = "#d88900" if marker == "o" else "#7b4ab5"
            if observed_start != observed_end and observed_end >= start and observed_start < end:
                ax.hlines(y-.1, max(start,observed_start), min(end,observed_end), color=obs_color,
                          linewidth=5, alpha=.35, zorder=2)
            for value in dict.fromkeys([observed_start, observed_end]):
                indicator = draw_time(value, y - .1, obs_color, marker, 45)
                if indicator:
                    codes.append("Obs" + indicator)
                    outside.append({"report_id": row["report_id"], "kind": "observation", "actual_time_utc": value.isoformat() + "Z"})
        else:
            raw_time = row.get("time_original", "")
            timezone_note = row.get("timezone_original", "").casefold()
            has_clock = re.search(r"\b\d{1,2}:\d{2}\b", raw_time) is not None
            codes.append("U" if has_clock and ("not stated" in timezone_note or "unknown" in timezone_note) else "M")
        if codes:
            note_texts.append(ax.text(note_x, y, " ".join(codes), transform=transform, ha="left", va="center",
                                      fontsize=7.4, color="#555555"))

    #*** 3. Lay out legends and scientific interpretation notes
    types = [
        Line2D([], [], marker="D", ls="none", mfc="#c73e3a", mec="white", label="Model maximum: UTC peak observation available"),
        Line2D([], [], marker="D", ls="none", mfc="none", mec="#c73e3a", label="Model maximum: no usable UTC peak observation"),
        Line2D([], [], marker="o", ls="none", mfc="#d88900", mec="white", label="UTC discharge peak"),
        Line2D([], [], marker="^", ls="none", mfc="#7b4ab5", mec="white", label="UTC water-level peak (reference)"),
    ]
    type_legend = fig.legend(handles=types, loc="center", bbox_to_anchor=(.5,1.55/height),
                            ncol=2, frameon=False, fontsize=8)
    represented = list(dict.fromkeys(aliases.get(row["river_group"], row["river_group"]) for row in records))
    basin_handles = [Line2D([],[],marker="s",ls="none",color=palette.get(group,neutral),
                           label=group if group in palette else f"{group} (unmapped)") for group in represented]
    basin_legend = fig.legend(handles=basin_handles,loc="center",bbox_to_anchor=(.5,1.02/height),
                             ncol=4, frameon=False, fontsize=8, handletextpad=.35, columnspacing=1.4)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    foot = ("Diamond fill indicates observation availability, not model-observation agreement. Bold labels: UTC peak reported. "
            "M no peak time; U timezone unknown; P upstream proxy; N no cell; C context only. "
            "Within-row offsets separate close markers. Edge arrows show actual out-of-view times, not boundary peaks.")
    foot = wrap_figure_text(foot, renderer, (width - .8)*dpi, fontsize=7.5)
    foot_artist = fig.text(.4 / width, .65 / height, foot, ha="left", va="top", fontsize=7.5, color="#555555")
    event_note = settings.get("event_note", "")
    event_artist=fig.text(.4/width,.22/height,wrap_figure_text(event_note,renderer,(width-.8)*dpi,fontsize=8),
                          ha="left", va="bottom", fontsize=8, color="#333333")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    # Verify the physical text columns rather than relying on tight bounding-box cropping.

    #*** 4. Check existing decoration bounds and export
    bounds = fig.bbox
    for artist in [*measured_labels, *note_texts, type_legend, basin_legend, foot_artist, event_artist]:
        box = artist.get_window_extent(renderer)
        if box.x0 < bounds.x0 or box.x1 > bounds.x1 or box.y0 < bounds.y0 or box.y1 > bounds.y1:
            raise ValueError(f"Summary decoration outside fixed canvas: {artist}")
    if max(artist.get_window_extent(renderer).x1 for artist in measured_labels) > ax.bbox.x0 - 8:
        raise ValueError("Location labels overlap the time axis; shorten labels in summary settings")
    if foot_artist.get_window_extent(renderer).y0 <= event_artist.get_window_extent(renderer).y1:
        raise ValueError("Summary footnote overlaps the event note")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=dpi, facecolor="white")
    plt.close(fig)
    print(f"Fig23b: {len(records)} rows; palette={palette_path.name}; unresolved colors={sorted(set(unresolved))}; "
          f"outside-view markers={len(outside)}; display=[{start}, {end}) UTC")
    return {"display_start_utc":settings["display_start_utc"],"display_end_utc":settings["display_end_utc"],
            "rows":len(records), "basin_indicators":basin_rows, "labels":label_rows,
            "unresolved_basin_groups":sorted(set(unresolved)), "outside_view_markers":outside,
            "canvas_inches":[width, height], "time_axis_inches":[left, bottom, plot_width, plot_height],
            "decoration_bounds_checked":True, "marker_row_offsets":{"model_with_observation": .1, "observation": -.1}}


def main() -> None:
    """Read retained analysis CSVs and render the requested figures and display review."""

    #*** 1. Read Shell display settings and saved analysis CSVs
    # Preserve the established CLI description while expanding source documentation.
    parser = argparse.ArgumentParser(description='Render Step 23 model hydrographs and reported flood-timing summary.')
    parser.add_argument("--timeseries-csv", type=Path, required=True)
    parser.add_argument("--comparison-csv", type=Path, required=True)
    parser.add_argument("--hydrographs-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--summary-settings", type=Path,
                        default=Path(__file__).resolve().parents[1] / "metadata/23_timing_figure_settings.json")
    parser.add_argument("--summary-only", action="store_true", help="redraw only Fig23b; preserve Fig23a")
    parser.add_argument("--hydrograph-width", type=float, default=15)
    parser.add_argument("--hydrograph-row-height", type=float, default=3)
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()
    series = read_csv(args.timeseries_csv)
    comparisons = read_csv(args.comparison_csv)

    #*** 2. Render requested figures without repeating peak analysis
    if not args.summary_only:
        plot_hydrographs(series, comparisons, args.hydrographs_output, args.hydrograph_width, args.hydrograph_row_height, args.dpi)
        print(f"Wrote {args.hydrographs_output}")
    review = plot_timing_summary(comparisons, args.summary_output, args.summary_settings)
    # Display metadata is separate from peak-analysis CSVs.
    (args.summary_settings.parent / "23_timing_figure_review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {args.summary_output}")


if __name__ == "__main__":
    main()
