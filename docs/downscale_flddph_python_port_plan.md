# Python Flood-Depth Downscaling Package Plan

## Approved scope

- Project: portable Python flood-depth downscaling package.
- Owner: Dai Yamazaki (maintainer); Codex implements.
- Persistent branch: `feature/package-builder` (maintainer confirmed registration on this branch on 2026-11-23).
- Main deliverables: `tools/downscale_flddph/`, its copied `sample_mekong/`, concise `tools/README.md` entry, and task evidence. The package was relocated from `tools/output_analysis/` during the approved shared-tools reorganization (DT-0162).
- Preserve `etc/downscale_flddph/`, `visualization/output_analysis/p02-f04`, model code, maps, and Tutorial 11. No Tutorial 11 adoption is included.
- No overlapping open GitHub Issue or PR for `downscale_flddph` was found in the repository search.

## Development and scientific risk

This is L1 feature development with high scientific risk: the port touches Fortran/Python indexing, the order of tributary and backwater adjustments, grid alignment, permanent-water handling, and missing values. The acceptance reference is the existing `downscale_flddph_trib.F90`, compared against a representative Mekong 2001-09-01 input on the same map and target grid. Agreement is evidence of port fidelity, not independent validation of the scientific method.

## Acceptance checks

1. Snapshot extraction uses the CF time coordinate; period mean/maximum semantics and missing-value handling are recorded.
2. Standard and copied sample Shell/Python files have no dependency on repository-relative Python code or symlinks.
3. Python output coordinates, orientation, dimensions, units and missing-value mask agree with the high-resolution map contract.
4. Fortran and Python arrays are compared numerically for the prescribed Mekong case; report valid-cell counts, unequal-cell counts and maximum absolute difference, with the comparison tolerance stated.
5. Verify representative tributary adjustment, backwater, permanent-water and buffer behavior; plot the output and visually inspect the p02-f04-style comparison.
6. Keep tracked sample data limited to the compact low-resolution snapshot, source Namelist when available, downscaled NetCDF and PNG; do not add raw annual outputs or high-resolution maps.

## Data availability note

At project registration, the just-run `gosh_test/out/mek02/` outputs had not yet become available. The maintainer later ran `gosh_test/mek02`; its 2001 NetCDF output and actual `input_cmf_2001.nam` were then found and inspected. The sample uses a snapshot selected from `o_flddph2001.nc` at the exact CF timestamp `2001-09-01 00:00:00`, and the copied Namelist is provenance only (its machine-specific paths are not parsed or used).

## Completion and evidence

The requested package and copied sample were implemented. The Python sample reproduces the existing p02-f04 output exactly over all valid cells. A fresh comparison against the unchanged Fortran reference has identical dimensions and valid masks, with one differing valid cell and maximum absolute difference `2.3841858e-7 m` (comparison tolerance `1e-5 m`). The sample also exercised non-zero tributary adjustment, backwater adjustment and permanent-water handling. Snapshot selection, two-sample inclusive-period mean and maximum were checked against direct selections from the CF time series. See the package README and research validation record for commands, environment, and limits.

Knowledge-gap review: checked scientific assumptions, NetCDF/map I/O contracts, algorithm order, comments and recorded evidence; no material new gaps found. Remaining limits are scope limits, not blockers: only the Mekong 15-minute-to-1-minute sample was compared, and other map families and resolutions are not yet demonstrated. Task and validation evidence are indexed as [DT-0159](../research/development_tasks.csv), [VR-0205](../research/validation_runs.csv), and [the validation detail](../research/records/validation_runs/VR-0205.md).

## Approved scope extension — input compatibility and calculation switches (2026-11-23)

The maintainer authorized extending this package on the same `feature/package-builder` branch. Preserve the downscaling equations and operation order while adding single-record little-endian Float32 Binary snapshots alongside NetCDF input; NetCDF-first, missing-file-only fallback among NetCDF/Binary map layers; and independent `TRIBUTARY_FILL` and `PERMANENT_WATER` switches, both defaulting ON. Keep the implementation and copied sample self-contained, record actual source formats/files and option values in output metadata, and do not change Tutorial, Gallery, map-conversion tools, or Fortran sources. Acceptance is focused on the Mekong sample: exact default output compatibility, cross-format comparisons, all four option combinations, and comparison of Tributary OFF/Permanent ON with the unchanged basic Fortran method. See DT-0161 and VR-0207.


## Approved scope extension — existing workflows (2026-11-23)

The maintainer explicitly extended the existing `feature/package-builder`
assignment to replace active p02-f04 and Guide01 runtime dependence on the
legacy Fortran/Binary workflow with the Python package. Scope covers the
Visualization Shell/plot adapter and catalog/README, a Tutorial-local copy of
the package, Guide01 NetCDF preparation/downscaling/plotting, and directly
related design/manual/test documentation. Preserve experiment settings,
scientific equation, display style, and the legacy Fortran source. The Tutorial
copy must not import Python implementation from `tools/`. No model rerun is
requested. Focused acceptance: p02-f04 render and inspect; synthetic adapter
contract test; syntax/import/path checks; report Guide01 execution limits if
model products are absent.

## Approved scope extension — Flood Duration workflow (2026-11-23)

The maintainer authorized adding the legacy Flood Duration workflow to this
package on the same `feature/package-builder` branch. Add separate Depth and
Duration Shell entry points and self-contained Python copies under
`sample_mekong/`; preserve existing Flood Depth numerical behavior and use
`aggregate_flddph.py` to prepare the sample snapshot only when absent. Port the
legacy daily threshold-count and `catmxy`/`flddif` lookup semantics, including
strict thresholds and a separate permanent-water mask. Keep `sample_mekong/out/`
ignored and preserve local files while removing the previously tracked inputs
from the Git index. Generate the Mekong 2001 Duration NetCDF and Figure, update
package/sample/tool documentation and research evidence, and compare both
Duration stages to the unchanged Fortran references. Do not change CaMa-Flood,
legacy Fortran, Tutorial 11, or Gallery content. The source CF axis has 365
daily timestamps from 2001-01-02 through 2002-01-01; the maintainer confirmed
these are end-time samples representing the 2001 simulation year. See DT-0163
and VR-0209.
