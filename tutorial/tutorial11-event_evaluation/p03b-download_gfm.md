# p03b — Download Selected GFM Data

## Workflow Summary

### Inputs
- `metadata/03a_selected_passes.json`
- `metadata/02_domain_selection.json`
- Step 3a catalogue cache/metadata and the requested GFM layers

### Tasks
- Download or reuse only the selected pass's native GFM COG assets and write a manifest plus summary.

### Outputs
- `AI_survey_report/03b_gfm_download.md`
- `AI_work_report/03b_gfm_download.md`
- Native COGs, manifest and summary under ignored `Atlantis/`

## Human Instructions

Provide access to the event directory's Atlantis environment and catalogue cache. The selection may remain `proposed`; scripts must not require `approved`. This Prompt directs the first acquisition and report, not a later classification.

## Example AI Agent Prompt

```text
Complete Step 3b GFM acquisition for the selected event pass(es).

Event directory: [PATH]

1. Read pass IDs, catalogue dates and requested layers from
   `metadata/03a_selected_passes.json`, and the satellite-analysis bbox from
   `metadata/02_domain_selection.json`. Do not require an `approved` status.
2. Reuse the existing Atlantis installation and `run_script/s03b-download_gfm.sh`. Download
   only selected pass assets; reuse matching local files on rerun. Save caches,
   COGs and logs under the ignored event-local `Atlantis/` directory. Do not
   reproject, resample, mosaic or classify the native assets.
3. Check the resulting `download_manifest_<pass-id>.csv` and
   `download_summary_<pass-id>.json`: Item/layer correspondence, unique files,
   sizes, checksums, file presence and raster readability. Distinguish manifest
   item-layer rows from unique COG files and bytes.
4. Create/update `AI_survey_report/03b_gfm_download.md` for the researcher and
   `AI_work_report/03b_gfm_download.md` for developers. Report selected passes,
   assets/layers, verified counts and bytes, acquisition state, missing/failed
   files, commands, issues, and the Step 3c handoff. State clearly what was not
   downloaded or checked.

Do not proceed past acquisition/manifest verification into classification.
Human review is recommended but is not an execution gate. Missing or unreadable
required files remain ordinary processing failures and must be reported.
```

## Data contract

Use the manifest as the authoritative Step 3c file list. Its local paths are relative to the dataset root recorded in the summary. Keep original COGs out of Git; do not place generated assets in shared model directories.
