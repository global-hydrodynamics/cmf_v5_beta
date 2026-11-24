# p02 Domain Design — AI Work Report

## Work Summary

Initially reconstructed from the retained former Step 2 report, domain handoff JSON, settings, Figure 2 and current process document. On 2026-11-23, the candidate simulation-window bounds and Figure 2 were updated per researcher direction; this did not repeat Basin ID or hydrologic-boundary analysis.

## Inputs

- Historical source: former root `02_analysis_domain_design.md`
- `metadata/02_domain_selection.json`, `metadata/event_figure_settings.json`, `metadata/event_map_extents.csv`
- `metadata/01_impact_locations.csv`, supplied station data and `figure/f02-analysis_domain_design.png`
- Existing `plot_script/f02-analysis_domain.sh` and Tutorial-local f02 scripts/settings

## Actions Performed

- Consolidated the recorded `glb_15min` Basin 74/1299 findings, candidate extents, gauge locations, observation priorities, rationale and unresolved hydrologic choices into the Survey Report.
- Kept the 4–8°E, 49–52°N satellite-analysis AOI unchanged.
- Set the candidate simulation outer-edge bounds to 3–13°E, 45–53°N and retained the previous decimal values in a separate metadata field as the earlier corner-cell-center candidate.
- Expanded only the Figure 2 viewport northward so the new north edge and its label are visible. No Basin-ID, hydrologic-scope or map analysis was repeated.

## Generated Outputs

- `AI_survey_report/02_analysis_domain_design.md`
- `AI_work_report/02_domain_design.md`
- Updated `metadata/02_domain_selection.json`, `metadata/event_figure_settings.json`, `figure/f02-analysis_domain_design.png`, and this report.

## Execution and Checks

- Regenerated Figure 2 with the existing `visualization/river_map/script/f06a-OSM_background-default.py` renderer using `map/glb_15min`, existing OSM cache and Tutorial settings. The orange rectangle now uses outer edges [3, 45, 13, 53].
- Opened the saved figure and confirmed the rectangle, candidate label and title are visible without overlap; the red satellite AOI remains unchanged.
- JSON parsing and `git diff --check` were performed. The prior basin findings remain inherited from the earlier Step 2 review; this update did not independently verify full upstream/outlet coverage or boundary treatment.

## Issues and Resolutions

- Basin 74 groups Rhine with Meuse/Vesdre routing; basin IDs are not treated as natural drainage divides.
- The candidate simulation box and basin scope are not final. The possible role of ID 1299 remains an open research decision.

## Remaining Issues

- Confirm upstream connectivity, downstream outlet, native/high-resolution watershed relation, active mask, forcing coverage and boundary coordinate convention before simulation.
- Verify reach-level Ahr, Erft/Swist and Vesdre observations.
- The map-grid boundary convention and full hydrologic completeness remain to be checked before simulation. The satellite-analysis AOI was not changed.
