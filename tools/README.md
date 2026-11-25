# Shared Tools

## Overview

`tools/` contains reusable command-line utilities and independent scientific
workflow packages shared by CaMa-Flood v5 examples. It does not contain model
source code or map-conversion utilities; those remain in their component
directories.

## Available Tools

| Tool | Category | Purpose | Location |
| --- | --- | --- | --- |
| `igetday` | calendar | Print Gregorian days in a requested month. | [`scripts/igetday.py`](scripts/igetday.py) |
| `output_ctl` | data_format | Generate GrADS CTLs for configured Binary model outputs. | [`scripts/generate_output_ctl.py`](scripts/generate_output_ctl.py) |
| `restart_ctl` | data_format | Generate GrADS CTLs for Binary Restart files. | [`scripts/generate_restart_ctl.py`](scripts/generate_restart_ctl.py) |
| `downscale_flddph` | output_analysis | Downscale CaMa-Flood flood depth or annual flood duration to an existing higher-resolution map grid. | [`downscale_flddph/`](downscale_flddph/README.md) |
| `cmf_shell_functions` | shell | Source common map-preprocessing Shell functions. | [`cmf_shell_functions.sh`](cmf_shell_functions.sh) |

The machine-readable source of truth is [`tools_list.csv`](tools_list.csv).
Detailed instructions are in [`scripts/README.md`](scripts/README.md) and the
individual package README files.

## Tool Categories

- `calendar`: date and calendar helpers.
- `data_format`: utilities for preparing visualization descriptors for model
  data products.
- `output_analysis`: analysis workflows for model outputs.
- `shell`: functions sourced by map-preprocessing Shell workflows.

Categories are catalog metadata, not directory names. Small standalone
utilities belong in `scripts/`; multi-file workflows with their own settings
and samples belong in a named directory under `tools/`.

## How to Use

Python utilities in `scripts/` can be run directly from any working directory.
For example:

```sh
./tools/scripts/igetday.py 2024 2
./tools/scripts/generate_output_ctl.py --help
./tools/scripts/generate_restart_ctl.py --help
```

For package workflows, read the package README and edit its documented user
settings before running the Shell entry point. The downscaling package is
standalone and can be copied into another research project; its map and data
inputs remain external.

### Shared map Shell functions

Map-preprocessing Shell workflows validate `CMF_V50_ROOT` and source the common
entry point:

```sh
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"
cmf_check_init "Prepare map data"
HIRES_TAG=$(cmf_select_hires_tag "${HIRES_TAG:-}")
```

The entry point only loads functions. The implementations live in
`tools/shell_functions/`: `cmf_check_shell_error.sh` provides the `cmf_check_*`
reporting functions, and `cmf_select_hires_tag.sh` interactively resolves one
installed high-resolution tag. Selection prompts and diagnostics go to stderr;
the selected tag alone is written to stdout so command substitution is safe.
The selector expects to run from a map-local script directory and checks
`../<tag>` directories in coarsest-first order. An explicit valid tag is
proposed for confirmation; an unset value proposes the coarsest available tag;
declining allows selection from the available list. Invalid input and EOF fail
instead of silently choosing another map.

The public calls are `cmf_select_hires_tag "$HIRES_TAG"` for operations that
may process multiple `location.txt` areas, and
`cmf_select_hires_tag "$HIRES_TAG" --single-area` for allocation workflows.
Single-area mode checks that `location.txt` declares exactly one area, its
identifier matches the selected tag, and at least one `<TAG>.<VARIABLE>.nc` or
`.bin` layer exists. This is a layout check, not validation of required layer
contents; the Python reader performs scientific-input checks. The `.bin` form
keeps explicitly selected legacy Binary maps eligible.

## Tool Catalog for AI Agents

Before developing a new utility, inspect [`tools_list.csv`](tools_list.csv) and
reuse a tool whose purpose matches the task. Use `long_description` to assess
when it applies and its limits; read the linked README and `--help` for exact
input/output contracts and commands. When adding a tool, update both the CSV
catalog and this README. The catalog is maintained by hand; it is not generated
automatically.
