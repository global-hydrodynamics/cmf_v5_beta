# Step 12 ERA5-Land Runoff Preparation — AI Work Report

## Work summary

Reviewed and reorganized Step 12 as a reproducible Tutorial workflow, reusing
the researcher-generated data. The earlier data inspection found 20 raw and
20 converted daily files; the present task did not download, reconvert, or
modify them. Added a Tutorial-local dataset Registry and adjusted Step 12
metadata to reference it. Updated the process so Step 13 owns Input Matrix
preparation/validation and Step 14 owns simulation setup and GOSH script
creation.

## Inputs and retained evidence

- Product Shell: `inp/download_ERA5-Land/tutorial11-Rhine_2021Jul.sh`
- Shared stages: `s01-download.sh`, `s02-convert_CMF_nc.sh`
- Local dataset: `inp/tutorial11-ERA5land-Rhine2021Jul/`
- Step 2 period/domain context and Step 11 Rhine regional map
- ERA5-Land workflow README, Tutorial rules and KG-0019

The Product Shell preserves dataset `tutorial11-ERA5land-Rhine2021Jul`, July
1–20, 2021, requested bounds 2.5–13.5°E and 44.5–53.5°N, hourly TSTEP,
daily download/output grouping, NetCDF and NCPUS=2. The bounds intentionally
extend 0.5° beyond the Step 11 map.

## Registry and Metadata

Created `tutorial/tutorial11-event_evaluation/runoff_dataset.csv` using the
same header/schema as `inp/runoff_datasets.csv`. Its one event-specific row
records the dataset path/pattern, observed NetCDF variable and grid, period,
units, `DROFUNIT`, source and data scope, verification state, and Input Matrix
relationship. It is the specification Registry for Steps 13 and 14. The shared
input Registry was not changed.

Reworked `metadata/12_era5land_runoff.json` as the Step 12 execution record.
It links to the Tutorial Registry and records selected request settings,
processing provenance, file/log counts and checks, the present-but-unvalidated
Step 11 matrix pair, period context, KG-0019, and the Step 13 handoff. Detailed
dataset specification is not repeated as a second Registry.

## Existing dataset checks

Reused the earlier representative-data inspection results: 20 original and
20 converted files cover every requested day; the source and converted files
have 24 hourly timestamps per day and a continuous 480-label sequence. Raw and
converted coordinates match; the observed 0.1° grid centers are longitude
2.5–13.5°E and latitude 53.5–44.5°N. The converted field is float32
`runoff(time,lat,lon)` in mm per timestep with fill `1e20`, shape
(24,91,111). Retained per-day download and conversion logs recorded completion
for all dates. These are structural checks, not independent value-by-value
conversion validation.

Step 12 does not verify the regional Input Matrix. Although
`map/Rhine_15min/inpmat_ERA5land_global.bin` and its `diminfo` exist, their
correctness for this downloaded runoff and map is assigned to Step 13.

## Files changed

- Added `runoff_dataset.csv`.
- Updated `p12-era5land_runoff_preparation.md` to define Registry use and the
  Step 13/14 boundaries.
- Updated `metadata/12_era5land_runoff.json` to link to, rather than duplicate,
  the Registry specification.
- Updated the Step 12 Survey Report and `00_event_evaluation_process.md`.
- Updated the Step 11 handoff references and development history as needed.

No generated NetCDF, raw source, log, Product Shell setting, conversion
algorithm, map, or shared runoff registry row was changed. The Tutorial-local
runoff data remain ignored.

## Step 13/14 handoff and limitations

Step 13 should read the dataset row from `runoff_dataset.csv`, inspect the
actual NetCDF grid, and prepare/validate the map-specific Input Matrix. Step 14
should decide the simulation period, spin-up, forcing coverage and model
settings, then create a GOSH script. Step 15 performs model execution after
setup is complete. Do not infer those conditions from the
acquisition interval. KG-0019 remains unresolved: ERA5-Land 00 UTC represents
the preceding 24-hour accumulation, and conversion first-record/period-boundary
behavior is not scientifically resolved. No CaMa-Flood run or model-observation
comparison was performed.
