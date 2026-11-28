# Step 14 — Simulation Setup and Execution Work Report

> The first noedge and later 20-day standard-nextxy records below are retained
> as history. The current Step 14 result is the 31-day standard-nextxy run
> under `experiment/Rhine2021/`; that directory was reused, so the earlier
> noedge products are no longer present there.

## Inputs and configuration

- Branch/revision: `feature/package-builder`, `e8763a23`.
- Executable: existing NetCDF-enabled `src_main/MAIN_cmf` (not rebuilt for this
  task; SHA-256 `3a7893ffeb40f052e27d163ebc205374dc8ee7ec3f7564ef69a9ea1f293dc987`).
- Map: `map/Rhine_15min/`, 40 × 32 at 0.25°, outer bounds 3–13°E, 45–53°N.
  Individual NetCDF files were read with `LMAPCDF=.FALSE.`. Used the regional
  default `nextxy_noedge.nc`, `rivwth_merit.nc`, `bifprm.nc`, and the map's
  other individual NetCDF fields.
- Runoff: Registry ID `tutorial11-ERA5land-Rhine2021Jul`, 20 daily files,
  `runoff(time,lat,lon)` with 24 × 91 × 111 values per day, units mm per
  one-hour timestep. Used `LINPCDF=.TRUE.`, `CROFFREQ="DAY"`, prefix
  `runoff_`, suffix `.nc`, `IFRQ_INP=1`, `DROFUNIT=3600000`, and
  `LINTERP=.TRUE.`.
- Input Matrix: `inpmat_ERA5land_Rhine2021Jul.bin` and matching diminfo;
  `log_CaMa.txt` confirms the regional binary matrix was loaded. The global
  `ERA5land_global` pair was not used.
- Period and initialization: 2021-07-01 00:00 through exclusive
  2021-07-21 00:00, 480 hours, no spin-up, `LRESTART=.FALSE.`, no Restart
  input, `DT=3600`, adaptive timestep and bifurcation routing enabled,
  dam operation disabled. Manning and related parameters retain the `mek01`
  maintained sample values.
- Outputs: `outflw,pthflw,storge,sfcelv,rivdph,flddph,fldfrc,fldare`, hourly
  NetCDF and NetCDF Restart at end only.

## Historical 20-day execution — standard `nextxy.nc`

On 2026-11-23, set `CNEXTXY` to `map/Rhine_15min/nextxy.nc` and reran
the same 480-hour, 20-day cold-start experiment in a new directory to preserve
the original results:

```sh
RUNDIR="$PWD/experiment/Rhine2021-nextxy" bash run_script/s14-run_simulation.sh
```

The model exited with status 0 after 480 steps. The run wrote eight hourly
NetCDF files (each 480 records; gridded fields 32 × 40, `pthflw` 5 × 20) and
the end-time Restart. Outputs plus Restart total 14,878,117 bytes. The model
log confirms the regular `nextxy.nc` input and successful completion; no
error, warning, fatal, or STOP text was found. Machine-readable sizes,
paths and configuration are in
[`metadata/14_simulation_setup.json`](../metadata/14_simulation_setup.json).

## Current execution — 31 days through July 31

The researcher extended the converted ERA5-Land dataset through July 31 and
ran the existing s14 workflow with the standard `nextxy.nc` map. Inspection of
the retained data found 31 raw and 31 converted daily NetCDF files, each with
24 records and the same 111 × 91 input grid. The combined 744 hourly labels
are contiguous from July 1 00:00 through July 31 23:00. Retained download and
conversion logs cover July 1–20 only; per-day logs for July 21–31 were not
present, so evidence for the extension comes from the local files and model
log.

The current simulation covers 2021-07-01 00:00 through 2021-08-01 00:00
exclusive (744 hourly steps), with no spin-up and `LRESTART=.FALSE.`. It
completed with status 0 and wrote the final Restart at 2021-08-01 00:00.
All eight hourly NetCDF outputs have 744 time records; outputs plus Restart
total 23,029,200 bytes. The model log confirms the July 31 runoff file and the
regional Step 13 matrix were read. The matrix was not regenerated because the
input spatial grid remains 111 × 91. Current paths, sizes and metadata are in
[`metadata/14_simulation_setup.json`](../metadata/14_simulation_setup.json).

## Historical 20-day execution instructions

The reproducible entry point is `run_script/s14-run_simulation.sh`. The initial run
documented above used the then-default directory. The historical 20-day standard-network
run used `experiment/Rhine2021-nextxy/`. The current31-day default is
`experiment/Rhine2021/`; the example below is its entry point:

```sh
bash run_script/s14-run_simulation.sh
```

The current script resolves paths from its own location and defaults to
`experiment/Rhine2021/`. It does not clear or overwrite a nonempty run
directory; set `RUNDIR` to another path for an additional run. The first
attempt of the original noedge run exposed one extra `..` in the repository-
root path and stopped before the model launched. That path was corrected,
after which the run completed successfully. No generated result existed to
overwrite.

The successful execution ran on macOS arm64 with four OpenMP threads. It
completed in two seconds with exit status 0. The model log has no error or
warning text and ends at step 480 at 2021-07-21 00:00. No source, map,
converted runoff, or Input Matrix data were changed.

## Historical 20-day runtime products

All the following are ignored by Git under `experiment/`:

- `input_cmf.nam`, copied `MAIN_cmf`, `log_CaMa.txt`, `console.log`,
  `run_time.log`, and `mapdata.txt`.
- Eight hourly NetCDF files, each with 480 time records and a 32 × 40 grid:
  `o_outflwRhine2021Jul.nc` (977,105 B),
  `o_pthflwRhine2021Jul.nc` (157,584 B; 20 pathways × 5 layers),
  `o_storgeRhine2021Jul.nc` (989,359 B),
  `o_sfcelvRhine2021Jul.nc` (920,342 B),
  `o_rivdphRhine2021Jul.nc` (932,745 B),
  `o_flddphRhine2021Jul.nc` (861,981 B),
  `o_fldfrcRhine2021Jul.nc` (880,832 B), and
  `o_fldareRhine2021Jul.nc` (882,594 B).
- `restart2021072100.nc` (63,385 B), with one end-time record.

The eight outputs plus Restart total 6,665,927 bytes. The model outputs use a
time coordinate relative to 2021-07-01 00:00: the first record is 3,600 s and
the final record/Restart is 1,728,000 s. The exact run configuration and
machine-readable file inventory are in
`metadata/14_simulation_setup.json`; the actual Namelist and logs remain with
the ignored experiment products.

## Historical checks and handoff

- `sh -n run_script/s14-run_simulation.sh` passed.
- The run log shows the regional map inputs and Step 13 Input Matrix loaded,
  480 model steps completed, and NetCDF Restart written at the exclusive end.
- `ncdump -h` opened all eight outputs and the Restart. Each gridded output
  contains `time=480`, `lat=32`, `lon=40`; `pthflw` has 20 pathways and 5
  layers. The Restart contains one time record and the same map grid.
- Model log and console were searched for error, warning, fatal, or STOP text;
  none was found. `console.log` is empty because the model writes its detailed
  record to `log_CaMa.txt`.
- `experiment/Rhine2021/` is Git-ignored; only the reusable script and compact
  settings/reports are intended for Git.

The current standard-nextxy operational run does not test hydrologic skill. It uses no spin-up, and
KG-0019 (ERA5-Land 00 UTC accumulation attribution and converter boundary
handling) remains unresolved. Step 15 now visualizes signed local peak
discharge from the retained `outflw` and `pthflw` files; see
[`p15-simulation_output_visualization.md`](../p15-simulation_output_visualization.md)
and the [Step 15 Work Report](15_simulation_output_visualization.md). Step 16
will design observation matching. Do not treat these outputs or figures as a
validated event simulation.


## Current script interface follow-up — 2026-11-28

Updated the reusable Step 14 Shell to the shared `CMF_V50_ROOT`/common-function convention and the current map-root NetCDF layout. It now reads `runoff_tag`, `outputs.input_matrix`, and `outputs.dimension_info` from Step 13 `current_workflow_contract`, which points to the retained NetCDF matrix and Namelist DIMINFO. The recorded 2026-11-24 model execution consumed the historical Binary matrix; its settings, output fingerprints, execution facts and JSON fields were not changed. `sh -n` passed. The simulation was not rerun, and no files in `experiment/Rhine2021/` were changed.
