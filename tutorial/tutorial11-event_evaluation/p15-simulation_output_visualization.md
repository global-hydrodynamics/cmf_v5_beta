# p15 — Simulation Output Visualization

### How to Use This Workflow

**Rhine 2021:** Keep the current Step 14 experiment and visualization settings
below; provide the entire Markdown file as an attachment or copy its full
content. This workflow consumes retained output and does not rerun the model.

**Another event:** Review the source experiment/output paths, record period,
map/topology, AOI and figure settings in the Step 14/02 handoffs and plotting
Shell. The Rhine names, 744-record period and cold-start statements below are
current-case settings/evidence, not assumed properties of a new simulation.
Verify actual time axes, variable definitions and map/helper compatibility;
retain the signed-peak and layer-aggregation methods. Give the entire updated
file to the agent after prerequisites and scientific choices are established.
Editing this Prompt alone does not adapt the plotting implementation.

The execution block depends on the full file and is not a standalone Prompt.

## Workflow Summary

**Inputs**

- Step 14 hourly `outflw` and `pthflw` NetCDF outputs, located using
  `metadata/14_simulation_setup.json`.
- The `Rhine_15min` map and its network, bifurcation, and elevation products.
- The Step 2 satellite-analysis AOI in `metadata/02_domain_selection.json`.
- The standard `nextxy.nc` network and visualization method from Gallery
  p02-f02b.

**Tasks**

- Inspect the actual NetCDF time axes and calculate signed local maximum-
  absolute discharge values over the retained 744 hourly records (July 1–31).
- Generate and visually inspect the regional direction-aware network map
  (Fig. 15a) and its AOI view (Fig. 15b), using line widths that keep the complete network distinguishable at
  overview scale.
- Save the derived peak values and record the inputs, method, results and
  scientific limits in metadata and reports.

**Outputs**

- `figure/f15a-maximum_discharge-regional.png`
- `figure/f15b-maximum_discharge-aoi.png`
- `experiment/Rhine2021/analysis/maximum_discharge_20210701-20210801.nc`
  (derived, ignored runtime output)
- Step 15 metadata, Survey Report and Work Report.

Both network maps show each main-channel link's signed `outflw` value at its
own time of maximum absolute hourly mean. They independently show each
bifurcation path's local peak. These peaks may occur at different times;
neither figure is a simultaneous flow snapshot or a model skill assessment. The run has no spin-up, and the ERA5-Land timing issue
KG-0019 remains unresolved.

## Human Instructions

After Step 14 has produced the hourly outputs, run the visualization workflow
from this directory:

```sh
bash plot_script/f15-maximum_discharge.sh
```

The script reads input paths and the AOI from Step metadata, saves derived peak
values under the ignored experiment directory, and writes the two figures to
`figure/`. It does not rerun CaMa-Flood. Review is recommended but is not a
program execution gate; missing or inconsistent input files stop the normal
workflow with an error.

## Example AI Agent Prompt

**Current Rhine 2021 configuration:** Event names, paths, periods, geometry
and researcher-selected settings in this block describe this application.
For another event, review and replace them using its own inputs and decisions;
the general methods and limits still apply. Supply the complete file.

```text
Complete Tutorial 11 Step 15 using this prompt and the retained Step 14
outputs. Inspect applicable repository/tutorial rules, Step 14 metadata,
Step 2 AOI metadata, Rhine map files and Gallery p02-f02b method.
Do not rerun CaMa-Flood or change its inputs or outputs.

Read and verify the actual hourly time axes. For each outflw cell, select the
signed value at argmax(abs(outflw)) across valid records; preserve negative
and zero values, and leave all-missing cells missing. For each pthflw path and
hour, first sum signed values over map layers with positive width, then select
the signed sum at the path's maximum absolute value. Do not sum per-layer
maxima. Keep main-channel and bifurcation peak times independent.

Generate Fig. 15a as the direction-aware signed-peak Rhine river network over
the full map extent and Fig. 15b as the same network over the Step 2
satellite-analysis AOI, using the map's 1-minute elevation background. Read
the standard `nextxy.nc` topology specified in Step 14. Use upstream-area-scaled lines that remain visibly distinct across the
full basin at overview scale.
Reuse existing Gallery helpers without using Mekong-specific paths or data.
Record that local peaks are not a simultaneous state and that this cold-start
run does not establish skill. Preserve the no-spin-up and KG-0019 limitations.

Save a compact derived NetCDF under experiment/Rhine2021/analysis/, create
metadata/15_simulation_output_visualization.json and the Step 15 Survey/Work
Reports, update the process and Step 14 handoff, and add a development-log
entry. Visually inspect both figures and perform focused data/geometry checks.
Do not compare observations, calculate performance metrics, publish to the
Visualization Gallery, or modify model code. Commit and push the authorized
Step 15 changes on feature/package-builder.
```
