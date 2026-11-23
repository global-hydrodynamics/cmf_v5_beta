# p15 — Simulation Output Visualization

## Workflow Summary

**Inputs**

- Step 14 hourly `outflw` and `pthflw` NetCDF outputs, located using
  `metadata/14_simulation_setup.json`.
- The `Rhine_15min` map and its network, bifurcation, and elevation products.
- The Step 2 satellite-analysis AOI in `metadata/02_domain_selection.json`.
- The standard `nextxy.nc` network and visualization methods from Gallery
  p02-f01a and p02-f02b.

**Tasks**

- Inspect the actual NetCDF time axes and calculate signed local maximum-
  absolute discharge values over the retained 480 hourly records.
- Generate and visually inspect the native-grid regional raster (Fig. 15a)
  and direction-aware network map in the AOI (Fig. 15b).
- Save the derived peak values and record the inputs, method, results and
  scientific limits in metadata and reports.

**Outputs**

- `figure/f15a-maximum_discharge-regional.png`
- `figure/f15b-maximum_discharge-aoi.png`
- `experiment/Rhine2021-nextxy/analysis/maximum_discharge_20210701-20210720.nc`
  (derived, ignored runtime output)
- Step 15 metadata, Survey Report and Work Report.

Fig. 15a shows each native map cell's signed `outflw` value at its own time
of maximum absolute hourly mean. Fig. 15b shows each main-channel link's
corresponding cell peak and each bifurcation path's local peak. These peaks
may occur at different times; neither figure is a simultaneous flow snapshot
or a model skill assessment. The run has no spin-up, and the ERA5-Land timing issue
KG-0019 remains unresolved.

## Human Instructions

After Step 14 has produced the hourly outputs, run the visualization workflow
from this directory:

```sh
bash f15-maximum_discharge.sh
```

The script reads input paths and the AOI from Step metadata, saves derived peak
values under the ignored experiment directory, and writes the two figures to
`figure/`. It does not rerun CaMa-Flood. Review is recommended but is not a
program execution gate; missing or inconsistent input files stop the normal
workflow with an error.

## Example AI Agent Prompt

```text
Complete Tutorial 11 Step 15 using this prompt and the retained Step 14
outputs. Inspect applicable repository/tutorial rules, Step 14 metadata,
Step 2 AOI metadata, Rhine map files and Gallery p02-f01a/p02-f02b methods.
Do not rerun CaMa-Flood or change its inputs or outputs.

Read and verify the actual hourly time axes. For each outflw cell, select the
signed value at argmax(abs(outflw)) across valid records; preserve negative
and zero values, and leave all-missing cells missing. For each pthflw path and
hour, first sum signed values over map layers with positive width, then select
the signed sum at the path's maximum absolute value. Do not sum per-layer
maxima. Keep main-channel and bifurcation peak times independent.

Generate Fig. 15a as the native 40 × 32 signed-peak `outflw` raster over the
full map extent, following Gallery p02-f01a without interpolation and with
missing cells white. Generate Fig. 15b as the direction-aware signed-peak
network over the Step 2 AOI, using the map's 1-minute elevation background.
Read the standard `nextxy.nc` topology specified in Step 14 and preserve the
p02-f02b width, flow-direction and bifurcation-style rules. Reuse existing
Gallery helpers without using Mekong-specific paths or data.
Record that local peaks are not a simultaneous state and that this cold-start
run does not establish skill. Preserve the no-spin-up and KG-0019 limitations.

Save a compact derived NetCDF under experiment/Rhine2021-nextxy/analysis/, create
metadata/15_simulation_output_visualization.json and the Step 15 Survey/Work
Reports, update the process and Step 14 handoff, and add a development-log
entry. Visually inspect both figures and perform focused data/geometry checks.
Do not compare observations, calculate performance metrics, publish to the
Visualization Gallery, or modify model code. Commit and push the authorized
Step 15 changes on feature/package-builder.
```
