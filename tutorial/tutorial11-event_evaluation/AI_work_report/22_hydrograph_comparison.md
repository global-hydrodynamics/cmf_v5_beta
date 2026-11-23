# Step 22 — Hydrograph Comparison Work Report

## Inputs and extraction

- Model: `experiment/Rhine2021-nextxy/o_outflwRhine2021Jul.nc`
- Observations: `observation/stations_data/Qobs_06_2021_st153_63_28.csv`
- Allocation: `metadata/21_gauge_allocation.csv`
- Observation metadata: `metadata/04_discharge_dataset.json`
- Run metadata: `metadata/14_simulation_setup.json`

Ran `bash s22-extract_hydrograph.sh` from the Tutorial 11 directory. The script reads the zero-based `model_row_0based` and `model_col_0based` from Step 21 and indexes `outflw(time,lat,lon)` without reallocating stations. The requested range is `[2021-07-12 00:00, 2021-07-17 00:00)`. It wrote 120 hourly model values and 20 observation values for each of the three stations (360 model rows and 60 observation rows total). No values were interpolated, aggregated, or converted.

## Time and unit handling

The model NetCDF reports `time:units="seconds since 2021-07-01 00:00"`, `outflw:units="m3/s"`, and `outflw:cell_methods="time: mean"`. The time reference omits a timezone; the CF convention defaults this to UTC. Model timestamps in the output CSV include `Z` in `datetime_comparison`.

The observation metadata records unknown timezone and unknown unit. Its original CSV labels are preserved exactly in `datetime_original`; `datetime_comparison` stores the same nominal labels without a timezone suffix. Plotting overlays the labels without any conversion and is explicitly provisional. The inherited provider description says six-hour mean with interval-end labels; the NetCDF source has no time bounds or averaging attribute.

## Outputs and checks

- `metadata/22_hydrograph_timeseries.csv` — separate source rows, values, timestamps and unit/time-reference status.
- `metadata/22_hydrograph_comparison_summary.json` — source paths, coordinate/time metadata, series maxima and limitations.
- `figure/f22-hydrograph_comparison.png` — three vertically stacked station panels.
- `p22-hydrograph_comparison.md` — reusable Workflow Summary and Agent Prompt.
- `AI_survey_report/22_hydrograph_comparison.md` — qualitative findings and interpretation limits.

Ran `bash f22-hydrograph_comparison.sh` and visually inspected the saved image. The three panels use a shared July 12–17 axis, hourly model lines and six-hour observation lines with markers. The values and timing were not adjusted. The shown maxima are window-edge maxima: each model maximum is at Jul 16 23:00 UTC; the observation maxima are at the Jul 16 18:00 source label.

Shell commands completed and the output CSV/JSON/PNG were created. An auxiliary one-off summary command initially used the wrong relative path to `.venv`; rerunning it from the Tutorial root succeeded. No model was run, and no skill metrics were calculated.

## Handoff and open items

The CSV and summary are inputs for later matching design. Observation discharge units and timezone remain unverified, so the overlay cannot establish magnitude agreement or peak-time error. The Step 14 experiment is a cold-start operational run and has its own forcing-time attribution limitation. Formal temporal pairing, unit verification, and quantitative evaluation remain outside Step 22.
