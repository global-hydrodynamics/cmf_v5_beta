# Step 15 — Simulation Output Visualization Work Report

## Inputs and method

Used the current Step 14 files
`experiment/Rhine2021-nextxy/o_outflwRhine2021Jul.nc` and
`o_pthflwRhine2021Jul.nc`, resolved through
`metadata/14_simulation_setup.json`. The output map is `Rhine_15min`, 40 × 32,
with bounds 3–13°E and 45–53°N. The AOI was read from Step 2 metadata as
4–8°E and 49–52°N.

Both NetCDF files contain 480 hourly records on identical 3,600-second
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
bash f15-maximum_discharge.sh
```

The script reuses the Gallery p02-f01a native-grid raster conventions for
Fig. 15a and p02-f02b direction-aware vector helpers for Fig. 15b. It reads
Rhine `uparea`, the standard `nextxy.nc`, `lonlat`, `bifprm`, and 1-minute
elevation products; no Mekong data paths or stations are used. The Step 14 run was
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
- Fig. 15a displays the full 3–13°E, 45–53°N native 40 × 32 raster; 1,245
  peak cells are valid and 35 all-missing cells are white.
- Fig. 15b displays the specified 4–8°E, 49–52°N AOI, 1,181 main-network links
  and all 20 valid bifurcation paths over the Rhine 1-minute elevation data.
- Both PNGs were opened and inspected. Fig. 15a shows the configured native
  grid without interpolation, with readable sign and magnitude variation. The
  initial AOI axis argument order
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
