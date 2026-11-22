# Step 12 ERA5-Land Runoff Preparation — AI Work Report

## Work summary

Inspected the researcher-prepared Tutorial 11 ERA5-Land dataset on
2026-11-23, without downloading, converting, overwriting, or moving data.
Created the reusable Step 12 Prompt, machine-readable metadata, reports and
cross-step documentation. No runoff algorithm, Input Matrix, regional map or
model configuration was changed.

## Inputs and settings

- Product Shell: `inp/download_ERA5-Land/tutorial11-Rhine_2021Jul.sh`
- Shared downloader/converter: `s01-download.sh`, `s02-convert_CMF_nc.sh`
- Dataset root: `inp/tutorial11-ERA5land-Rhine2021Jul/`
- Step 2 domain metadata and Step 11 regional map/Input Matrix
- ERA5-Land workflow README, NetCDF output conventions and KG-0019

The shell settings are dataset `tutorial11-ERA5land-Rhine2021Jul`, dates
2021-07-01 through 2021-07-20 inclusive, requested bounds 2.5–13.5°E and
44.5–53.5°N, hourly timestep, daily source/output grouping, NetCDF and two
workers. These settings were preserved. The requested bounds extend 0.5° past
the Step 11 model-map outer edges on each side.

## Existing data and checks

The local dataset contained 20 source files named
`original/ERA5-Land_runoff_YYYYMMDD.nc` and 20 converted files named
`runoff_YYYYMMDD.nc`; all dates from July 1 through July 20 were present.
Retained download logs recorded completion for 20/20 dates, and conversion
logs recorded output writes for 20/20 dates. Their run IDs and files are
ignored local evidence.

Using the repository Python environment and NetCDF4, inspected the source
variable and converted NetCDF structure. Source files contain `ro` in metres
with dimensions `(valid_time=24, latitude=91, longitude=111)`. Converted files
contain float32 `runoff(time,lat,lon)` in millimetres, with dimensions
`(24,91,111)`, `_FillValue=missing_value=1e20`, and a long name describing
runoff accumulated over each input timestep. All 20 converted files share
identical coordinate arrays. Longitude centers are 2.5 through 13.5°E at
0.1° increasing; latitude centers are 53.5 through 44.5°N at 0.1° decreasing.
The derived outer cell edges are 2.45–13.55°E and 44.45–53.55°N.

Both the raw and converted timestamps form one strictly continuous hourly
sequence of 480 labels, 2021-07-01 00:00 through 2021-07-20 23:00. Each date has 24 records, and the raw/converted coordinate arrays match.
The observed converted value range is 0–71.4271 mm per record; each daily file
has 16,392 masked values. These are structural and descriptive checks, not an
independent numerical reconstruction or hydrological validation.

The retained `runoff_info_CaMaFlood.txt` reports `LINPCDF=.TRUE.`,
`CROFFREQ=DAY`, `CVNROF=runoff`, `CVNTIME=time`, `IFRQ_INP=1`, and
`DROFUNIT=3600000`. The regional map's `diminfo_ERA5land_global.txt` and
`inpmat_ERA5land_global.bin` are present. The downloaded coordinates match the
0.1° global ERA5-Land center lattice and N-to-S latitude order. The matrix was
not regenerated or read/validated cell by cell.

## Files changed

- Added `tutorial/tutorial11-event_evaluation/p12-era5land_runoff_preparation.md`.
- Added `tutorial/tutorial11-event_evaluation/metadata/12_era5land_runoff.json`.
- Added Step 12 Survey and Work Reports.
- Updated `metadata/02_domain_selection.json` to retain the initial candidate
  analysis window and separately record the researcher-selected runoff period
  and requested area.
- Updated the event process to identify Step 12 as runoff preparation and
  move model setup/simulation to Step 13, matching to Step 14, and evaluation
  to Step 15.
- Updated Step 11 handoff text, the ERA5-Land workflow README and the Rhine
  Product Shell's stale Japan description.
- Recorded the work in the Tutorial development log and repository task status.

The data directory, originals, converted NetCDF, logs and generated info file
remain ignored and were not added to Git. The event-specific dataset was not
added to `inp/runoff_datasets.csv`.

## Limits and unresolved matters

KG-0019 remains open: the 00 UTC source accumulation represents the preceding
24-hour interval, while the converter's daily first-record handling and
period-boundary coverage have not been independently verified. The July 1
start is not proof of sufficient spin-up. No CaMa-Flood reader, map-cell runoff
mapping or simulation was exercised. Model simulation dates remain undecided;
forcing must be extended for evaluation beyond July 20.

## Step 13 handoff

Use `inp/tutorial11-ERA5land-Rhine2021Jul/runoff_YYYYMMDD.nc` as the forcing
candidate and pair it with `map/Rhine_15min/inpmat_ERA5land_global.bin` and
`diminfo_ERA5land_global.txt`. Confirm Step 13 run dates, forcing coverage,
`DROFUNIT`, timestep and NetCDF input settings from the actual configuration.
Keep source/raw files for provenance and repeat conversion only when needed.
