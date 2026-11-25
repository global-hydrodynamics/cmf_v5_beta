# ADR-0014: Use required positional inputs and Python defaults for channel parameters

- Status: accepted by maintainer task instruction
- Date: 2026-11-25
- Event IDs: `EV-0763`, `EV-0764`
- Decision owner: Dai Yamazaki

## Context

The channel-parameter programs and Shell workflow repeated standard choices as positional mode tokens and Shell variables. This obscured required inputs and made standard NetCDF execution verbose.

## Alternatives considered

- Retain the existing positional mode selectors and their duplication in Shell.
- Make required data/parameter inputs positional, establish standard NetCDF and input-matrix defaults in Python, and expose only legacy alternatives as named flags.

## Decision and rationale

Use positional arguments for required input files and coefficients. Default to NetCDF map/runoff inputs and input-matrix interpolation. Expose legacy Binary runoff/map handling and nearest-grid interpolation as named Boolean flags. Keep the two maintained s01 wrappers synchronized, with one general initialization block followed by scientific user settings, direct commands and a grouped optional-flag reference.

## Consequences and compatibility constraints

The old positional mode interface is intentionally replaced. The direct Rhine caller and focused benchmarks were updated. Channel equations, coefficients in the maintained standard wrapper, file formats, filenames and calculations remain unchanged. The standard NetCDF workflow and tested legacy Binary sample produced outputs exactly equal to their existing references.

## Evidence and implementation links

- `map/tools/code/param_channel_calc_outclm.py`
- `map/tools/code/param_channel_calc_rivwth.py`
- `map/tools/code/param_channel_set_merit_width.py`
- `map/tools/script_params/s01-channel_params.sh`
- `map/mekong_15min/script_params/s01-channel_params.sh`
- `docs/preprocessing_code_conventions.md`
- `VR-0234`
- Implementation commit: `bdcc579ef944a21a72af999509d15da5e8b2e9aa`

## Supersedes / superseded by

None.
