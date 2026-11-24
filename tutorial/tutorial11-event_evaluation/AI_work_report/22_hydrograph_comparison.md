# Step 22 — Hydrograph Comparison Work Report

## Inputs and extraction

- Model: `experiment/Rhine2021/o_outflwRhine2021Jul.nc`
- Observations: `observation/stations_data/Qobs_06_2021_st153_63_28.csv`
- Allocation: `metadata/21_gauge_allocation.csv`
- Observation metadata: `metadata/04_discharge_dataset.json`
- Run metadata: `metadata/14_simulation_setup.json`

Ran `bash run_script/s22-extract_hydrograph.sh` from the Tutorial 11 directory after updating its model input to the current Step 14 `experiment/Rhine2021/` directory. The script reads the zero-based `model_row_0based` and `model_col_0based` from Step 21 and indexes `outflw(time,lat,lon)` without reallocating stations. The requested range is `[2021-07-10 00:00, 2021-08-01 00:00)`. It wrote 528 hourly model values and 88 observation values for each of the three stations (1,584 model rows and 264 observation rows total). No values were interpolated, aggregated, or converted.

## Time and unit handling

The model NetCDF reports `time:units="seconds since 2021-07-01 00:00"`, `outflw:units="m3/s"`, and `outflw:cell_methods="time: mean"`. The time reference omits a timezone; the CF convention defaults this to UTC. Model timestamps in the output CSV include `Z` in `datetime_comparison`.

The observation metadata records unknown timezone and unknown unit. Its original CSV labels are preserved exactly in `datetime_original`; `datetime_comparison` stores the same nominal labels without a timezone suffix. Plotting overlays the labels without any conversion and is explicitly provisional. The inherited provider description says six-hour mean with interval-end labels; the NetCDF source has no time bounds or averaging attribute.

## Outputs and checks

- `metadata/22_hydrograph_timeseries.csv` — separate source rows, values, timestamps and unit/time-reference status.
- `metadata/22_hydrograph_comparison_summary.json` — source paths, coordinate/time metadata, series maxima and limitations.
- `figure/f22-hydrograph_comparison.png` — three vertically stacked station panels, covering July 10–31.
- `p22-hydrograph_comparison.md` — reusable Workflow Summary and Agent Prompt.
- `AI_survey_report/22_hydrograph_comparison.md` — qualitative findings and interpretation limits.

Ran `bash plot_script/f22-hydrograph_comparison.sh` and visually inspected the saved image. The three panels use a shared July 10–August 1 axis, hourly model lines and six-hour observation lines with markers. The values and timing were not adjusted. In the expanded interval, model maxima are 8,490.1 m³/s (Lobith, Jul 18 17:00 UTC), 6,465.5 m³/s (Speyer, Jul 18 02:00 UTC), and 6,473.4 m³/s (Maxau, Jul 17 09:00 UTC). Observation maxima at supplied labels are 6,684.746 (Lobith, Jul 18 06:00), 3,957.5 (Speyer, Jul 18 06:00), and 4,214.583 (Maxau, Jul 17 18:00); the observation unit/timezone caveats still apply.

Shell commands completed and the output CSV/JSON/PNG were created. An auxiliary one-off summary command initially used the wrong relative path to `.venv`; rerunning it from the Tutorial root succeeded. No model was run, and no skill metrics were calculated.

## Handoff and open items

The CSV and summary are inputs for later matching design. Observation discharge units and timezone remain unverified, so the overlay cannot establish magnitude agreement or peak-time error. The Step 14 experiment is a cold-start operational run and has its own forcing-time attribution limitation. Formal temporal pairing, unit verification, and quantitative evaluation remain outside Step 22.
