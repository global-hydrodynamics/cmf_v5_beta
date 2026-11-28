# Step 15 — Simulation Output Visualization Work Report

## Current 31-day visualization (2026-11-24)

Regenerated Fig. 15a and Fig. 15b from the retained Step 14 standard-
`nextxy` outputs in `experiment/Rhine2021/`. The source `outflw` and
`pthflw` files each contain 744 hourly records for the interval
`[2021-07-01 00:00, 2021-08-01 00:00)`, with labels from July 1 01:00 through
August 1 00:00 UTC. No model rerun was performed for Step 15.

The derived file is
`experiment/Rhine2021/analysis/maximum_discharge_20210701-20210801.nc`
(file size recorded in `metadata/15_simulation_output_visualization.json`).
The regenerated maps use the standard `nextxy.nc` network. The full-period
checks found 926,280 valid `outflw` values, 35 all-missing cells, and 1,245
valid cell peaks. Signed peak range is −1,095.38 to 11,592.53 m³/s; 11 cell
peaks are negative. There are 20 `pthflw` paths with active width, including
7 channel-bifurcation and 13 overland-only paths; their signed peak range is
−202.81 to 2,373.30 m³/s, with 4 negative peaks.

Both regenerated figures were opened and visually inspected. The regional
network lines remain visible at full-basin scale, and the AOI layout and
legend are readable. The peaks are local maxima at potentially different
times and do not depict a simultaneous state.

## Historical 20-day run record

The original 2026-11-14 visualization used the then-current Step 14 files
`experiment/Rhine2021-nextxy/o_outflwRhine2021Jul.nc` and
`o_pthflwRhine2021Jul.nc`, resolved through
`metadata/14_simulation_setup.json`. The output map is `Rhine_15min`, 40 × 32,
with bounds 3–13°E and 45–53°N. The AOI was read from Step 2 metadata as
4–8°E and 49–52°N.

Both historical NetCDF files contain 480 hourly records on identical 3,600-second
intervals. Output labels run from 2021-07-01 01:00 UTC through 2021-07-21
00:00 UTC, representing the requested start-exclusive hourly means through
the exclusive run end. `outflw` is `time,lat,lon`; `pthflw` is
`time,NPTHLEV,NPTHOUT`; both are labeled m³/s and `time: mean`.

For `outflw`, each map cell stores the signed record selected by
`argmax(abs(outflw))`; missing records are excluded, zero is valid, and a cell
with no valid values remains missing. For `pthflw`, signed values over
positive-width layers are summed at each hour before selecting the path's
maximum absolute signed sum. Main-channel and bifurcation peaks are selected
independently. The derived compressed NetCDF contains peak values, peak times
and source record indices, plus path/layer and endpoint metadata.

## Execution and outputs

From `tutorial/tutorial11-event_evaluation/`:

```sh
bash plot_script/f15-maximum_discharge.sh
```

The script reuses Gallery p02 direction-aware vector helpers. It reads Rhine
`uparea`, the standard `nextxy.nc`, `lonlat`, `bifprm`, and 1-minute elevation
products; no Mekong data paths or stations are used. The Step 14 run was
executed once with `nextxy.nc` in a fresh directory; the previous `noedge` run
was left untouched.

- `figure/f15a-maximum_discharge-regional.png` — full 3–13°E, 45–53°N
  direction-aware network with signed local peaks from all 1,181 valid
  main-channel links.
- `figure/f15b-maximum_discharge-aoi.png` — AOI river network with main-link
  and bifurcation signed peaks, flow arrows, and elevation background.
- `experiment/Rhine2021-nextxy/analysis/maximum_discharge_20210701-20210720.nc` —
  derived peak data under the Git-ignored experiment directory (33,864 bytes).

## Checks and visual review

- Read 597,600 valid `outflw` values; 35 grid cells have no valid output and
  remain missing. There are 1,245 valid peak cells. Signed peak range:
  −1,095.38 to 11,592.53 m³/s; 11 cells have a negative signed peak. The
  source includes 3,522 negative hourly values, none treated as missing.
- Recomputed every valid cell's signed local peak directly from the source
  records; all 1,245 values match the saved derived NetCDF within float
  precision.
- The 20 `pthflw` output IDs and endpoint coordinates match the Rhine
  `bifprm.nc` table. Positive layer widths identify 7 channel-bifurcation and
  13 overland-only paths. Signed peak range: −202.81 to 2,373.30 m³/s; 4 path
  peaks are negative.
- Fig. 15a displays the full 3–13°E, 45–53°N network with increased
  upstream-area-scaled vector line widths (up to 1.68 points) and 1.50-point
  bifurcation paths, using standard `nextxy.nc` topology.
- Fig. 15b displays the specified 4–8°E, 49–52°N AOI, 1,181 main-network links
  and all 20 valid bifurcation paths over the Rhine 1-minute elevation data.
- Both PNGs were opened and inspected after the line-width increase. Fig. 15a
  now has clearly visible main-channel and bifurcation lines. The initial AOI axis argument order
  showed an incorrect extent and was corrected. A second visual pass found
  overlap between the lower legend and longitude label; layout spacing was
  adjusted, then the figures were regenerated and inspected again.
- The derived NetCDF was reopened and its variables, dimensions, dtypes,
  units, and fill values were checked.

## Limitations and handoff

No observations were matched, no skill metric or accuracy evaluation was
performed, and no conclusion about flood-reconstruction quality is supported.
All map-cell and pathway peaks can occur at different hours; Fig. 15b is not
a simultaneous network state. The run was cold-started without spin-up, and
KG-0019 remains unresolved. Step 16 must establish defensible spatial,
temporal, and variable correspondence before evaluation.


## Current map-interface follow-up — 2026-11-28

Updated Step 15 base-map reads to the current map-root NetCDF layout and `params.nml`. The retained `pthflw` NetCDF carries the exact static path IDs, endpoints, coordinates and layer widths used by its simulation; Step 15 now uses that paired metadata for unchanged active-layer aggregation and path display. This was necessary because the current local `bifprm.nc` has 23 paths while the retained run has 20; seven shared path IDs have changed endpoint indices, and current IDs 21–23 are absent from the run. Joining the current table to the retained time series would misrepresent that result. No model output or map data was changed.

A focused run to `/tmp` succeeded: all 744 records were read; 1,245 valid outflow peak cells and 20 bifurcation paths were processed; 1,181 main-network links and all 20 retained bifurcation paths were drawn regionally. Figures 15a/15b and the derived NetCDF were opened/inspected; visual layout was readable. This validates the map-format interface for the retained outputs, not equivalence of the current revised bifurcation map to the historical run.
