# ERA5-Land Hourly Runoff Preparation — Survey Report

## Summary

ERA5-Land hourly runoff was selected by the researcher as input for a future
CaMa-Flood event simulation. The hourly product supplies time-varying runoff
around the July 2021 flood. This report covers data preparation only; it does
not report a simulation or model evaluation.

The acquisition dates are **2021-07-01 through 2021-07-20**, selected to retain
a pre-event interval before the initial candidate analysis window of July 10–25.
These periods have separate roles: the core event context is July 13–15; the
July 10–25 window remains the initial analysis candidate; July 1–20 is the
runoff acquisition period; and the model simulation/evaluation dates remain
undecided. A July 1 start does not prove sufficient spin-up. Later evaluation
requires extending the forcing beyond July 20.

The Step 11 Rhine map is 3–13°E, 45–53°N. The requested CDS bounds are
2.5–13.5°E, 44.5–53.5°N, intentionally 0.5° wider on each edge to avoid input
grid correspondence problems at the map boundary. Inspection found actual
coordinate centers at 2.5–13.5°E and 53.5–44.5°N, spaced by 0.1°; derived
outer cell edges are 2.45–13.55°E, 44.45–53.55°N. Requested bounds, centers,
and cell edges are distinct.

## Existing data and registered product

The local data directory contains 20 original daily files and 20 converted
daily files for every date July 1–20. Retained download/conversion logs have
completion/output records for each date. No download or conversion was repeated
for this documentation update.

Each converted file has 24 hourly records with dimensions
`runoff(time,lat,lon) = (24,91,111)`. The sequence spans 480 hourly labels from
2021-07-01 00:00 through 2021-07-20 23:00 UTC, with no duplicate or missing
labels. The field is float32 `runoff` in mm per input timestep, with fill and
missing values `1e20`. The raw ERA5-Land field is `ro` in metres. Daily file
grouping does not average the hourly data. The dataset specification, file pattern, grid, units, conversion factor and
provenance are registered in [Tutorial 11 runoff_dataset.csv](../runoff_dataset.csv).

## Model input and Step 13 responsibility

The Step 11 map has an `ERA5land_global` Input Matrix and `diminfo` pair. Their
presence is recorded as a candidate handoff; Step 12 did not establish that
the mapping is correct for this regional runoff subset. **Step 13 owns the
actual Input Matrix preparation and validation.** It should compare the
registered NetCDF grid to the regional map's required geometry and recreate
the matrix only if needed. Step 14 then decides simulation settings and writes
the reproducible GOSH workflow using the same Tutorial Registry.

The Tutorial-local Registry uses the shared runoff registry's column schema
and is authoritative for this event dataset. It is not synchronized to
`inp/runoff_datasets.csv`; raw/converted event data remain local and ignored.
The separate `metadata/12_era5land_runoff.json` records selected settings,
processing state, checks and handoff and points to the Registry rather than
duplicating the full dataset specification.

## Scientific limitations and next steps

KG-0019 remains open. ERA5-Land valid-time 00 UTC represents an accumulation
for the preceding 24 hours. The converter differences accumulated source
values within UTC dates and keeps the first record by default; the first-value
and period-boundary treatment have not been independently established as
physically complete. No timestamp shift or algorithm change was made.

Step 14 must set a simulation period and verify that forcing covers the full
run and intended evaluation window. It must also use `runoff_dataset.csv` and
the Input Matrix result from Step 13. No model reader, simulation, gauge
matching or flood-skill evaluation was run for Step 12.

See the [Step 12 Prompt](../p12-era5land_runoff_preparation.md),
[Step 12 Metadata](../metadata/12_era5land_runoff.json), and the
[event process](../00_event_evaluation_process.md).
