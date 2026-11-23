# p22 — Model–Observation Hydrograph Comparison

## Workflow Summary

- **Inputs:** Step 21 gauge allocation; Step 14 hourly `outflw`; Step 4 supplied six-hour discharge observations and metadata.
- **Tasks:** Extract values at the already allocated model cells for 2021-07-10 through 2021-07-31 inclusive (end-exclusive boundary 2021-08-01 00:00); preserve native time sampling and units; create a three-panel hydrograph Figure and document uncertainty.
- **Outputs:** `metadata/22_hydrograph_timeseries.csv`, `metadata/22_hydrograph_comparison_summary.json`, `figure/f22-hydrograph_comparison.png`, plus Survey and Work Reports.

## Reusable AI Agent Prompt

Use this workflow for the Rhine 2021 sample only after checking the current Step 21 allocation and the referenced files. Step 21's allocation is authoritative; do not search for or reassign gauges.

1. Read `metadata/21_gauge_allocation.csv`, `metadata/04_discharge_dataset.json`, `metadata/14_simulation_setup.json`, the supplied observation CSV and NetCDF, and the Step 14 `outflw` file identified by its metadata. Confirm the current paths before execution.
2. Extract model `outflw(time,lat,lon)` from each allocated `model_row_0based`, `model_col_0based` cell. The CSV indices are zero-based and map to the `(lat,lon)` array order. Keep hourly model records and the source observation timestamps at six-hour cadence; do not interpolate, average, or pair samples.
3. Inspect the time and variable metadata. Use the model CF time convention as documented. Keep observation timestamps as supplied because their timezone is not declared. Do not convert or offset observations to align peaks. Retain the source unit information; do not assume the observation unit equals the model's.
4. Create a three-row shared-time-axis Figure for Lobith/153, Speyer/63, and Maxau/28 for July 10–31, with the plotted axis ending at the exclusive boundary August 1 00:00. Visually inspect it. Clearly label any unresolved time or unit interpretation and describe the overlay as provisional when appropriate.
5. Save the extracted rows and a JSON summary for later work. Write a qualitative Survey Report, a reproducible Work Report, and update `00_event_evaluation_process.md`. Do not calculate skill metrics in this Step.
6. Human review is recommended but not an execution gate. Preserve the evidence and uncertainties so the next Step can decide how to establish formal temporal/variable matching.

Run the extraction and plotting entry points from this directory:

```sh
bash s22-extract_hydrograph.sh
bash f22-hydrograph_comparison.sh
```

The model and observation records remain separate in the CSV. `datetime_comparison` is a plotting coordinate: model entries carry `Z` (UTC under the CF time convention); observation entries retain their unqualified source labels. The Figure overlays those nominal labels without applying a timezone conversion.
