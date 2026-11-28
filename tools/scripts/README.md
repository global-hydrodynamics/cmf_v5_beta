# Standalone Utilities

These standard-library Python command-line utilities can be invoked directly.
Their paths and default registries are resolved from the scripts, not the
current working directory.

## `igetday.py`

Print the number of days in a Gregorian year/month. February in year 0 retains
the legacy 28-day rule.

```sh
./tools/scripts/igetday.py 2024 2
# 29
```

Requires integer `YEAR` and `MONTH` arguments with month 1–12. Invalid input
returns a nonzero status and writes an error to stderr.

## `generate_output_ctl.py`

Create GrADS CTL files for configured Binary XY model outputs. The command
reads `input_cmf.nam`, map geometry, and `variable_table/output_variables.csv`.
It locates the map from `CNEXTXY`, `CGRAREA`, or `CDIMINFO`, preferring the
map's authoritative `params.nml` (`&GRID` and `&DOMAIN`). If that file is absent,
it can derive model-grid spacing from the configured `diminfo_<ROFFTAG>.nml`
`&DIMINFO` group after checking longitude and latitude spacing. `&INPUTDIM`
describes runoff geometry and is not used for CTL axes. Legacy `params.txt`
remains supported where no v5 geometry file is available. When both v5 files
are available, their model-grid dimensions and bounds must agree.

```sh
./tools/scripts/generate_output_ctl.py --help
./tools/scripts/generate_output_ctl.py --run-dir out/mek01-default_run --mode planned
```

`planned` describes configured output files; `existing` describes complete
records already present and reports incomplete files. It does not alter model
Binary data. See [`tools/README.md`](../README.md) for workflow context.

## `generate_restart_ctl.py`

Create GrADS CTL files for existing main Binary Restart files using the
Namelist, map metadata, and `variable_table/restart_variables.csv`.

```sh
./tools/scripts/generate_restart_ctl.py --help
./tools/scripts/generate_restart_ctl.py --run-dir out/mek02-longterm_mapnc
```

For Float64 Restart data, the utility creates a separate Float32 visualization
copy and leaves the original Restart intact. It does not modify the model
Restart.
