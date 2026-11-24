# p03c GFM Classification — AI Work Report

## Work Summary

Reconstructed from retained processing metadata, focus-area JSON, current 1-minute raster and Figure 3c. The classification, aggregation and focus selection were not rerun for this documentation task.

## Inputs

- p03b manifest/COGs as identified in the retained processing records
- `metadata/02_domain_selection.json`
- `observation/GFM_extent/GFM_S1A_20210715_o038784_dt049389_extent20m.json`
- `observation/GFM_extent/GFM_S1A_20210715_o038784_dt049389_floodfrac_1min.tif`
- `metadata/03c_focus_areas.json`; Figure 3c

## Actions Performed

- Transcribed class definitions/counts and 1-minute raster facts from retained metadata and raster inspection evidence.
- Preserved the denominator rule (classes 0–4) and focus-selection diagnostics.
- Separated the absent full-source TIFF from files that remain present; did not restore or recreate it.

## Generated Outputs

- `AI_survey_report/03c_gfm_classification.md`
- `AI_work_report/03c_gfm_classification.md`
- Existing metadata, data and Figure are unchanged.

## Execution and Checks

- No classification or aggregation script was run.
- Retained rasterio inspection records the fraction TIFF as readable, 240×180, EPSG:4326, 1/60° grid, NoData -9999, 35,225 valid cells, range 0–75.91241%.
- Retained provenance records the source TIFF at 17,835×19,783, uint8, single band, 20 m and 23,445,565 bytes with SHA256 `ce449f65dbeeceacb5b7f2c493b70603d74f42a7e41127ed8fcff67bc20e10de`. The source raster is deleted in the current worktree by a pre-existing change; its counts were not freshly checked against pixels.
- The focus JSON records 140,228/160,301 Flood pixels retained (87.48%), 9.78% union area, 90.09% unique projected-window pixel reduction, and an in-memory estimated size of 2,098,447 bytes.

## Issues and Resolutions

- The size estimate is not the later measured total of extracted crops.
- The current worktree lacks the monolithic source TIFF. We reported inherited provenance separately from the current fraction raster and crop files.

## Remaining Issues

- For a pixel-level verification against the full source, restore it from the recorded source/provenance location only through a separate authorized data task; this report task did not alter user data.
- Valid support, exclusion and classification uncertainty must be retained in any later model comparison.


## 2026-11-24 — Focused Python readability pass (DT-0177)

Applied the new Python Style guidance to `script/f03c-flood_fraction_1min.py`
(the maintained path uses singular `script/`). Expanded the purpose/inputs/
outputs/workflow header and function docstrings; documented valid-support
percentages, north-up arrays, pixel-centre selection versus pixel-edge geometry,
and NoData versus valid zeros. Added meaningful numbered stages and repaired
continuation/call indentation. Kept main at the end; no function extraction,
new abstraction, import reordering, type changes or new configuration controls.

Verification: in-memory syntax compilation and exact AST equality against the
pre-task source after removing module/function docstrings; CLI argument/default
expressions also remain identical. The expanded module docstring is shown in
argparse's description; no option/help-option text or error condition changed.
`git diff --check` passes. No classification, aggregation, rendering, acquisition,
model or broad test-suite execution. Existing rasters/figures and scientific
handoff/fingerprint records are untouched; comments explain existing source
behavior rather than new scientific validation. Research validator retains15
pre-existing unrelated errors. No new scientific/architectural knowledge gap.
Changes remain uncommitted for review. Validation index: VR-0220.
