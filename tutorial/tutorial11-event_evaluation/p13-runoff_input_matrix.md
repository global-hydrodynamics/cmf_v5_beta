# p13 — Runoff Input Matrix Preparation

### How to Use This Workflow

**Rhine 2021:** Keep the current regional map, dataset and Input Matrix
settings below; provide the entire Markdown file as an attachment or copy its
full content. Inspect the actual inputs as the existing procedure requires.

**Another event:** Review the event map/dataset paths, matrix tag and wrapper,
input-grid dimensions/order/edges and representative sites in the current-event
instructions below. Derive geometry from the new actual inputs rather than
copying Rhine numbers. Verify the generator and auxiliary-map compatibility;
scientific implementation and runoff conversion remain unchanged. Give the
entire updated file to the agent after the required inputs and decisions are
established. Prompt edits alone do not adapt a map-specific matrix or wrapper.

The execution block requires the full document, including Interpretation and
execution boundary; it is not a standalone Prompt. Existing Rhine availability
is retained example context, not a new-event completion statement.

## Workflow Summary

### Inputs
- Step 11 regional model map: `map/Rhine_15min/`
- Step 12 dataset row: `runoff_dataset.csv`
- Step 12 execution record: `metadata/12_era5land_runoff.json`
- Local ERA5-Land files under `inp/tutorial11-ERA5land-Rhine2021Jul/`
- Shared generator: `map/tools/code/param_inpmat_generate.py`

### Tasks
- Verify the actual runoff NetCDF grid and regional map dimensions/bounds.
- Keep the regional input grid distinct from the global `ERA5land_global` grid.
- Run the shared NetCDF-first generator with the Rhine regional settings below; the map-local `i01` example is global and is not suitable for this subset.
- Inspect the generated `diminfo` and matrix layout, bounds and indices.
- Record outputs, evidence, limitations and the Step 14 handoff.

### Outputs
- `map/Rhine_15min/inpmat_ERA5land_Rhine2021Jul.nc` (local NetCDF map data)
- `map/Rhine_15min/diminfo_ERA5land_Rhine2021Jul.nml` (local Namelist metadata)
- Reproduction command using the shared generator (below)
- `metadata/13_runoff_input_matrix.json`
- `AI_survey_report/13_runoff_input_matrix.md`
- `AI_work_report/13_runoff_input_matrix.md`

## Human Instructions

For this Rhine sample, the researcher has selected the July 1–31, 2021 hourly
ERA5-Land dataset. The regional map and runoff NetCDF are already available
locally. The current NetCDF matrix pair listed below may also be retained locally;
inspect and reuse it if it passes the current structural checks instead of
regenerating it automatically. Ask the agent to inspect those actual inputs and use the Tutorial-local
`runoff_dataset.csv` as the dataset specification. The existing global
`ERA5land_global` matrix is for a 3600 × 1801 grid and must not be reused for the
111 × 91 regional subset merely because both use 0.1° spacing.

The current map interface is `params.nml`, `1min/location.csv`, and
`1min/1min.catmxy.nc` (`catmxx` and `catmyy` on `(lat, lon)`, one-based x/y).
The map-local `1min/` layer is the high-resolution catchment assignment used
by the shared Python generator. The settings must use the runoff **cell edges**
(2.45–13.55°E, 44.45–53.55°N), derived from the inspected coordinate centers;
they are not the requested-download bounds or the first/last cell centers.

## Example AI Agent Prompt

**Current Rhine 2021 configuration:** Event names, paths, periods, geometry
and researcher-selected settings in this block describe this application.
For another event, review and replace them using its own inputs and decisions;
the general methods and limits still apply. Supply the complete file.

```text
Complete Tutorial 11 Step 13: prepare and validate the Rhine regional runoff
Input Matrix. The current pair may already exist locally; inspect it first,
reuse it if it passes the checks, and do not claim it was regenerated. Read the repository, map, input and Tutorial instructions, the
preprocessing conventions, the map-tool documentation, the Step 11 map README,
Step 12 Prompt/metadata, and `runoff_dataset.csv`.

Inspect the actual regional map and converted NetCDF files before choosing any
settings. Do not trust a registry or prior report instead of checking the
inputs. The Step 12 regional dataset is 111 × 91 at 0.1° with longitude centers
2.5–13.5°E and north-to-south latitude centers 53.5–44.5°N. Derive the
cell-edge bounds from the actual coordinates. The Rhine base map is 40 × 32
at 0.25° with outer edges 3–13°E and 45–53°N. Confirm these values from
`params.nml`, `1min/location.csv` and the actual NetCDF.

The global `ERA5land_global` pair uses 3600 × 1801 input cells and is not the
matrix for this regional subset. Choose a distinct `ROFFTAG` and use the existing
map-local 1-minute catchment NetCDF. Do not repurpose
`map/Rhine_15min/script_params/i01-inpmat_ERA5land.sh`; it configures the
global runoff grid. Run the shared Python generator from the repository root
with these current event-specific settings (change only after inspecting another
event's input grid and map):

```sh
.venv/bin/python map/tools/code/param_inpmat_generate.py 1min 0.1 2.45 13.55 53.55 44.45 NtoS diminfo_ERA5land_Rhine2021Jul.nml inpmat_ERA5land_Rhine2021Jul.nc --map-dir map/Rhine_15min
```

The generator reads `location.csv` and `catmxx/catmyy` from the map, writes the
paired NetCDF matrix and DIMINFO under the map root, and defaults to NetCDF.
Do not select the legacy `--map-format binary` mode or change the generator implementation.

Read the generated `diminfo_ERA5land_Rhine2021Jul.nml` file verbatim. Explain its fields and distinguish
what it records (model and input dimensions, maximum contribution count, map
edges, and matrix filename) from input-grid spacing, input-grid cell edges and
latitude order, which must be read from the generator settings and actual
NetCDF/Registry. Check matrix size against the model dimensions, record count
and numeric type; ensure all contributing one-based input indices are within
111 × 91 and every modeled river cell has valid input coverage. Inspect a few
representative Rhine mainstem cells and document that one catchment may receive
runoff contributions from multiple input cells.

Write `metadata/13_runoff_input_matrix.json`, the Survey Report and Work Report.
Update the process, map README and direct Step 12 handoffs as needed. Keep the map and matrix data outside Git. Track Tutorial documentation and any
small Tutorial-owned reproducibility script only when one is introduced. Do not decide simulation dates, write a GOSH script,
run CaMa-Flood, change runoff conversion, or modify the shared matrix code.
Record only checks actually completed and hand the paired matrix/diminfo plus
Registry and Step 12 metadata to Step 14.
```

## Interpretation and execution boundary

`ROFFTAG` identifies the spatial grid/mapping pair, not the runoff period. A
matrix can be reused only with the same input grid geometry/order and the same
CaMa-Flood map. Step 13 prepares the map-to-runoff correspondence; it does not
validate runoff timing, settle the simulation period, or prove that the model
reader consumes the files correctly in a full simulation. KG-0019 remains open.
