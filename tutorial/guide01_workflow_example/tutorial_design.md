# Workflow Example — River-Depth Sensitivity and Flood-Inundation Analysis

**Status:** The complete reference workflow, simulations, analyses, and figures
were implemented and run earlier; their history remains in Guide01. The
learner start now requires editing the map preparation setting and creating a
separate GOSH configuration. This intentionally incomplete learner workflow
has not yet been followed through from a fresh package.

This document refines the Chat AI draft in
[Step 03's first design draft](../guide01_how_to_develop_tutorial/03draft_first_tutorial_design.md)
using the current implementation and sample files. It defines this tutorial
and does not claim that the experiment has been scientifically validated.


Guide01 shares Tutorial02's executable prerequisite: reuse the NetCDF-enabled
`src_main/MAIN_cmf` compiled during Tutorial01. Do not invoke a separate compiler
wrapper or depend on an out/bin model executable. Keep the repository-local Python environment requirement. Guide01 bundles a
copy of the standalone Python `downscale_flddph/` package and uses NetCDF for
the event input and one-minute result; it does not compile the legacy Fortran
program. This path alignment does not change the approved experiment settings
or learner edits.

## 1. Purpose and learning outcomes

The example teaches a controlled sensitivity experiment: change the mapped
river-channel depth, run otherwise matched CaMa-Flood simulations, and examine
how the model responds in discharge, channel depth, water-surface elevation,
and inundation. Learners should be able to:

- preserve and compare a baseline map parameter with a reproducible modified
  parameter;
- configure equivalent model experiments so that `rivhgt` is their only
  scientific input difference;
- distinguish channel depth, water-surface elevation, inundated fraction, and
  flooded area;
- derive spatial and regional diagnostics from time-dependent model outputs;
- trace a selected coarse-grid flood state into the existing 1-minute
  inundation downscaling method; and
- distinguish a model sensitivity result from observational validation or a
  general prediction.

The expected responses discussed in the initial design are hypotheses. The
figures must show the measured model response, including results that differ
from those expectations.

## 1.1 Required learner activities

Learners change `RIVHGT_INCREMENT_M` from `0.0` to the approved `3.0` in
`s01-prepare_map.py`, then generate the tutorial-owned
`map_modify/rivhgt_deep.nc`. They copy `run-experiment.sh` and edit `PROJ` and
`RIVHGT` to create an independent Deep Channel configuration that uses the
modified map. These activities teach learners to prepare a map-parameter
variant without modifying shared inputs and to configure a separate GOSH
experiment. Completion is observable from the map preparation checks, separate
Control and Deep Channel output paths, and comparison products. Completed
reference scripts, modified map data, and analysis evidence remain in
`design/` and must be omitted from learner packages.

## 2. Researcher-approved experiment

| Setting | Control | Deep Channel |
|---|---|---|
| Map | Mekong 15-minute map | Same map and geometry |
| River depth | Original `rivhgt` | Original valid-cell values + 3.0 m |
| Physics and numerics | Tutorial02 `mek_default` | Identical to Control |
| Runoff, input matrix, dates, initial state | Same | Same |
| Period | Calendar year 2000, including February 29 | Same |
| Output | Daily NetCDF | Same |

The only intended experiment change is the static channel-depth parameter.
Treat the shared map as a read-only source. Generate the modified map parameter
inside this tutorial at
`tutorial/guide01_workflow_example/map_modify/rivhgt_deep.nc`.
The learner map-preparation script belongs to this tutorial, not the shared
map-building tools. Control reads the original
`map/mekong_15min/rivhgt.nc`; Deep Channel points `CRIVHGT` directly to
the tutorial-local NetCDF file. Do not write the variant or a symlink into
`map/mekong_15min/`. The existing individual-map NetCDF convention stores the
logical variable as `rivhgt` even when the file has a different descriptive
filename.

The map reader uses the path supplied in `CRIVHGT` directly; it does not
prepend the shared map directory. Tutorial run scripts execute the model from
their run directory, so they should derive an absolute path to
`map_modify/rivhgt_deep.nc` from the script location and place
that path in the Deep Channel namelist. This avoids dependence on the caller's
current working directory. The source map remains shared and read-only; the
modified product is owned by this workflow example.

In `src_main/cmf_ctrl_maps_mod.F90`, channel-bed elevation is calculated as
`D2RIVELV = D2ELEVTN - D2RIVHGT`. Thus adding 3 m to `rivhgt` lowers the
calculated channel-bed elevation by 3 m while leaving channel-top elevation
unchanged. In `src_main/yos_cmf_diag.F90`, `D2SFCELV` is the water-surface
elevation (`elevtn - rivhgt + rivdph`). An increase in `rivdph` therefore does
not by itself imply an increase in absolute `sfcelv`.

### Verified map contract

The current `map/mekong_15min/params.txt` declares an 80 × 120 grid at 0.25°
covering 90–110°E and 5–35°N. Cell centers are 90.125–109.875°E and
5.125–34.875°N. The existing
[`netcdf/rivhgt.nc`](../../map/mekong_15min/rivhgt.nc) has a Float32
`rivhgt(lat,lon)` variable in metres with `_FillValue` and `missing_value`
`-9999`; its coordinates and missing mask match the corresponding map fields.
The inspected sample has 6,566 nonmissing cells and 3,034 masked cells. The
`nextx` mask matches the `rivhgt` mask; valid endpoint codes such as `-9` and
`-10` mean a test like `nextx > 0` would incorrectly exclude valid network
cells. Use the source missing mask / valid-network mask, not a positive-index
test. This is a structural check of the current sample, not scientific
validation of the map.

For the modified product, preserve dimensions, coordinate arrays, variable
name, units, and missing-value attributes, and add 3.0 m only where the source
`rivhgt` is valid. Validate that the baseline file remains unchanged, that the
valid-cell difference is exactly +3.0 m within Float32 representation, and
that missing cells remain missing. The learner package intentionally omits this generated file; the complete
reference product is retained under `design/`.

Relevant metadata are in [`map_variables.csv`](../../variable_table/map_variables.csv),
and the model map reader is documented in
[`src_main/README.md`](../../src_main/README.md). The Mekong sample also has
`prmwat.nc`, an optional post-processing map whose `prmwat` values are
per-unit-catchment permanent-water area in m². It is not a simulation input.

## 3. Simulation configuration and outputs

The reference Tutorial02 runner is
[`mek_default.sh`](../tutorial02-mekong_netcdf_4exp/mek_default.sh). Its
verified settings include `LKINE=.FALSE.` (Local Inertial routing),
`LFPLAIN=.TRUE.`, `LPTHOUT=.TRUE.`, `LFLDOUT=.TRUE.`, `LSLPMIX=.FALSE.`,
`LADPSTP=.TRUE.`, `DT=600` s, 4 OpenMP threads, and Gregorian leap-year
handling. It reads individual map NetCDF files under
`map/mekong_15min/`, the 2000 annual runoff file
`inp/repo-mek_1deg/runoff2000.nc`, and the existing
`inpmat_repo-mek_1deg.bin` / `diminfo_repo-mek_1deg.txt` pair. Its forcing setup
uses `CROFFREQ="YEAR"`, `IFRQ_INP=24`, `CVNROF="runoff"`, and
`DROFUNIT=86400000` for the sample's daily `mm day-1` values.

For this one-year experiment, use the same settings and inputs, set the model
period to 2000-01-01 00:00 inclusive through 2001-01-01 00:00 exclusive, and
start both runs from the same configured initial state without a prior-year
Restart. This reproduces the Tutorial02 Default *configuration*, not its
multi-year Restart-connected state. The initial state and forcing must be
identical between the two runs. A one-year run can retain cold-start effects;
it is a controlled one-year sensitivity example, not an equilibrium result.

The output writer in `src_main/cmf_ctrl_output_mod.F90` creates NetCDF files
named `o_<variable><COUTTAG>.nc`; the Tutorial02 convention therefore gives,
for example, `o_outflw2000.nc`. Set `COUTTAG=2000` for both experiments and
use `IFRQ_OUT=24` and `LOUTCDF=.TRUE.`. The researcher-approved daily output
set is `outflw`, `rivdph`, `sfcelv`, and `fldfrc`:

| Variable | Meaning and unit | Time semantics in `output_variables.csv` |
|---|---|---|
| `outflw` | River + floodplain discharge, m³/s | Daily interval mean (`D2OUTFLW_oAVG`) |
| `rivdph` | River-channel water depth, m | Snapshot |
| `sfcelv` | Water-surface elevation, m | Snapshot |
| `fldfrc` | Flooded fraction of a unit catchment, dimensionless | Snapshot |

The model calls output after the interval diagnostics are finalized in
`src_main/cmf_drv_advance_mod.F90`; do not describe every variable as a daily
mean. Use `variable_table/output_variables.csv` as the metadata source. Check
that each output has a complete, aligned 2000 time axis (including leap day),
consistent map coordinates and fill values, and the expected variable and
units. The earlier Guide01 execution record documents the reference run; a fresh
learner-created run has not been performed after making the starting files
intentionally incomplete.

**Downscaling input clarification:** Do not add daily `flddph` to the model
output list. For the approved Tutorial02 Default configuration with
`LFPLAIN=.TRUE.`, the staging equations in
`src_main/cmf_calc_fldstg_mod.F90` give the floodplain depth from channel
depths as `max(rivdph - rivhgt, 0)`: below bankfull, floodplain depth is zero;
above bankfull, channel storage is represented as channel maximum storage
plus `river_length × channel_width × flddph`. The downscaling adapter can
derive this field from each selected `rivdph` NetCDF time slice and the static
`rivhgt` map. This saves a redundant daily output field. The clipping at zero
is required to match the model's below-bank behavior.

## 4. Current learner and developer file organization

The tutorial lives at `tutorial/guide01_workflow_example/`, beside Tutorial01
and Tutorial02. The GitHub source retains completed solutions and developer
records in `design/`; the learner package excludes that directory. The starter
preparation script and Control GOSH are present, while the modified map and
learner-created Deep Channel GOSH are absent. Generated outputs are ignored.

```text
tutorial/guide01_workflow_example/
├── tutorial_design.md
├── design/                         developer references and reset
├── manual_workflow_example.md      learner instructions
├── s01-prepare_map.py              starter; learner changes increment to 3.0
├── run-experiment.sh               working Control GOSH template
├── s02-run_control.sh
├── map_modify/                     initially no modified map
├── out/                            generated model outputs
├── analysis/                       generated diagnostics
├── figure/                         generated learner figures
└── sample_figure/                  approved expected-result figures
```

`design/` includes the complete map-preparation and experiment scripts,
reference map, tests, and prior analysis products. `sample_figure/` is included
in the learner file set; `figure/` contains no pre-generated PNGs. There is no
tutorial package assembler yet, so only a temporary staged file-set review can
be performed at this time.

## 5. Analysis plan

### Controlled comparisons

First compare time coordinates, masks, dimensions, and map geometry across
variables and experiments. Compute `Deep Channel - Control` only over matching
valid cells and timestamps. Summarize `outflw`, `rivdph`, `sfcelv`, and
`fldfrc` using statistics and sites selected during review. Preserve signed
discharge if it occurs. Do not encode the expected response as a pass/fail
condition.

The fixed Phnom Penh event is selected from the **Control** 2000 daily
`sfcelv` series at a researcher-approved nearby model cell. Record the cell,
coordinate, timestamp, peak value, and tie-breaking rule in a derived table.
Use that same date for both experiments; it need not be the date of maximum
delta-wide inundation.

### Flooded fraction and area

`ctmare` is unit-catchment area in m²; `fldfrc` is a dimensionless fraction.
The model computes `D2FLDARE = D2GRAREA × D2FLDFRC` in
`src_main/cmf_calc_fldstg_mod.F90`. For a regional total, calculate
`Σ(fldfrc × ctmare)` over an agreed set of valid catchments, then divide by
1,000,000 for km². For cellwise maps compare `fldfrc` itself, because
`fldare`/area-weighted values scale with catchment size. The exact regional
mask and treatment of catchments crossing its boundary remain open.

### Permanent water

The current `prmwat` product is a coarse, per-catchment area in m², not a
high-resolution pixel mask. `map/tools/script_params/s05-permanent_water.sh`
and `param_water_calc_prmwat.F90` document how it is aggregated. The existing
1-minute downscaler instead uses high-resolution `rivwth` values as its
permanent-water classification and applies a minimum 0.1 m depth at pixels
where `rivwth` is neither `-9999` nor zero. It does not read `prmwat`.
Initially show `prmwat` as separate context (or omit it from the 1-minute
pixel image); do not subtract it from `fldfrc` or the downscaled depth without
a researcher-approved area-conserving method. This avoids treating an
aggregate catchment area as a pixel mask or double-counting standing water.

## 6. One-minute downscaling

### Implemented Python package workflow

The reusable package source is [`tools/downscale_flddph/`](../../tools/downscale_flddph/). Guide01 keeps a self-contained copy under [`downscale_flddph/`](downscale_flddph/) so its learner workflow does not import Python code from `tools/`. The package implements the tributary-aware Python port of the legacy `downscale_flddph_trib.F90` algorithm; the legacy source under `etc/` remains unchanged for reference and other users.

`s04-downscale_event.sh` processes Control and Deep Channel in sequence. For each case, `a02-prepare_downscale_input.py` selects the event time from the matching `rivdph` output, checks coordinates, units and missing masks against that case's `rivhgt`, and writes a one-record `(time,lat,lon)` NetCDF with `flddph = max(rivdph - rivhgt, 0)`. It then invokes the Tutorial-local `downscale_flddph/script/downscale_flddph.py` with the shared Mekong map layers and the fixed 102–108°E, 9–15°N domain. The downscaler writes `flddph_1min_provisional.nc`; no Fortran compile or intermediate Binary file is used. Its existing five-model-cell buffer and high-resolution map interpretation are retained.

`v01-plot_results.py` reads these NetCDF results and checks their coordinates, 1-minute spacing, dimensions, and metre units before drawing Figure 6. The two cases use the same Control-selected event. The output is diagnostic postprocessing, not a new hydrodynamic simulation or direct validation of inundation.

The previously generated sample Figure and summary statistics record the earlier reference run. The Tutorial's model-output directory is not included in this checkout, so the two Guide01 cases could not be rerun during this package migration; the Python-versus-Fortran numerical comparison is separately documented for the p02-f04 Mekong snapshot.

## 7. Proposed figures and interpretation

1. **Map parameter change:** baseline `rivhgt`, Deep Channel `rivhgt`, and the
   valid-cell difference. Teach the mask and why the baseline must remain
   unchanged.
2. **Model output fields:** representative daily `outflw`, `rivdph`, `sfcelv`,
   and `fldfrc` maps with units and variable-specific scales. Exact date(s) TBD.
3. **River-channel time series:** Control and Deep Channel at researcher-
   selected map cells. Locations and summary period TBD.
4. **Flooded fraction versus area:** contrast `fldfrc` cellwise with
   `fldfrc × ctmare` area and show the selected region's total area through
   time. Region TBD.
5. **Sensitivity maps:** experiment differences for selected daily/statistical
   summaries. Exact date/statistic TBD; show actual responses, not assumed
   reductions.
6. **One-minute downscaling:** Control and Deep Channel on the shared
   Control-peak date, with a map extent selected around Phnom Penh. Identify
   `prmwat` separately as catchment-level context if useful; do not imply that
   it is the downscaler's input or a pixel mask.

Why keep `rivdph` and `sfcelv` separate: `rivdph` is measured relative to the
channel bed, while `sfcelv` is absolute elevation. Why use `fldfrc` and
`fldfrc × ctmare` differently: the first is comparable cellwise; the second
contributes physical area to a regional sum. Why use one Control-selected
date: both images then represent the same event, rather than each experiment's
different peak.

## 8. Validation and scope for a later implementation

| Stage | Minimum checks |
|---|---|
| Map parameter | Source unchanged; same dims/coords/dtype/metadata; +3.0 m only on valid cells; missing mask identical. |
| Control/Deep runs | Same executable, namelist values except `CRIVHGT`, forcing, input matrix, date range, and initial state; completion logs and daily time-axis check. |
| Output analysis | Registry units/semantics; identical coordinates/time; missing masks; `fldfrc` bounds; reproducible point/date selection and area sum. |
| NetCDF downscaler input | Requested date maps to exactly one time record; validate `rivdph`/`rivhgt` coordinates, units and masks before deriving nonnegative `flddph`; verify output coordinates, units, fill value and one-record time. |
| 1-minute result | Crop geometry and buffer coverage; expected raster dimensions/orientation; assigned/unassigned pixel counts; finite nonnegative depths; verify the same event date in both experiments. |
| Figures | Rebuild from stored analysis products; labels/units/scales reflect the variables; caption says sensitivity, not validation. |

Use small synthetic NetCDF fixtures for the Guide01 adapter and package input
contract. The package migration preserves the legacy algorithm and the output
is checked against its established reference where the corresponding sample is
available. Do not validate the external NetCDF library itself; verify the
expected values, dimensions, mask, and selected time slice.

## 9. Open questions for researcher review

### Blocking before point-based analysis and downscaling

1. **Phnom Penh reference cell:** Specify a named coordinate/station or
   approve a reproducible rule such as the nearest valid model cell to a
   supplied Phnom Penh reference coordinate. The maximum `sfcelv` date depends
   on this choice.
2. **Downscaling crop:** Approve west/east/south/north bounds around Phnom Penh.
   The crop must be covered by the 1-minute tiles including the tool's
   five-cell model-grid buffer.

### Needed before regional-area figures and finalizing analysis

3. **Lower-Mekong/delta region:** Define the catchment mask and how edge
   catchments are counted. Different masks produce different total-area
   series.
4. **Other temporal summaries and point locations:** Choose dates/statistics
   for representative spatial maps and locations for `outflw`, `rivdph`, and
   `sfcelv` time series. Keep the fixed Control peak-day rule for the
   downscaling event.

There is no need to output model `flddph`; it is derived for the downscaler
from daily `rivdph` and static `rivhgt` under the selected Default physics.
Whether `prmwat` is used beyond separate context visualization remains a
scientific choice; no quantitative subtraction is specified here.

## 10. Current implementation status and remaining work

The complete reference implementation, map variant, analysis artifacts, and
figures are retained in `design/` and `sample_figure/`. The learner-facing
starter map script requires changing its increment setting, and the completed
Deep Channel runner is not present at the tutorial root. No new simulations or
scientific results were generated for the learner-package revision. The next
work is to build a real tutorial package, follow the manual from a clean
package, and record any usability gaps. Scientific interpretation questions
in Sections 8–9 remain open and must not be settled by package preparation.
