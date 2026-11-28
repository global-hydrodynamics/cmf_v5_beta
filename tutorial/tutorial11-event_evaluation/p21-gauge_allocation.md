# p21 — Gauge Allocation

### How to Use This Workflow

**For Rhine 2021:** Use the current configuration unchanged. Provide the entire
`p21-gauge_allocation.md` file to an AI agent as an attachment or by copying its
full Markdown content, and ask it to execute the workflow using these instructions
and the current repository context.

**For another flood event:**

1. Read Section 5, *Adaptation to Another Event*.
2. Edit Section 2, *Event-Specific Configuration*, for the new event, model map,
   observation datasets, study settings and event-specific scientific decisions.
3. Review the other sections for assumptions and implementation dependencies
   that may not transfer. Editing Section 2 alone does not make the existing
   scripts compatible with another region.
4. Provide the **entire updated Markdown file** to the AI agent. Ask it to inspect
   the existing scripts and inputs, adapt event-specific implementation where
   needed, and execute only after the necessary prerequisites and scientific
   decisions are established. Such implementation changes belong to that later
   application, not this documentation refinement.

**Sections 1–5 together constitute the complete workflow instructions. Do not
copy or execute Section 3 alone.** The entire Markdown file is the unit of reuse;
read all sections together under the applicable repository instructions.

## Workflow Summary

- **Inputs:** Selected gauge inventory and provider metadata; Step 01 impact/timing
  inventories; the simulation's current map and native catchment assignments;
  existing allocation products. Section 2 identifies the Rhine 2021 inputs.
- **Tasks:** Check coordinates/indices, outlets, upstream areas and connectivity;
  keep geographic, direct catchment and final river allocations distinct;
  apply only the specified event review; retain evidence and uncertainty.
- **Outputs:** Separate gauge and impact CSV handoffs, catchment-review metadata,
  regional/companion Figures, and Step 21 Survey/Work Reports (Section 4).

## 1. General Workflow

### 1.1 Gauge candidates and current-map correspondence

Inspect the repository and Tutorial instructions, the current simulation map,
the selected gauge inventory and the original station metadata. Treat the
current map used by the experiment as authoritative; do not assume an older
map's allocation remains valid.

For each selected gauge, establish the source row/column convention and map
grid alignment before indexing. Inspect the current map's outlet longitude and
latitude, upstream drainage area and nextxy network. Compare the supplied
candidate and any available existing allocation product with the current-map
cell. Measure station-to-outlet distance, check drainage-area correspondence
with explicit units, and verify relevant downstream station ordering by
following nextxy. Use unit-catchment outlet coordinates for model locations,
not grid centers. Do not optimize allocations using model-observation flow
agreement or replace a candidate by simple nearest-cell search.

If an area unit is not declared, preserve the source value and leave any derived
comparison clearly conditional or unavailable. Output row/column values are
zero-based Python array indices, with row following the map's latitude array
order. Read actual params/location geometry; the current study's native-grid
representation and pixel-edge conventions are specified in Section 2.

### 1.2 Geographic assignment and catchment-based river review

Read every Step 01 impact/timing report, retaining `report_id` and `location_id`.
For each georeferenced coordinate, identify the containing current-map cell and
record its outlet, upstream area and outlet distance. Keep that geographic
assignment distinct from the outlet location and from whether the outlet
represents the named river. Assess named-river correspondence separately; do
not snap small-tributary locations to a nearby mainstem or nearest outlet.
Reports without coordinates or outside the map remain in the CSV without an
inferred location, with their status explained.

Read geometry from `params.nml` and the auxiliary grid from `location.csv`.
Use `1min/1min.catmxy.nc` (`catmxx` and `catmyy` on `(lat, lon)`) for the
stored high-resolution pixel-to-river-cell assignment;
use `nextxy` for downstream connectivity and downstream paths, not to infer
the pixel's catchment membership. Keep three distinct layers in the impact CSV:

1. `model_*`: original geographic containing-cell assignment, unchanged.
2. `catmxy_*`: direct native unit-catchment assignment, unchanged by correction.
3. `river_model_*`: final evaluation cell, normally the direct catmxy cell.
   The reviewed exception for explicitly named mainstem-catchment cases is
   specified in Section 2; it is not a general upstream-selection algorithm.
   `river_allocation_method`, `river_correction_applied`,
   `river_correction_steps` and `river_correction_reason` explain the selection.

Retain downstream paths and evidence-qualified river status. NoData or
missing-coordinate cases remain unassigned; do not snap to a channel.
Preserve all old columns, repeated cells and original notes with appended new
evidence, and keep ai_notes as the last column. Figure and handoff contracts
are in Section 4; do not mix impact records into the gauge-only CSV.

## 2. Event-Specific Configuration — Rhine 2021

### 2.1 Inputs and native-grid contract

Use the simulation's current `map/Rhine_15min/` map: 15 arcmin (0.25°),
40 × 32 cells, with a 600 × 480 one-minute auxiliary grid. Inputs are:

- Selected gauges in `metadata/02_gauges.csv` and provider station table
  `observation/stations_data/allstations.csv`: the three Rhine gauges Lobith,
  Speyer and Maxau.
- `metadata/01_impact_locations.csv` and
  `metadata/01_reported_flood_timing.csv` for the existing 22 impact/timing
  report/location records.
- `params.nml`, `1min/location.csv`, `1min/1min.catmxy.nc` and base individual
  NetCDF network/outlet fields stored directly under the map root, together
  with available existing allocation products.

Reuse the p01-f04 current NetCDF reader and pixel-edge boundary method.
One-minute pixels use west/north-inclusive and east/south-exclusive edges,
north-first rows and west-first columns. Stored `catmxx`/`catmyy` are one-based
regional model x/y, so row=y−1 and col=x−1. Where the 0.25-degree map cannot
establish a local tributary match, mark named-river correspondence as uncertain.
These are the current Rhine map's contracts, not assumed properties of every
future map or dataset.

### 2.2 Reviewed lower-Ahr exception and inherited evidence

For this event, the five lower-Ahr reports listed in `UPSTREAM_AHR_REPORTS`
use the directly mapped Schuld catchment as their reviewed tributary anchor.
The candidate must flow **directly into the raw catmxy cell** in standard
nextxy, have valid outlet/channel data and a smaller positive upstream area.
If that cannot be verified, leave the evaluation cell unresolved. Never choose
an arbitrary incoming branch, largest area, or nearest outlet. The corrected
cell is an upstream proxy, omitting downstream tributary area; this does not
establish the exact local reach or flood-wave timing. Keep the status plausible.
All other valid points retain direct catmxy. Existing Kordel basin/cell-scale
confirmation is inherited from the remote scientific review, not newly validated
by this integration. The previous review is retained in `prior_*` fields;
`catmxy_river_allocation_status/reason` retain the direct-lookup assessment.

The existing named set comprises `impact-ahr-altenahr`, `peak-ahr-altenahr`,
`impact-ahr-bad-neuenahr`, `impact-ahr-sinzig` and `peak-ahr-bad-bodendorf`;
the directly mapped anchor is `impact-ahr-schuld`. This identifies the current
reviewed cases without authorizing correction of other reports or transferring
the Ahr choice to another river system.

### 2.3 Current entry points, views and downstream state

Run the allocation check and then render its Figures:

```sh
bash run_script/s21-gauge_allocation.sh --catchment-only
bash plot_script/f21-gauge_allocation.sh
```

Use `--catchment-only` to enrich an existing table without rewriting geographic
columns or the three-gauge CSV. For initial table creation, omit that flag.
The existing processing script verifies supplied gauge candidates against the
current map and relevant existing allocation products. Keep the regional Figure
plus the Ahr–Erft catchment companion specified in Section 4; edit its extent in
the Shell.

Step 23 uses final river_model indices and propagates the allocation method.
It has been rerun on 2026-11-24 with these cells; current output fingerprints
are in `metadata/23_handoff_status.json`. Any later allocation change requires
checking that fingerprint and re-extracting Step 23 as appropriate.

## 3. Agent Execution Instructions

This section is the execution directive within the full document, not a
standalone copy-and-paste Prompt. Read and apply Sections 1–5 together; the
references below rely on the complete file being supplied.

```text
Complete the gauge and reported-impact location allocation for the intended
flood-event study. Read Section 1 (General Workflow), Section 2 (Event-Specific
Configuration), and Section 4 (Outputs and Handoff) before execution. Confirm
that the configured map, inventories and reviewed decisions apply to this study;
for a different event, review Section 5 rather than carrying over Rhine choices.

Establish source/map coordinate and indexing conventions before allocating
selected gauges. Compare current-map candidates, stored outlets, upstream areas
with explicit or conditional units, outlet distances and downstream station
order using Section 1.1. Keep the geographic containment of every Step 01 report
separate from direct native catmxy and final river correspondence as required
by Section 1.2. Preserve missing/out-of-map assignments and their explanations.

Apply the native-grid conventions and exactly the event-specific review in
Section 2. In the current Rhine study, use the existing entry points and the
reviewed Schuld-based Ahr exception only for the named reports. Compare the
priority Ahr/Erft assignments and standard downstream paths; preserve old
columns and the gauge CSV during catchment-only enrichment. Do not broaden the
exception or choose another branch when its required evidence fails.

Provide the reusable processing Shell/Python pair and machine-readable outputs
specified in Section 4, reusing the existing pair for the current workflow.
Save separate gauge/impact tables and the catchment-review provenance. Render
the regional and companion Figures with the stated outlet/connector and view
requirements. Create the researcher-facing Survey Report and technical Work
Report, and update the Tutorial process and development log. Preserve the
Step 22/23 handoff and uncertainty contracts and all scope restrictions in
Section 4. Human review is recommended, not a script execution gate.
```

## 4. Outputs and Handoff

### 4.1 Products and preservation

- `metadata/21_gauge_allocation.csv`: observation coordinates, original
  candidate fields, current map's zero-based row/column, outlet coordinates,
  map upstream area, station-to-outlet distance, area comparison, allocation
  comparison and evidence-based decision.
- `metadata/21_impact_location_allocation.csv`: separate report-linked
  geographic, direct catchment and final evaluation allocations, with the
  evidence/uncertainty fields and preservation rules in Sections 1–2. Retain all
  report/location IDs in the configured inventory.
- `metadata/21_catchment_review.json`: full paths/source hashes and review
  evidence.
- `figure/f21a-gauge_allocation.png` and
  `figure/f21b-catchment_allocation.png`: the regional Figure and the current
  event-specific companion specified in Section 2.3. Show the current map's river network, observation
  gauges, impact localities, detailed sites, final adopted `river_model_*`
  outlets and point connectors, with local views where full-map separation or
  overlapping labels require them. Do not draw geographic or uncorrected
  alternatives; retain those fields in the CSV for provenance.
- Step 21 researcher-facing Survey Report and technical Work Report, plus the
  Tutorial process/development-log update. The reusable processing Shell/Python
  pair is already provided by the current workflow; its paths are in Section 2.

Do not modify reference Tutorial 02/Visualization code or model/map/
source-observation data. Do not extract model flows, calculate performance
metrics, or publish a Gallery item as part of Step 21.

### 4.2 Downstream consumers and scientific review

The gauge CSV is the machine-readable Step 22 handoff for later discharge
extraction. The impact CSV preserves geographic cells and adds catchment-based
candidates and final evaluation cells. For later Step 23 work, use final
`river_model_row_0based` and `river_model_col_0based`, carrying the allocation
method and correction/river-status uncertainty; do not silently fall back to
geographic cells for missing assignments. Step 21 does not implement that
extraction. The current Rhine Step 23 state is recorded in Section 2.3.

A reviewer can compare source coordinates, grid indices, outlet location, map
topology and Figures. Human review is recommended but does not gate processing.
Do not treat a spatial assignment as a validated river match or discharge
comparison; tributary representation, time conventions and discharge units may
remain unresolved.

## 5. Adaptation to Another Event

| Action | Items to reconsider |
| --- | --- |
| **Replace** | Event map/observation paths, station and impact/timing inventories and IDs, geographic bounds, figure views, and the current event's dated downstream status. |
| **Verify** | Actual map geometry, coordinate/array order, stored x/y indexing, native resolution and Binary layout, pixel-edge rules, units, missing values, input compatibility, outlet/channel data, connectivity and existing allocations. The current runnable pair has Rhine-specific selections; do not assume a generic Prompt makes that implementation event-independent. |
| **Scientific Review** | Named-river correspondence, ambiguous tributaries and any proposed proxy. The Schuld anchor, five lower-Ahr exceptions and inherited Kordel status do not transfer automatically; the Ahr procedure is not arbitrary upstream snapping or an outlet/area ranking rule. |
| **Reuse** | Evidence-based candidate checks, outlet-based model locations, distinct geographic/direct/final layers, explicit uncertainty, separate gauge/impact handoffs and the processing/reporting principles in Sections 1 and 4. |
