# p03b GFM Download — AI Work Report

## Work Summary

Reconstructed from the current ignored local manifest/summary and downloader documentation. The acquisition was not rerun. The local Atlantis assets remain outside Git.

## Inputs

- `metadata/03a_selected_passes.json`
- `metadata/02_domain_selection.json`
- Local Tutorial `Atlantis/` download manifest and summary for `S1A_o038784_dt049389`

## Actions Performed

- Read the retained summary and manifest outcomes as recorded evidence.
- Counted the summary values: 11 selected STAC Items, 44 expected Item/layer references, four layers and 37 unique COG files.
- Confirmed report values against the retained local summary: 37 verified, zero missing/failed, 52,333,157 total bytes and `ready_for_p03c: true`.

## Generated Outputs

- `AI_survey_report/03b_gfm_download.md`
- `AI_work_report/03b_gfm_download.md`
- Existing local data/manifests were not modified.

## Execution and Checks

- No download or processing command was run in this report reconstruction.
- The artifact record states that all 37 paths exist and that size, checksums and GeoTIFF readability were verified by the p03b summary process. Those checks are reported from the retained summary, not repeated here.
- The exact command line and runtime environment are not reconstructed beyond the tracked Shell entry point `run_script/s03b-download_gfm.sh`; no unrecorded invocation details are asserted.

## Issues and Resolutions

- 44 requested Item-layer references map to 37 unique assets; these counts must not be conflated.
- COGs reside under ignored `Atlantis/` and will not be available in another checkout through Git.

## Remaining Issues

- Preserve local data provenance and ensure the manifest's dataset-root-relative paths resolve before p03c in another environment.
- This one selected pass is not the complete event observation record.
