# p03d Focus-Area Extraction — AI Work Report

## Work Summary

Reconstructed from `metadata/03d_extracted_areas.json`, the 15 referenced crop files and Figure 3d. Extraction and figure generation were not rerun for this report task.

## Inputs

- `metadata/03c_focus_areas.json`
- `metadata/03d_extracted_areas.json`
- Fifteen `observation/GFM_extent/*_F*_extent20m.tif` crops
- `figure/f03d-gfm_focus_areas_20m.png`

## Actions Performed

- Summed recorded per-crop file sizes to 2,113,624 bytes (2.016 MiB).
- Confirmed all 15 metadata output paths exist in the current worktree.
- Read class-count and dimension records from the extraction JSON; did not compare crop arrays against the absent monolithic source.

## Generated Outputs

- `AI_survey_report/03d_focus_area_extraction.md`
- `AI_work_report/03d_focus_area_extraction.md`
- Existing crops, extraction metadata and Figure are unchanged.

## Execution and Checks

- No s03d/f03d command was run for this retrospective report.
- Metadata records 15 outputs, source-pixel alignment, uint8, single-band, 20 m, source CRS WKT, NoData 255, per-file SHA256 and class counts.
- The extraction JSON total is 2,113,624 bytes; the files present match the paths enumerated there. The source full-area TIFF is absent from the current worktree.

## Issues and Resolutions

- The original source raster's recorded size (23,445,565 bytes) comes from retained provenance. The ~90.98% byte reduction is therefore based on recorded source size, not a fresh comparison in this report task.
- Summing per-area class counts can count projected overlap more than once. The reported table is per-file metadata, not a unique-pixel union.

## Remaining Issues

- Use the extraction manifest as the downstream index and preserve its CRS WKT, bounds, checksums and class definitions.
- Before quantitative comparison, define spatial/temporal matching and valid-observation treatment; the crops alone do not establish model skill.
