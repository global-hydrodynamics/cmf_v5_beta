# CaMa-Flood v5 developer test workflows

Maintained v5 simulations are `mek01-default_run.sh` and `mek02-2year_netcdf.sh`. Historical scripts under `legacy/` are not automatically supported v5 workflows. The separate root `legacy/gosh/` retains v4 references. Tutorial workflows are independent, with their own tutorial-local output directories.

## Project and output-directory convention

Each maintained simulation defines `PROJ` in its user settings and defaults to:

```text
${CMF_BASE}/gosh_test/out/${PROJ}/
```

`CMF_BASE` is always the repository root. The project directory contains the copied executable, generated Namelist, model outputs, Restart files, logs and other generated run files. `COUTDIR="./"` and `CRESTDIR="./"` remain relative to the model's working directory, which is `RUNDIR`. The entire `gosh_test/out/` tree is Git-ignored.

| Script | Default PROJ | Default directory from repository root |
| --- | --- | --- |
| `mek01-default_run.sh` | `mek01` | `gosh_test/out/mek01/` |
| `mek02-2year_netcdf.sh` | `mek02` | `gosh_test/out/mek02/` |

The environment can override `PROJ`. A nonempty explicit `RUNDIR` takes precedence over the PROJ-derived default; existing callers that supply it continue to control the full path. An empty variable uses its default. `${VAR:-default}` in the scripts implements this convention.

From the repository root, build using the reviewed local configuration as described in [config/README.md](../config/README.md):

```sh
./gosh_test/compile.sh
cd gosh_test
./mek01-default_run.sh
PROJ=mek01-default ./mek01-default_run.sh
./mek02-2year_netcdf.sh
PROJ=mek02-custom ./mek02-2year_netcdf.sh
```

The first script retains its existing requirement to launch from `gosh_test/`. For a complete path override:

```sh
PROJ=mek01-custom RUNDIR="/absolute/path/to/my-run" ./mek01-default_run.sh
```

Both scripts keep their existing sample-rerun policy: they replace only their known generated files in the selected RUNDIR, not the entire directory. Choose another project or explicit RUNDIR to retain an earlier run. Existing outputs under the old root `out/` locations are not moved or deleted by this change. Files unrelated to the selected sample and sibling projects are preserved.

## Mekong default experiment

`mek01-default_run.sh` uses `src_main/MAIN_cmf`, the tracked 15-minute Mekong map, daily Binary `inp/repo-mek_1deg_bin/` forcing grouped into monthly files (`CROFFREQ="MON"`), reusing the unchanged `test-mek_1deg` input matrix. It runs from 2000-01-01 00:00 to 2000-02-10 00:00 (40 days, end exclusive), with bifurcations and adaptive stepping enabled and reservoir operation disabled. Its default four-thread setup and scientific settings are unchanged. It writes planned output CTLs before the model and Binary Restart CTLs after successful execution; Float64 Restart visualization copies remain explicitly lossy Float32 products.

## Mekong annual NetCDF experiment

`mek02-2year_netcdf.sh` uses the same `src_main/MAIN_cmf`, built with NetCDF support. It runs 2000–2001 with annual NetCDF forcing from `inp/repo-mek_1deg/`, individual NetCDF maps, the Binary input matrix and NetCDF output/Restart. Year two reads the prior year's Restart inside the selected RUNDIR. Years, map selection, output-variable list, timestep and physical settings are unchanged. See the [runoff guide](../inp/README.md#supported-input-formats-and-simulation-settings) for grouping and unit conventions.

The former separate `compile_netcdf.sh` and `legacy02-longterm_netcdf.sh` files are absent from the current checkout; this change does not restore them or change the maintained scripts' executable selection. Historical consolidated-map/Binary-Restart comparison results remain in [the model-source plan](../docs/model_source_workflow_plan.md); they do not validate every current configuration.

## Callers, tutorials and visualization

The output-alias test helper explicitly substitutes RUNDIR and remains compatible. Tutorial01, Tutorial02 and Guide01 run independently and keep their existing tutorial-local output paths. They do not delegate their run directory to these GOSH scripts.

Output-analysis f01 and its shared extractor still default to the previous root `out/mek02-2year_netcdf/` location. They are intentionally not updated in this local task; adapting those callers is deferred to integration. Their existing SOURCE_DIR setting or extractor --source-dir option can identify a run when needed. No fallback or compatibility layer is added.

## Validation and implementation status

The tracked Mekong inputs support small developer runs, while larger data support extended tests. Current output metadata are resolved from `CMF_BASE/variable_table/output_variables.csv` unless `COUTVAR_TABLE` overrides it; maintained runners keep CMF_BASE at the repository root.

Validation is limited to syntax, unchanged Namelist templates and short output-directory probes; no full model simulation or numerical validation is claimed. The [development and distribution design](../docs/development_and_distribution_design.md) records broader unfinished regression/package work. Follow [CONTRIBUTING.md](../CONTRIBUTING.md) for proportionate tests and [Tutorial01](../tutorial/README.md) for learner-facing instructions.
