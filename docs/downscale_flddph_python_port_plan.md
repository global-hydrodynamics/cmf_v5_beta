# Python Flood-Depth Downscaling Package Plan

## Approved scope

- Project: portable Python flood-depth downscaling package.
- Owner: Dai Yamazaki (maintainer); Codex implements.
- Persistent branch: `feature/package-builder` (maintainer confirmed registration on this branch on 2026-11-23).
- Main deliverables: `tools/output_analysis/downscale_flddph/`, its copied `sample_mekong/`, concise `tools/README.md` entry, and task evidence.
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
