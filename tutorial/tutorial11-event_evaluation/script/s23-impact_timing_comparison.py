#!/usr/bin/env python3
"""Extract report-linked impact hydrographs and compare UTC peak windows.

Inputs: Step01 UTC timing reports, Step21 allocation and hourly model outflw.
Outputs: unique-cell series CSV and report-linked timing-comparison CSV.
Workflow:
    1. Resolve report cells and the half-open model peak-search interval.
    2. Extract finite flows and their signed-value maxima at unique cells.
    3. Compare eligible discharge-peak times with reported windows and export.
Boundary maxima and unresolved/context-only cells are not validated event peaks.
Water-level peaks remain reference context; missing/unknown times are not guessed.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
import re

from netCDF4 import Dataset, num2date
import numpy as np


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read report/allocation rows without changing their recorded scientific fields."""
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def parse_utc(value: str) -> datetime | None:
    """Require an explicit offset and return naive UTC, or None for an empty field."""
    if not value:
        return None
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(text)
    if parsed.utcoffset() is None:
        raise ValueError(f"Expected an explicit UTC offset in timing field: {value}")
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def iso_utc(value: datetime) -> str:
    """Format an already UTC-interpreted datetime with a Z suffix."""
    return value.isoformat(timespec="seconds") + "Z"


def signed_window_lag_hours(peak: datetime, start: datetime, end: datetime) -> tuple[float, bool]:
    """Return signed hours to the nearest window edge, or zero inside [start, end].

    Negative means the model peak precedes the window; positive means it
    follows it. A point window requires equality for an inside match."""
    if start == end:
        lag = (peak - start).total_seconds() / 3600.0
        return lag, lag == 0
    if peak < start:
        return (peak - start).total_seconds() / 3600.0, False
    if peak > end:
        return (peak - end).total_seconds() / 3600.0, False
    return 0.0, True


def select_cell(row: dict[str, str]) -> tuple[int, int, str, str]:
    """Use a confirmed/plausible river cell, otherwise retain geographic context or no cell."""
    status = row.get("river_allocation_status", "")
    river_row, river_col = row.get("river_model_row_0based", ""), row.get("river_model_col_0based", "")
    if status in {"confirmed", "plausible"} and river_row and river_col:
        return int(river_row), int(river_col), row.get("river_allocation_method") or "river_assessment_candidate", status
    geo_row, geo_col = row.get("model_row_0based", ""), row.get("model_col_0based", "")
    if geo_row and geo_col:
        return int(geo_row), int(geo_col), "geographic_cell_context_only", status or "unreviewed"
    return -1, -1, "no_model_cell", status or "unavailable"


def main() -> None:
    """Extract unique-cell flows and qualify report-linked timing-window comparisons."""

    #*** 1. Read the UTC search range and report/allocation contracts
    # Preserve the established CLI description while expanding source documentation.
    parser = argparse.ArgumentParser(description='Extract report-linked impact hydrographs and compare UTC peak windows.')
    parser.add_argument("--tutorial-dir", type=Path, required=True)
    parser.add_argument("--model-netcdf", type=Path, required=True)
    parser.add_argument("--timing-csv", type=Path, required=True)
    parser.add_argument("--allocation-csv", type=Path, required=True)
    parser.add_argument("--timeseries-output", type=Path, required=True)
    parser.add_argument("--comparison-output", type=Path, required=True)
    parser.add_argument("--search-start", default="2021-07-12T00:00:00Z")
    parser.add_argument("--search-end-exclusive", default="2021-07-19T00:00:00Z")
    args = parser.parse_args()

    tutorial = args.tutorial_dir.resolve()
    search_start = parse_utc(args.search_start)
    search_end = parse_utc(args.search_end_exclusive)
    if search_start is None or search_end is None or search_end <= search_start:
        raise ValueError("Model peak search range is invalid")

    timing = read_csv(args.timing_csv)
    allocation_rows = read_csv(args.allocation_csv)
    allocation = {row["report_id"]: row for row in allocation_rows}
    if len(allocation) != len(allocation_rows):
        raise ValueError("Step 21 allocation contains duplicate report_id values")
    timing_ids = [row["report_id"] for row in timing]
    if set(timing_ids) != set(allocation):
        missing = sorted(set(timing_ids) ^ set(allocation))
        raise ValueError(f"Step 01 / Step 21 report_id mismatch: {missing}")

    chosen: dict[str, tuple[int, int, str, str]] = {
        report_id: select_cell(allocation[report_id]) for report_id in timing_ids
    }
    unique_cells = sorted({(r, c) for r, c, _, _ in chosen.values() if r >= 0})
    model_rows: list[dict[str, str]] = []
    peak_by_cell: dict[tuple[int, int], dict[str, object]] = {}

    #*** 2. Extract unique-cell flows and identify finite signed-value maxima
    with Dataset(args.model_netcdf) as ds:
        if "outflw" not in ds.variables or "time" not in ds.variables:
            raise ValueError(f"Expected outflw and time variables in {args.model_netcdf}")
        flow = ds.variables["outflw"]
        time_var = ds.variables["time"]
        if flow.dimensions != ("time", "lat", "lon") or getattr(flow, "units", "") != "m3/s":
            raise ValueError("Expected outflw(time, lat, lon) in m3/s")
        time_units = getattr(time_var, "units", "")
        calendar = getattr(time_var, "calendar", "standard")
        if not time_units:
            raise ValueError("Model time coordinate has no CF units")
        decoded = num2date(time_var[:], units=time_units, calendar=calendar,
                           only_use_cftime_datetimes=False, only_use_python_datetimes=True)
        times = [datetime(value.year, value.month, value.day, value.hour, value.minute, value.second)
                 for value in decoded]
        indexes = [i for i, value in enumerate(times) if search_start <= value.replace(tzinfo=None) < search_end]
        if not indexes:
            raise ValueError("No model output records fall in the requested peak-search period")
        if len(indexes) != len(times) or indexes != list(range(indexes[0], indexes[-1] + 1)):
            # The file may include spin-up before the search period; the filtered
            # window must still be contiguous for a meaningful local maximum.
            if indexes != list(range(indexes[0], indexes[-1] + 1)):
                raise ValueError("Model search-window records are not contiguous")

        for row, col in unique_cells:
            if not (0 <= row < flow.shape[1] and 0 <= col < flow.shape[2]):
                raise ValueError(f"Step 21 allocation cell {(row, col)} is outside model output grid")
            values = np.ma.asarray(flow[indexes, row, col], dtype=np.float64).filled(np.nan)
            finite = np.isfinite(values)
            if not finite.any():
                raise ValueError(f"No finite model outflw values at cell {(row, col)}")
            max_index = int(np.nanargmax(values))
            peak_index = indexes[max_index]
            peak_time = times[peak_index]
            peak_by_cell[(row, col)] = {
                "time": peak_time,
                "value": float(values[max_index]),
                "boundary": max_index in {0, len(indexes) - 1},
            }
            reports_for_cell = [rid for rid, selected in chosen.items()
                                if selected[0:2] == (row, col)]
            group_text = "; ".join(sorted({allocation[rid]["river_group"] for rid in reports_for_cell if allocation[rid]["river_group"]}))
            basis_text = "; ".join(sorted({chosen[rid][2] for rid in reports_for_cell}))
            status_text = "; ".join(sorted({chosen[rid][3] for rid in reports_for_cell}))
            for index, value in zip(indexes, values):
                if np.isfinite(value):
                    model_rows.append({
                        "model_row_0based": str(row), "model_col_0based": str(col),
                        "datetime_utc": iso_utc(times[index]), "outflw_m3s": f"{float(value):.9g}",
                        "river_groups": group_text, "allocation_basis": basis_text,
                        "river_allocation_status": status_text,
                    })

    #*** 3. Qualify timing-window comparisons by data/river support
    comparison_rows: list[dict[str, str]] = []
    for report in timing:
        report_id = report["report_id"]
        assigned = allocation[report_id]
        row, col, basis, river_status = chosen[report_id]
        record: dict[str, str] = {
            "report_id": report_id,
            "location_id": report["location_id"],
            "location_name": report["location_name"],
            "river_group": report["river_group"],
            "model_row_0based": str(row) if row >= 0 else "",
            "model_col_0based": str(col) if col >= 0 else "",
            "geographic_model_row_0based": assigned.get("model_row_0based", ""),
            "geographic_model_col_0based": assigned.get("model_col_0based", ""),
            "model_cell_basis": basis,
            "model_peak_time_utc": "",
            "model_peak_discharge_m3s": "",
            "observed_start_time_utc": report["start_time_utc"],
            "observed_end_time_utc": report["end_time_utc"],
            "time_original": report["time_original"],
            "timezone_original": report["timezone_original"],
            "timing_type": report["timing_type"],
            "confidence": report["confidence"],
            "river_match_status": assigned.get("river_match_status", ""),
            "river_allocation_status": river_status,
            "lag_to_window_hours": "",
            "inside_window_flag": "",
            "comparison_status": "",
            "ai_notes": "",
        }
        if row < 0:
            record["comparison_status"] = "no_model_cell"
            record["ai_notes"] = "No report coordinate and no Step 21 model cell; no time series was inferred."
            comparison_rows.append(record)
            continue

        peak = peak_by_cell[(row, col)]
        peak_time = peak["time"]
        record["model_peak_time_utc"] = iso_utc(peak_time)
        record["model_peak_discharge_m3s"] = f"{peak['value']:.9g}"
        if peak["boundary"]:
            record["comparison_status"] = "model_peak_at_search_boundary"
            record["ai_notes"] = "Search-window maximum occurs at the first or last timestamp; do not call it an event peak."
            comparison_rows.append(record)
            continue
        if river_status in {"not_represented", "unresolved", "not_assessed_missing_coordinates"}:
            record["comparison_status"] = (
                "river_not_represented_context_only" if river_status == "not_represented"
                else "river_match_unresolved_context_only"
            )
            record["ai_notes"] = "The plotted model series is only geographic-cell context, not a local river comparison."
            comparison_rows.append(record)
            continue
        start = parse_utc(report["start_time_utc"])
        end = parse_utc(report["end_time_utc"])
        if start is None or end is None:
            raw_time = report.get("time_original", "")
            has_clock = re.search(r"\b\d{1,2}:\d{2}\b", raw_time) is not None
            timezone_note = report.get("timezone_original", "").casefold()
            if has_clock and ("not stated" in timezone_note or "unknown" in timezone_note):
                record["comparison_status"] = "timezone_unknown"
                record["ai_notes"] = f"Original source time retained but not placed on UTC axis: {raw_time}"
            else:
                record["comparison_status"] = "time_unavailable"
                record["ai_notes"] = "No UTC time or interval is recorded in Step 01."
            comparison_rows.append(record)
            continue
        if report["timing_type"] != "discharge_peak":
            record["comparison_status"] = "water_level_peak_reference_only"
            record["ai_notes"] = "A water-level peak is shown as hydrologic context; lag metrics are reserved for discharge peaks."
            comparison_rows.append(record)
            continue

        lag, inside = signed_window_lag_hours(peak_time, start, end)
        record["lag_to_window_hours"] = f"{lag:.3f}"
        record["inside_window_flag"] = str(inside).lower()
        if river_status == "plausible" or basis == "geographic_cell_context_only":
            record["comparison_status"] = "provisional_river_match"
            record["ai_notes"] = "Time difference is provisional because the river-to-model-cell correspondence is not confirmed."
        else:
            record["comparison_status"] = "compared_discharge_peak"
            record["ai_notes"] = "UTC discharge-peak time comparison at the Step 21 river-assessment cell."
        comparison_rows.append(record)

    for record in comparison_rows:
        if record["model_cell_basis"] == "one_step_upstream_tributary_proxy":
            record["ai_notes"] += (" Evaluation uses an upstream tributary proxy that omits downstream "
                                   "catchment area; it is not the exact local river reach.")

    #*** 4. Write series and report-linked comparison records
    args.timeseries_output.parent.mkdir(parents=True, exist_ok=True)
    with args.timeseries_output.open("w", newline="", encoding="utf-8") as stream:
        fields = ["model_row_0based", "model_col_0based", "datetime_utc", "outflw_m3s",
                  "river_groups", "allocation_basis", "river_allocation_status"]
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(model_rows)
    with args.comparison_output.open("w", newline="", encoding="utf-8") as stream:
        fields = ["report_id", "location_id", "location_name", "river_group",
                  "model_row_0based", "model_col_0based",
                  "geographic_model_row_0based", "geographic_model_col_0based",
                  "model_cell_basis",
                  "model_peak_time_utc", "model_peak_discharge_m3s",
                  "observed_start_time_utc", "observed_end_time_utc", "time_original",
                  "timezone_original", "timing_type",
                  "confidence", "river_match_status", "river_allocation_status",
                  "lag_to_window_hours", "inside_window_flag", "comparison_status", "ai_notes"]
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(comparison_rows)

    print(f"Wrote {args.timeseries_output}: {len(model_rows)} samples at {len(unique_cells)} unique model cells")
    print(f"Wrote {args.comparison_output}: {len(comparison_rows)} report-linked rows")
    print(f"Search window: [{args.search_start}, {args.search_end_exclusive})")
    for cell, peak in sorted(peak_by_cell.items()):
        print(f"cell={cell}: peak={peak['value']:.2f} m3/s at {iso_utc(peak['time'])}; boundary={peak['boundary']}")


if __name__ == "__main__":
    main()
