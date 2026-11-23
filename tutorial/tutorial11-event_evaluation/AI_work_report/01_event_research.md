# p01 Event Research — AI Work Report

## Work Summary

Reconstructed from retained Tutorial 11 documents, impact inventory, station inventory and Figure 1. This report task did not repeat the literature search, recreate the CSV, or regenerate the map.

## Inputs

- Historical source: former root `01_flood_event_overview.md` (now migrated to the Survey Report)
- `metadata/01_impact_locations.csv`; `observation/README.md` and `metadata/04_discharge_dataset.json`
- `figure/f01-reported_flood_impacts.png`; `f01-reported_flood_impacts.sh`

## Actions Performed

- Summarized retained event, impact, candidate-observation and uncertainty statements.
- Kept correspondence-supplied details distinct from public references and inspected station-file facts.
- Preserved the distinction between approximate locality coordinates and measured flood limits.

## Generated Outputs

- `AI_survey_report/01_flood_event_overview.md`
- `AI_work_report/01_event_research.md`
- Existing CSV and Figure are inputs, not modified outputs.

## Execution and Checks

- No scientific search, Shell, Python, or plotting command was rerun for this retrospective report.
- The report links to existing Figure 1 and inventory files.

## Issues and Resolutions

- Supplied archive files contain Lobith, Speyer and Maxau; earlier correspondence named Bonn, which is absent. The report follows inspected-file evidence.
- Gauge units/time zone/source agency remain unknown; no assumptions were introduced.

## Remaining Issues

- Confirm station provenance, units, timezone and coordinate convention before quantitative use.
- Verify collaboration-supplied ECMWF experiment identifiers and satellite candidate datasets from their original records.
- Step 2 must determine the actual model routing scope; this report does not assign Basin IDs.


## 2026-11-24 — Flood timing and detailed location update

### Inputs and research

Reviewed all 14 rows in `metadata/01_impact_locations.csv` and retained their identifiers and map coordinates. Consulted the LfU July 2021 report, Erftverband catchment report, Waterschap Limburg crisis evaluation, the Delft University flood-event thesis (Vesdre/Geul context), and the Demer Basin assessment. Station coordinate references were checked for Altenahr, Müsch, Bad Bodendorf, Bliesheim, Kordel and Prümzurlay.

### Outputs and decisions

- Created `metadata/01_reported_flood_timing.csv` with 14 locality-level impact records plus 8 distinct gauge/outlet timing records. `ai_notes` is the final field.
- Locality impact coordinates remain approximate map points. Station coordinates use separate timing records and do not move or relabel the 14 impact markers. Unknown local times remain blank in UTC fields.
- LfU table times are explicitly MESZ/CEST and were converted to UTC (UTC−2), retaining original labels. Erftverband, Waterschap Limburg and the Eupen outlet thesis did not explicitly establish timezone notation in the examined passages; their UTC fields remain blank.
- Updated `metadata/event_figure_settings.json` with concise, qualified river/gauge timing labels. Added optional legend-title support to `visualization/river_map/script/f06b-OSM_background-local_info.py`; configurations without `legend_title` keep the existing default behavior.
- Regenerated `figure/f01-reported_flood_impacts.png` with `bash tutorial/tutorial11-event_evaluation/f01-reported_flood_impacts.sh`.
- Updated the Step 1 Prompt, process document, Survey Report, and development/status records.

### Checks and limits

Confirmed all 14 base `location_id` values exist in the impact inventory; confirmed CSV header order and that `ai_notes` is last; checked all populated UTC values are CEST−2 conversions only from the LfU table. Figure rendering completed and the saved output was visually inspected. The timing search is selective, not exhaustive; precise local inundation times remain unresolved for many towns. No model output, gauge allocation, or quantitative comparison was produced.
