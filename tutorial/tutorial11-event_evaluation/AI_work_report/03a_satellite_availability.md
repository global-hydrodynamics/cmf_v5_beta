# p03a Satellite Availability — AI Work Report

## Work Summary

Reconstructed from current tracked pass/orbit metadata, Step 3a survey narrative, selected-pass JSON, Figure 3a and retained Atlantis notes. Catalogue search was not repeated for this documentation task.

## Inputs

- `metadata/02_domain_selection.json`
- `metadata/03a_satellite_pass_inventory.csv`
- `metadata/03a_satellite_orbit_metadata.csv`
- `metadata/03a_sentinel1_acquisition_footprints.geojson`
- `metadata/03a_selected_passes.json`
- Existing Atlantis catalogue caches and Step 3a implementation, as described by the retained survey record

## Actions Performed

- Consolidated the current focused 14–16 July pass inventory and geometry interpretation.
- Preserved separate counts for STAC Items, Equi7 tiles, source products and acquisition passes.
- Recorded that GFM tile coverage and source Sentinel-1 acquisition footprints are different geometries.

## Generated Outputs

- `AI_survey_report/03a_satellite_availability.md`
- `AI_work_report/03a_satellite_availability.md`
- No pass metadata or Figure was changed.

## Execution and Checks

- No STAC request, Copernicus OData query, Shell, Python or rendering command was run during retrospective documentation.
- The retained survey record reports 45 Items / 6 passes / 27 source product slices and documents reuse of the 15 July cache plus read-only queries for the other dates.

## Issues and Resolutions

- Atlantis source/Pixi symlinks were unavailable during the original survey. The record says the environment was not rebuilt; cached/read-only metadata supplied the survey.
- Selected pass remains `proposed`; this is not a processing gate.

## Remaining Issues

- Catalogue footprints do not prove valid GFM pixels or useful flood coverage.
- Review pass timing against hydrologic evidence and inspect valid/exclusion masks after acquisition.
