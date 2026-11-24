# p03a — Satellite Availability Survey

### How to Use This Workflow

**Rhine 2021:** Keep the existing event settings and retained survey; supply
this entire Markdown file as an attachment or copy its full content. Honor the
worked-example no-rerun constraint below.

**Another event:** Set the event/objective and directory placeholders, and review
the search dates and satellite-analysis bounds in the Step 02 domain handoff.
That JSON remains the source of search settings; do not create a duplicate
settings list here. Verify catalogue/footprint access and script dependencies,
then give the entire updated file to the agent for execution. The Rhine pass
IDs and completed-survey status do not apply to the new event.

The execution block is part of the full file, not a standalone Prompt. Review
pass-selection evidence without turning `proposed` into an approval gate.

## Workflow Summary

### Inputs
- `metadata/02_domain_selection.json` and Step 1/2 Survey Reports
- Search dates and candidate satellite-analysis bounds from the Step 2 handoff

### Tasks
- Search GFM/Sentinel-1 catalogue metadata, group Items by source acquisition, compare source footprints, and propose useful pass(es).
- Render a same-extent comparison map and record evidence and limitations.

### Outputs
- `AI_survey_report/03a_satellite_availability.md`
- `AI_work_report/03a_satellite_availability.md`
- Step 3a pass/orbit/footprint metadata and `metadata/03a_selected_passes.json`
- `figure/f03a-gfm-pass-footprints-*.png`

## Human Instructions

Provide the event directory and evaluation objective after Step 2. The agent reads the candidate period and bbox from the domain JSON. Human review of pass recommendations is encouraged but does not gate Step 3b.

## Example AI Agent Prompt

```text
Complete Step 3a satellite availability survey for this event.

Event/objective: [EVENT / PURPOSE]
Event directory: [PATH]

Read the Step 1/2 Survey Reports and `metadata/02_domain_selection.json`. Use
its satellite period and bbox as the initial catalogue search. On the first run,
complete metadata search, pass grouping, source-footprint comparison, initial
recommendation, figure, Survey Report and Work Report. Do not wait for review.

1. Run `run_script/s03a-satellite_availability.sh` for catalogue/orbit metadata only.
   Group GFM Items by verified Sentinel-1 platform, absolute orbit and
   datatake. Distinguish Item, source-product slice, Equi7 tile and acquisition
   pass counts.
2. Run `plot_script/f03a-satellite_footprints.sh`. Use the existing OSM/CaMa vector method,
   one panel per pass, common extent/scale, candidate AOI, source-product
   GeoFootprint, UTC times, satellite, orbit direction and pass ID.
3. Keep geometry meanings separate: GFM STAC geometry is product-tile
   coverage; Copernicus source `GeoFootprint` is source-product acquisition
   coverage. Neither is the distribution of valid flood-classification pixels.
   Do not infer missing observations or geometry.
4. Record the initial pass recommendation as `proposed` in the fixed
   `metadata/03a_selected_passes.json`. Status is descriptive only; Step 3b may
   read a proposed pass. Explain timing, spatial relevance, available layers
   and uncertainty rather than claiming a validated ranking.
5. Create/update `AI_survey_report/03a_satellite_availability.md` and
   `AI_work_report/03a_satellite_availability.md`. Include the pass comparison,
   selection rationale, exact outputs, commands/checks actually performed,
   limitations and handoff. Do not claim COG download during Step 3a.

If feedback is provided, revise the same selection/metadata/report files and
regenerate affected figures. No response leaves complete outputs proposed and
available to Step 3b. Do not create versioned copies or modify the downloader.
```

## Evidence and limitations

A product footprint is not proof of valid flood pixels, flood detection quality, or useful coverage of a river reach. The current Tutorial 11 survey is a worked example; do not rerun it or reuse its pass IDs for another event.
