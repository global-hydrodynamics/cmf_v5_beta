# Step 12 ERA5-Land Runoff Preparation — AI Work Report

## Work summary

The original Step 12 setup registered the researcher-prepared runoff data and
its 20-day inspection. On 2026-11-24, the local dataset was reinspected after
the researcher extended it through July 31. The 31 raw and 31 converted files
were not downloaded or converted again during this follow-up. Step 12 metadata,
the local registry, and Step 12 documentation now describe the extended
coverage.

## Inputs and retained evidence

- Product Shell: `inp/download_ERA5-Land/tutorial11-Rhine_2021Jul.sh`
- Shared stages: `s01-download.sh`, `s02-convert_CMF_nc.sh`
- Local dataset: `inp/tutorial11-ERA5land-Rhine2021Jul/`
- Step 2 period/domain context and Step 11 Rhine regional map
- ERA5-Land workflow README, Tutorial rules and KG-0019

The Product Shell is configured for dataset `tutorial11-ERA5land-Rhine2021Jul`,
July 1–31, 2021, requested bounds 2.5–13.5°E and 44.5–53.5°N, hourly TSTEP,
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

Reinspected the local files: 31 original and 31 converted files cover every
date July 1–31. All converted files have 24 hourly timestamps; their combined
744 labels are contiguous. The converted NetCDF files share the previously
recorded 0.1° grid centers: longitude
2.5–13.5°E and latitude 53.5–44.5°N. The converted field is float32
`runoff(time,lat,lon)` in mm per timestep with fill `1e20`, shape
(24,91,111). Retained per-day download and conversion logs cover July 1–20
only; per-day logs for July 21–31 were not present. These are structural
checks, not independent value-by-value conversion validation.

Step 12 does not verify the regional Input Matrix. Although
`map/Rhine_15min/inpmat_ERA5land_global.bin` and its `diminfo` exist, their
correctness for this downloaded runoff and map was assigned to Step 13. Step
13 generated and structurally checked the regional
`ERA5land_Rhine2021Jul` matrix. The July extension retains the same 111 × 91
grid, so the spatial matrix was not regenerated. Step 14's log confirms this
matrix was read for the extended run; see the Step 13 Work Report and metadata.

## Files changed

- Added `runoff_dataset.csv`.
- Updated `p12-era5land_runoff_preparation.md` to define Registry use and the
  Step 13/14 boundaries.
- Updated `metadata/12_era5land_runoff.json` to link to, rather than duplicate,
  the Registry specification.
- Updated the Step 12 Survey Report and `README.md`.
- Updated the Step 11 handoff references and development history as needed.

No generated NetCDF, raw source, or log was changed by this follow-up. The
Product Shell period/target and Tutorial-local records were aligned to the
existing local data. The Tutorial-local runoff data remain ignored.

## Step 13/14 handoff and limitations

Step 13 read the dataset row and generated/checked the regional Input Matrix;
its spatial grid remains unchanged. Step 14 ran 2021-07-01 00:00 through
2021-08-01 00:00 exclusive, consuming all 31 daily files with the standard
Rhine `nextxy.nc` map. The run completed 744 steps and wrote its Restart at
the exclusive end. The earlier noedge output is no longer present in the
reused `experiment/Rhine2021/` directory. Step 15 and Step 22 were regenerated
from the extended outputs. Do not infer simulation conditions from the
acquisition interval.
KG-0019 remains unresolved: ERA5-Land 00 UTC represents
the preceding 24-hour accumulation, and conversion first-record/period-boundary
behavior is not scientifically resolved. Step 12 made no model run; the
separate Step 14 run and Step 22 exploratory comparison are recorded in their
own reports.
