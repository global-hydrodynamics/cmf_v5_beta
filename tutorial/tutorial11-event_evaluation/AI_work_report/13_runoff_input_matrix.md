# Step 13 Runoff Input Matrix — AI Work Report

## Inputs and decisions

- Branch: `feature/package-builder`.
- Dataset registry: `runoff_dataset.csv`, ID `tutorial11-ERA5land-Rhine2021Jul`.
- Converted NetCDF inputs: `inp/tutorial11-ERA5land-Rhine2021Jul/runoff_YYYYMMDD.nc`.
- Map: `map/Rhine_15min/`; base grid 40 × 32, 0.25°, outer edges 3–13°E and 45–53°N.
- High-resolution catchment mapping: `map/Rhine_15min/1min/`, 600 × 480, same outer edges.
- Regional runoff grid: 111 × 91, 0.1°, center coordinates 2.5–13.5°E and 53.5–44.5°N north-to-south; derived outer edges 2.45–13.55°E and 44.45–53.55°N.

Selected `ROFFTAG=ERA5land_Rhine2021Jul`, distinct from the global grid tag.
The input bounds supplied to the generator are cell edges rather than centers.
The shared generator and conversion algorithms were not modified.

## Execution

Built the existing shared parameter executables:

```sh
make -C map/tools/code param
```

This invoked the Makefile's `params` target, including
`param_inpmat_generate`. Ran the new map-local wrapper:

```sh
./map/Rhine_15min/script_params/s03-generate_inpmat-rhine.sh
```

The command exited 0 and reported `nxin=111`, `nyin=91`, `input_num_max=30`.
It used the existing `1min/1min.catmxy.bin` and `1min/1min.grdare.bin`.

## Generated outputs

- `map/Rhine_15min/inpmat_ERA5land_Rhine2021Jul.bin` — 460,800 bytes.
- `map/Rhine_15min/diminfo_ERA5land_Rhine2021Jul.txt` — 322 bytes.
- Actual diminfo contents are transcribed and explained line by line in the
  [Survey Report](../AI_survey_report/13_runoff_input_matrix.md).
- Both generated map products are excluded by `map/.gitignore`; the small
  reproducible wrapper is Git-tracked.

## Checks completed

- Inspected `params.txt`, `1min/location.txt`, the generated descriptor and
  actual NetCDF coordinate arrays from July 1 and July 20; the two NetCDF grids
  match at 111 × 91 and 0.1° with north-to-south latitude.
- Confirmed the descriptor records model dimensions/outer edges and input
  dimensions. Input resolution, input edges and row order are from the wrapper
  and NetCDF, not fields stored in diminfo.
- Confirmed matrix byte size against 90 records of 40 × 32 32-bit values.
- Parsed the binary x-index, y-index and area planes using the Fortran source
  record order. Every one of 1,245 active river-network cells has contributions;
  all 16,963 positive-area pairs use one-based indices within 111 × 91, with
  finite positive areas. The remaining 35 model cells have no contribution.
- Checked representative Rhine network cells near Basel, Mainz, Cologne and
  Lobith. Each has valid mapped input cells. Their largest-area input cell can
  be offset from the unit-catchment outlet because the matrix aggregates
  high-resolution catchment pixels by runoff cell.
- `sh -n` passed for the new wrapper; `git diff --check` is clean.

## Limits and Step 14 handoff

No CaMa-Flood reader or simulation was run. Structural matrix checks do not
prove model runtime behavior or resolve KG-0019 (ERA5-Land time attribution and
converter boundary treatment). Step 14 should use this regional matrix/diminfo
pair with the Tutorial Registry, choose experiment/spin-up dates, verify forcing
coverage and runtime settings, and prepare a reproducible GOSH script. The
simulation period remains undecided here.


The subsequent Step 14 cold-start run consumed this regional matrix and
completed. Its experiment settings, generated outputs and operational checks
are recorded in `metadata/14_simulation_setup.json` and
`AI_work_report/14_simulation_setup.md`; that run does not resolve KG-0019.
