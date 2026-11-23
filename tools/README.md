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

The machine-readable source of truth is [`tools_list.csv`](tools_list.csv).
Detailed instructions are in [`scripts/README.md`](scripts/README.md) and the
individual package README files.

## Tool Categories

- `calendar`: date and calendar helpers.
- `data_format`: utilities for preparing visualization descriptors for model
  data products.
- `output_analysis`: analysis workflows for model outputs.

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

## Tool Catalog for AI Agents

Before developing a new utility, inspect [`tools_list.csv`](tools_list.csv) and
reuse a tool whose purpose matches the task. Use `long_description` to assess
when it applies and its limits; read the linked README and `--help` for exact
input/output contracts and commands. When adding a tool, update both the CSV
catalog and this README. The catalog is maintained by hand; it is not generated
automatically.
