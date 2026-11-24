# p23 — Flood Impact Timing Comparison

> **Current execution (2026-11-24):** Step23 has been rerun using the final
> Step21 allocations, including the reviewed upstream Ahr proxies. CSVs and
> Figures now contain 10 selected cells × 168 hours and all 22 report rows.
> Input/output fingerprints are in `metadata/23_handoff_status.json`.

## Workflow Summary

- **Inputs:** Step 01 reported timing records, Step 21 geographic allocations and reviewed river-assessment candidates, and the Step 14 hourly Rhine `outflw` NetCDF.
- **Tasks:** Extract one time series per distinct selected model cell; search model maxima over July 12–18; compare only source-supported UTC discharge peaks; render hydrograph and timing-summary figures.
- **Outputs:** `metadata/23_impact_model_timeseries.csv`, `metadata/23_impact_timing_comparison.csv`, Figures 23a/23b, Survey Report and Work Report.

## Reusable AI Agent Prompt

Use this workflow for the Rhine 2021 sample after checking the current Tutorial rules and the exact Step 14 output path. Treat the Step 01 timing ledger and Step 21 report-linked allocation as authoritative; do not redetermine event times or reallocate locations.

1. Read `metadata/01_reported_flood_timing.csv`, `metadata/21_impact_location_allocation.csv`, and the model output specified by `metadata/14_simulation_setup.json`. Confirm `outflw(time,lat,lon)`, `m3/s`, CF time units, the output grid shape, and hourly record availability.
2. For `confirmed` or `plausible` Step 21 river assessments, use `river_model_row_0based` and `river_model_col_0based` as the local-river evaluation candidate. Keep `model_row_0based` / `model_col_0based` as the geographic containing-cell result. The final candidate may be direct catmxy or an explicitly corrected upstream tributary proxy; retain `river_allocation_method` and its uncertainty. For `unresolved` or `not_represented`, show the geographic-cell hydrograph only as context; do not score it as local tributary flow. A report with no coordinates has no model series.
3. Deduplicate model extraction by the selected model cell, but retain one comparison row for each `report_id` and `location_id`. Save model samples from `[2021-07-12T00:00:00Z, 2021-07-19T00:00:00Z)` and search the maximum over that full interval. If the maximum is at either search boundary, do not call it an event peak.
4. Preserve `timing_type`, UTC start/end, original time string, original timezone note, and confidence. Do not convert a raw time unless Step 01 already records a source-supported UTC value. Plot unknown-time locations without an observation marker and identify their timing as unavailable; keep unconverted source times in the CSV/report.
5. Plot Figure 23a as one hourly hydrograph per unique selected cell for July 13–16 UTC. Plot Figure 23b as one row per report. Mark reported discharge peaks separately from water-level peaks; water-level peaks are reference information and must not be included in discharge-peak lag metrics.
6. Calculate `inside_window_flag` and signed `lag_to_window_hours` only for a confirmed UTC `discharge_peak` and a model peak not on the search boundary. Keep a computed lag provisional when river-cell correspondence is only plausible. Do not calculate lags for impact reports, unknown timezones, water-level peaks, unresolved/not-represented rivers, or missing model cells.
7. Run `bash s23-impact_timing_comparison.sh`, then `bash f23-impact_timing_comparison.sh`. Inspect both figures for time range, labels, marker meaning, unknown-time handling, and river-allocation caveats. Update the Survey Report, Work Report, this process document and the development log.

No interpolation, temporal aggregation, model rerun, gauge reallocation or skill metrics are part of this exploratory Step.
