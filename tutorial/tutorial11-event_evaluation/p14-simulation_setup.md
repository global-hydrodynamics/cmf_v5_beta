# p14 — Simulation Setup and Execution

## Workflow Summary

**Inputs**

- The Rhine regional map from Step 11.
- The Tutorial-local ERA5-Land runoff Registry row and converted daily NetCDF files from Step 12.
- The regional `inpmat` and `diminfo` pair from Step 13.
- The built CaMa-Flood v5 executable and its current output-variable Registry.

**Tasks**

- Review the actual map, forcing, matrix and model interfaces.
- Read the runoff tag and matrix/diminfo paths from Step 13 metadata; do not substitute the global ERA5-Land matrix.
- Configure and run the specified single 20-day, hourly cold-start experiment.
- Inspect the run log, hourly NetCDF outputs and end-of-run NetCDF Restart.
- Record exact settings, observed execution results, and limitations.

**Outputs**

- `s14-run_simulation.sh` and generated `experiment/Rhine2021/input_cmf.nam`.
- Ignored experiment outputs, logs and Restart under `experiment/Rhine2021/`.
- `metadata/14_simulation_setup.json`, `AI_survey_report/14_simulation_setup.md`, and `AI_work_report/14_simulation_setup.md`.

This is an operational cold-start run, not a calibrated or scientifically validated event reconstruction. The configured dates and settings come from the researcher; do not infer spin-up adequacy or resolve KG-0019 from a successful run.

## Human Instructions

The Rhine 2021 sample run is configured in `s14-run_simulation.sh`. Review or edit the grouped user settings only when a different experiment is intended. From the Tutorial 11 directory, run:

```sh
bash s14-run_simulation.sh
```

The default run directory is `experiment/Rhine2021/`, excluded from Git. The script preserves existing run contents and stops if that directory is nonempty. To retain a prior run and execute another, set `RUNDIR` to a new location:

```sh
RUNDIR="$PWD/experiment/Rhine2021-retry" bash s14-run_simulation.sh
```

Afterward, inspect the generated Namelist, `log_CaMa.txt`, console/runtime logs, hourly output NetCDF files and final Restart. Review is recommended; it is not a program gate. The input/output checks must still succeed before treating the run as operationally complete.

## Example AI Agent Prompt

```text
Complete Tutorial 11 Step 14 using p14-simulation_setup.md and the existing
Rhine 2021 sample configuration. Inspect the current branch, local rules,
Step 11–13 artifacts, actual map/forcing/matrix files, and current model
Namelist/output interfaces before implementation. Reuse the existing v5
GOSH defaults and do not change model source, map products, runoff conversion,
or the Input Matrix.

Create or update s14-run_simulation.sh to perform the specified one-time
20-day hourly cold-start run from 2021-07-01 00:00 to the exclusive end
2021-07-21 00:00. Use daily NetCDF runoff, the regional Step 13 matrix,
individual NetCDF map products, hourly NetCDF model output, and one NetCDF
Restart at the end. Protect existing experiment results.

Run CaMa-Flood once. Verify successful completion, actual time coverage and
variables in representative output files, and the final Restart. Save outputs
under the ignored Tutorial experiment directory. Create/update Step 14
metadata and separate researcher-facing Survey and technical Work Reports.
Preserve KG-0019 and state that this cold-start run is not a skill/accuracy
evaluation. Update the process/status and development log, then commit/push
only the authorized Step 14 files to feature/package-builder.
```
