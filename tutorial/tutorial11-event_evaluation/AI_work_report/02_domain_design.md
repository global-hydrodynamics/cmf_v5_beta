# p02 Domain Design — AI Work Report

## Work Summary

Reconstructed from the retained former Step 2 report, domain handoff JSON, settings, Figure 2 and current process document. No map analysis or figure generation was rerun for this report migration.

## Inputs

- Historical source: former root `02_analysis_domain_design.md`
- `metadata/02_domain_selection.json`, `metadata/event_figure_settings.json`, `metadata/event_map_extents.csv`
- `metadata/01_impact_locations.csv`, supplied station data and `figure/f02-analysis_domain_design.png`
- Existing `f02-analysis_domain.sh` and Tutorial-local f02 scripts/settings

## Actions Performed

- Consolidated the recorded `glb_15min` Basin 74/1299 findings, candidate extents, gauge locations, observation priorities, rationale and unresolved hydrologic choices into the Survey Report.
- Distinguished candidate map viewport, satellite-analysis area and simulation rectangle.
- Left machine-readable metadata unchanged. Its legacy `references` entries may still name the retired root reports; they were not edited under the read-only metadata instruction.

## Generated Outputs

- `AI_survey_report/02_analysis_domain_design.md`
- `AI_work_report/02_domain_design.md`
- Existing metadata, scripts and Figure remain unchanged.

## Execution and Checks

- No basin extraction, network trace, model setup or Figure regeneration was run as part of this report reconstruction.
- The recorded facts were transcribed from the retained Step 2 document and handoff, not newly scientifically verified.

## Issues and Resolutions

- Basin 74 groups Rhine with Meuse/Vesdre routing; basin IDs are not treated as natural drainage divides.
- The candidate simulation box and basin scope are not final. The possible role of ID 1299 remains an open research decision.

## Remaining Issues

- Confirm upstream connectivity, downstream outlet, native/high-resolution watershed relation, active mask, forcing coverage and boundary coordinate convention before simulation.
- Verify reach-level Ahr, Erft/Swist and Vesdre observations.
- The JSON reference strings to retired documents remain stale; no settings or metadata were altered here.
