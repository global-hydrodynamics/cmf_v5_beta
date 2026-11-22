# p03a — Satellite Availability Agent Workflow

## Purpose

Step 3a surveys GFM/Sentinel-1 acquisition metadata for the event's candidate
satellite-analysis domain and identifies useful observation passes for further
processing. On its first run, the agent searches the configured period and area,
creates pass inventories and footprint figures, records an initial recommended
pass selection, and presents evidence for researcher review. Later feedback
updates the same files and figures.

This Prompt currently covers GFM/Sentinel-1. It does not implement other
satellite catalogues.

## Human instructions

After Step 2, give the AI agent the Tutorial event directory and confirm the
evaluation objective and any additional observation priorities. The agent
should use these existing inputs:

- `01_flood_event_overview.md`;
- `02_analysis_domain_design.md`;
- `metadata/02_domain_selection.json`;
- reviewed Step 1 and Step 2 Figures;
- `observation_data_inventory.md`, `gfm_data_inventory.md`, and relevant GFM
  processing notes.

The researcher does not need to manually choose every pass before the initial
search. Run this workflow in the event's own directory. Tutorial 11's Rhine
2021 survey is a worked example; do not rerun it or copy its pass IDs to another
event.

## Example AI agent prompt

Copy and complete the event/objective fields and give this prompt to the agent.

```text
Perform Step 3a satellite availability survey for this flood evaluation.

Event: [EVENT NAME, REGION, YEAR]
Research objective: [RESEARCH OBJECTIVE]
Event directory: [PATH]

Work only in this event directory. Tutorial 11's Rhine 2021 files are examples;
do not edit them or reuse their selected passes, dates, domains or orbit choices
as facts for this event. Use the event's existing Step 1 and Step 2 evidence.
Distinguish source-verified acquisition metadata, GFM tile metadata,
interpretation, candidate selections and unresolved issues.

On this first run, complete the survey through an initial pass recommendation,
metadata files, Figure(s) and a written report. Do not stop to request human
approval for each initial candidate. Save recommendation statuses as `proposed`;
this is descriptive review metadata, not an execution gate. Present the full
result to the researcher afterwards. If the researcher gives feedback, update
the same configuration and result files and regenerate affected figures. Do not
create `_v2`, `_revised`, `_final` or other versioned filenames.

Task 1 — Review event and spatial inputs
Read `01_flood_event_overview.md`, `02_analysis_domain_design.md`,
`metadata/02_domain_selection.json`, the reviewed Step 1/2 figures, and relevant
observation inventories. Relate event timing to the satellite-search period and
review the candidate analysis domain. Use the Step 2 period and bbox as initial
search settings. If they are unsuitable for this survey, explain why and make
an evidence-based update in the same `metadata/02_domain_selection.json` file.
Do not alter simulation-domain facts as a side effect of a satellite-search
change.

Task 2 — Search GFM/Sentinel-1 acquisition metadata
Run the event's `s03a-satellite_availability.sh`. Reuse the established
`s01-download_gfm.py --catalogue-only` path. Search daily into separate local
catalogue/cache directories. Do not download GFM COG or Sentinel-1 image assets.
For each Sentinel-1 acquisition pass, record available STAC Item IDs, source
product IDs, UTC acquisition time, platform, absolute/relative orbit,
ascending/descending direction, datatake, footprint provenance, and relation to
the candidate AOI. Group multiple GFM Items and source slices under the actual
pass; do not count tiles as separate overpasses.

Keep these geometries distinct:
- GFM STAC Item geometry describes GFM/Equi7 product-tile coverage.
- Copernicus source-product GeoFootprint describes the catalogued original
  Sentinel-1 acquisition-product coverage.
- Neither geometry establishes valid GFM flood-classification pixels or proves
  a river reach was observed usefully.
Do not infer missing geometry, orbit direction or valid-pixel coverage.

Task 3 — Render and inspect pass footprints
Run `f03a-satellite_footprints.sh` using the resulting local catalogues and
metadata. Reuse the existing OSM and CaMa-Flood vector-map method. Show the
candidate Satellite analysis domain, one panel per acquisition pass, source
Sentinel-1 acquisition footprints, UTC time, satellite, orbit direction and
pass identity. Use the same geographic extent and scale across panels. If the
renderer or metadata are unavailable, report the limit and do not claim a
visual review.

Task 4 — Select initial candidate pass(es)
Compare event timing and flood evolution, source-footprint coverage of reported
impact areas, orbit direction, GFM product/layer availability, and fit to the
research objective. Choose a rational initial recommendation or set of
recommendations from available evidence. This is a screening judgment, not a
validated scientific ranking. Record the selection in the fixed
`metadata/03a_selected_passes.json` file with top-level and per-pass `status`
set to `proposed`. Keep only confirmed values; preserve unknowns as null or
omit unavailable optional metadata. Include the rationale and limitations.
Do not use status to block any later script. A `proposed` selection may be
consumed by Step 3b; researcher review is recommended but is not a programmatic
precondition.

The JSON is the Step 3b handoff contract. Use `schema_version`, `event`,
top-level `status`, `source_domain_config`, `required_gfm_layers`, `passes`,
and `limitations`. `source_domain_config` is a path relative to the JSON file
(in `metadata/`). Each pass entry identifies at least `pass_id` and
`catalogue_date`, plus observed orbit/time fields when known, a `status`, and
its selection rationale. Step 3b can map `catalogue_date` and `pass_id` to the
cached STAC pass and request the listed layers, using the bbox from
`02_domain_selection.json`. Status fields document review only: consumers must
not require `approved` to execute.

Task 5 — Present results and iterate
Present the footprint comparison, all searched passes, recommended pass(es),
selection rationale, AOI coverage limitations, orbit/time evidence and open
questions. The researcher may change the period/domain, add or remove passes,
or revise the recommendation. Apply feedback to the existing
`02_domain_selection.json`, `03a_selected_passes.json`, inventories, report,
and Figure(s) as appropriate, then rerun only affected work. Keep the same
filenames. The 3a outputs are useful before researcher review; review is a
recommended scientific process, not a software execution gate.

Task 6 — Finalize the Step 3a record
Update `03_satellite_data_survey.md` with search settings, pass comparisons,
recommended selection, evidence provenance, data-geometry distinctions and
limitations. Retain the fixed Step 3a metadata names and reproducible Shell
entry points. State clearly that no COG was downloaded during Step 3a. Do not
change the Step 3b downloader implementation as part of this survey task.

Do not claim that a source acquisition footprint is valid flood-observation
support, that a proposed pass is approved, or that metadata collection
establishes scientific suitability. Report commands, outputs, inspection
results and unresolved questions.
```

## Expected outputs

| Output | Role |
| --- | --- |
| `03_satellite_data_survey.md` | Search method, pass comparison, rationale and limits |
| `metadata/03a_satellite_pass_inventory.csv` | Pass-level STAC/source-product summary |
| `metadata/03a_satellite_orbit_metadata.csv` | Orbit direction and relative-orbit evidence |
| `metadata/03a_sentinel1_acquisition_footprints.geojson` | Source acquisition geometries and provenance |
| `metadata/03a_selected_passes.json` | Fixed Step 3b pass-selection handoff |
| `s03a-satellite_availability.sh` | Reproducible metadata search workflow |
| `f03a-satellite_footprints.sh` | Reproducible pass-footprint figures |
| `figure/f03a-gfm-pass-footprints-*.png` | Pass-by-pass comparison maps |

The first run should leave a complete proposed selection and report for
researcher review. Subsequent edits update those same files. The Human reviews
the selected coverage, time/orbit reasoning, data limitations and relationship
to the evaluation purpose. `proposed` and `approved` are descriptive metadata;
they do not control whether processing scripts run. Step 3b may consume the
fixed JSON path without requiring approval status. Tutorial 11 already contains
a Rhine 2021 Step 3a sample; this Prompt is for future events and must not be
run there to recreate or alter it.
