# p11 Regional Map Preparation — AI Work Report

## Work summary

On 2026-11-23, inspected the existing local Rhine regional map and its retained
workflow copies against the Tutorial 11 Step 2 domain. Reused the matching map
products; no regionalization, parameter calculation, NetCDF/COG conversion,
data download, or model execution was run for this Step.

## Inputs inspected

- `tutorial/tutorial11-event_evaluation/metadata/02_domain_selection.json`
- `map/glb_15min/` metadata and available local source data
- `map/Rhine_15min/params.txt`, `region_info.txt`, base Binary products,
  `1min/`, `netcdf/`, `1min_nc/`, and `COG/`
- Map-local scripts and READMEs under `script_region/`, `script_params/`, and
  `script_format_conv/`
- Shared templates and guidance under `map/tools/`
- Existing `map/.gitignore`

## Domain and retained products

The regionalization settings specify `SOURCE="../../glb_15min/"`,
WEST=3.0, EAST=13.0, SOUTH=45.0, NORTH=53.0. `params.txt` reports NX=40,
NY=32, 0.25° spacing, and those exact outer edges. The 1-minute auxiliary
location metadata reports 600 × 480 cells, 1/60° spacing, same edges.

Retained products include the core routing/network and terrain/floodplain
Binary fields; `bifprm.csv`, `bifbsn.bin`, and `bifcol.bin`; channel parameter
files including `outclm.bin`, `rivwth.bin`, `rivhgt.bin`, `rivman.bin`,
`rivhgt_inf.bin`, and `rivwth_merit.bin`; `prmwat.bin`; runoff mapping and
matching diminfo files for both `test-1deg` and `ERA5land_global`;
`subbsn-sample.bin`/`subcol-sample.bin`; `GRDC_alloc.txt`; base NetCDF files;
high-resolution NetCDF/COG products; and 1-minute auxiliary Binary data.

The two matrix tags were not merged: `test-1deg` refers to the global
ELSE_GPCC climatology grid and its `map/data/ELSE_GPCC_clm-1981-2010.one`
channel input; `ERA5land_global` is the separate ERA5-Land runoff-grid
mapping. The retained channel script uses `test-1deg`, and the bifurcation
script uses five layers. The subbasin example thresholds are 30,000 and
5,000 km². `GRDC_alloc.txt` is not ECMWF gauge correspondence validation.

The existing map-local `s01-regional_map.sh` matches the current shared
regionalization workflow apart from its map-specific source and bounds. The
inspected parameter and format-conversion scripts match their current shared
counterparts. No script configuration was regenerated or replaced.

## Actions and checks actually performed

- Read the applicable repository, map and Tutorial 11 instructions and the
  relevant workflow documentation.
- Read the Step 2 domain JSON and compared it with the regionalization shell
  settings, `region_info.txt`, `params.txt`, and 1-minute `location.txt`.
- Checked presence and byte sizes of representative required Binary files,
  both runoff matrices and diminfo files, parameter products, subbasin and
  GRDC allocation products.
- Read representative NetCDF metadata: 40 × 32 base dimensions with 10
  floodplain layers; bifurcation metadata has 20 paths and five layers.
- Read representative COG metadata using the repository Python environment:
  EPSG:4326, base 40 × 32 at 0.25°, and 1-minute 600 × 480 at 1/60°, all over
  3–13°E and 45–53°N.
- Ran `sh -n` over the map-local regionalization, parameter and format
  conversion scripts; syntax checks passed.
- Used `git check-ignore` to confirm regional Binary, NetCDF, COG, 1-minute
  data and `params.txt` are ignored, while the map README and map-local scripts
  are not ignored.
- Reviewed `git status` to distinguish this Step's files from pre-existing
  Tutorial 11 Step 2 changes and the unrelated untracked
  `inp/download_ERA5-Land/tutorial11-Rhine_2021Jul.sh`; those existing files
  were preserved and not included in these reports.

## Files updated for this Step

- `tutorial/tutorial11-event_evaluation/p11-regional_map_preparation.md`
- `tutorial/tutorial11-event_evaluation/AI_survey_report/11_regional_map_preparation.md`
- `tutorial/tutorial11-event_evaluation/AI_work_report/11_regional_map_preparation.md`
- `tutorial/tutorial11-event_evaluation/00_event_evaluation_process.md`
- `map/Rhine_15min/README.md`
- `map/.gitignore`
- `tutorial/tutorial11-event_evaluation/development_log/development_log.md`

The data products under `map/Rhine_15min/` were not added to Git. Existing
Step 2 file edits and the unrelated untracked input script were not altered by
this Step.

## Step 12 runoff handoff

Use `map/Rhine_15min/` as the available candidate regional map. Its source and
outer edges, resolution and dimensions are recorded above. `test-1deg` and
`ERA5land_global` matrix/diminfo pairs are separate available inputs. Before a
run, Step 12 prepares the ERA5-Land forcing; Step 13 must verify its Input Matrix; Step 14 must define simulation dates, initialization,
confirm routing-group and boundary scope, and configure the model. No model
simulation or performance evaluation was performed in this Step.

## Limits

This was a retained-product inspection. It did not establish the full
provenance of every output, regenerate products, compare every binary value to
the global source, validate hydrologic completeness, or test a model run.
The status of existing map outputs for Step 13 matrix use and Step 14 simulation
configuration remains conditional on those later checks.
