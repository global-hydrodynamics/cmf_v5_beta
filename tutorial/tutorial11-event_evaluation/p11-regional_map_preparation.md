# p11 — Regional Map Preparation

## Workflow Summary

### Inputs
- `map/glb_15min/` source map and required auxiliary data
- `metadata/02_domain_selection.json`
- Existing local `map/Rhine_15min/` products, if present
- Shared v5 workflows and documentation under `map/tools/`

### Tasks
- Inspect existing map products before running any generator.
- Prepare map-local copies of regionalization, parameter and format-conversion scripts where absent.
- Configure the region from the Step 2 domain and prepare or verify routing, runoff mappings and map formats.
- Record what was newly generated separately from retained outputs and identify unresolved inputs.

### Outputs
- Local `map/Rhine_15min/` regional map and map-local scripts
- `AI_survey_report/11_regional_map_preparation.md`
- `AI_work_report/11_regional_map_preparation.md`
- A reproducible handoff to Step 12 runoff preparation, Step 13 Input Matrix preparation, and Step 14 simulation setup

## Human Instructions

This Step prepares the regional map used by the Rhine event experiment. The
global source map and generated regional products may be outside Git. Inspect
an existing regional map first; reuse valid products and do not overwrite
valuable local outputs without an explicit need. For this event the requested
source is `../../glb_15min/`, with outer bounds WEST/EAST/SOUTH/NORTH of
3.0/13.0/45.0/53.0 degrees. Do not copy the former cell-center candidate
bounds from another event or earlier settings.

## Example AI Agent Prompt

```text
Prepare Step 11, the regional map for this event.

Read the event's Step 2 machine-readable domain, map and map-tools READMEs, and
the target map directory before editing or executing anything. For Rhine 2021
use source `../../glb_15min/` and outer edges WEST=3.0, EAST=13.0, SOUTH=45.0,
NORTH=53.0, at 15 arc-minute resolution.

1. Inspect existing map files and parameters. Reuse matching outputs. Do not
   overwrite or regenerate an existing map automatically.
2. Copy shared `script_region`, `script_params`, and `script_format_conv`
   templates only when missing; preserve existing map-local configuration and
   review differences from the current shared templates.
3. If required products are missing and all inputs/executables are available,
   prepare only those products using documented shared workflows. Keep
   `test-1deg` (ELSE_GPCC climatology) distinct from `ERA5land_global` runoff
   mapping. Do not implement new scientific algorithms or gauge-allocation
   logic. GRDC allocation does not validate the ECMWF gauges.
4. Inspect map dimensions, grid edges, Binary/NetCDF/COG fields, high-resolution
   auxiliary layers, channel/bifurcation/permanent-water/subbasin products and
   runoff mappings. File presence alone is not hydrologic validation.
5. Create/update the Step 11 Survey and Work Reports with evidence, commands
   actually run, retained-versus-new products, blockers and the Step 12 runoff handoff.
   Keep regional map data local unless separate distribution approval exists.
6. Do not run the flood simulation or evaluate model performance in this Step.
   If inputs or tools are unavailable, report the blocker without claiming
   preparation succeeded.
```
