# p21 — Gauge Allocation

## Workflow Summary

**Inputs**

- The selected gauge inventory and provider station table.
- `metadata/01_impact_locations.csv` and
  `metadata/01_reported_flood_timing.csv` for reported impacts and detailed
  report locations.
- The current event-specific CaMa-Flood map used by the simulation, including
  `1min/location.txt`, `1min/1min.catmxy.bin` and base NetCDF network/outlet fields.
- Existing allocation products, where available.

**Tasks**

- Verify source row/column conventions and map grid coordinates.
- Resolve each candidate to a current-map cell and use its unit-catchment
  outlet coordinates, upstream area and downstream connection.
- Compare the observation and outlet locations, areas and network order.
- Assign each georeferenced impact report to its containing map cell; assess
  named-river correspondence separately, without snapping to a nearby outlet.
- Retain geographic assignments and add one-minute `catmxy` unit-catchment
  assignments, downstream paths and evidence-qualified river status.
- Save separate machine-readable gauge and impact-location handoffs and maps.

**Outputs**

- `metadata/21_gauge_allocation.csv`
- `metadata/21_impact_location_allocation.csv`
- `metadata/21_catchment_review.json`
- `figure/f21a-gauge_allocation.png` and `figure/f21b-catchment_allocation.png`
- Step 21 Survey and Work Reports

## Human Instructions

Adapt the station source, selected-station inventory and current map paths for
the event. Run the allocation check and then render its Figure:

```sh
bash s21-gauge_allocation.sh --catchment-only
bash f21-gauge_allocation.sh
```

The processing script verifies the supplied gauge candidates against the
current map and relevant existing allocation outputs. For impact reports, it
uses the recorded geographic coordinate to identify the containing model cell;
it does not replace that cell with the nearest outlet. It records the outlet,
upstream area and outlet distance, then marks named-river correspondence as
uncertain where the 0.25-degree map cannot establish a local tributary match.
Reports without coordinates remain in the CSV without an inferred location.
The output row/column values are zero-based Python array indices, with row
following the map's latitude array order.

## Catchment-based review contract

Keep three distinct layers in the impact CSV:

1. `model_*`: original geographic containing-cell assignment, unchanged.
2. `catmxy_*`: direct one-minute unit-catchment assignment, unchanged by correction.
3. `river_model_*`: final evaluation cell, normally the direct catmxy cell;
   use a reviewed one-step upstream tributary proxy only for explicitly named
   mainstem-catchment cases. `river_allocation_method`, `river_correction_applied`,
   `river_correction_steps` and `river_correction_reason` explain the selection.

Use `--catchment-only` to enrich an existing table without rewriting geographic
columns or the three-gauge CSV. For initial table creation, omit that flag.
Read actual params/location geometry; reuse the unchanged p01-f04 Binary reader
and pixel-edge boundary method. One-minute pixels use west/north-inclusive and
east/south-exclusive edges, north-first rows and west-first columns. Stored
int16 catmx/catmy are one-based regional model x/y, so row=y−1 and col=x−1.
NoData or missing-coordinate cases remain unassigned; do not snap to a channel.

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

Save full paths/source hashes in `metadata/21_catchment_review.json`. Preserve
all 22 report/location IDs, original notes with appended new evidence, repeated
cells, and ai_notes as the last column. Keep the regional Figure plus the
Ahr–Erft companion showing only the final adopted `river_model_*` outlets
and point connectors. Do not draw geographic or uncorrected alternatives;
retain those fields in the CSV for provenance. Edit its extent in the Shell.
Do not modify reference Tutorial 02/Visualization code or map/simulation inputs.

Existing Step23 code and prior outputs are retained from the remote branch.
It reads final `river_model_*` for plausible/confirmed status and now propagates
the allocation method. Do not reinterpret retained old Step23 outputs as current:
`metadata/23_handoff_status.json` identifies the five report selections that
changed and marks those outputs as requiring explicit re-extraction. Step23
extraction/peak comparison is not run as part of this integration.

## Example AI Agent Prompt

```text
Complete the gauge and reported-impact location allocation for this flood-event tutorial.
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

Create a reusable processing shell/Python pair and a CSV containing the
observation coordinates, original candidate fields, current map's zero-based
row/column, outlet coordinates, map upstream area, distance, area comparison,
allocation comparison and evidence-based decision. If an area unit is not
declared, preserve the source value and leave any derived comparison clearly
conditional or unavailable. Generate a Figure with the current map's river
network, observation gauges, selected outlets and connectors; add local views
if the full-map view cannot show their separation. Also read every Step 01
impact/timing report, retaining `report_id` and `location_id`, and allocate
each georeferenced coordinate to its containing current-map cell. Keep the
geographic cell assignment distinct from the map outlet and from whether that
outlet represents the named river. Do not snap small-tributary locations to a
nearby mainstem. Retain records with missing or out-of-map coordinates and
explain their status. Write these results to a separate
`metadata/21_impact_location_allocation.csv`; do not mix them into the
gauge-only `metadata/21_gauge_allocation.csv`, which remains the Step 22 gauge
handoff. Update the Figure to distinguish gauges, impact localities, detailed
sites and model outlets, and use local views where labels would otherwise
overlap. Add the catchment-based review specified above, preserving all old
columns and the gauge CSV; compare the priority Ahr/Erft assignments and
standard downstream paths, and generate the companion catchment Figure. Create a researcher-facing Survey Report and technical Work Report,
and update the Tutorial process and development log. Do not modify model/map/
source-observation data, extract model flows, calculate performance metrics,
or publish a Gallery item. Human review is recommended but is not a script
execution gate.
```

## Expected Handoff and Review

The gauge CSV is the machine-readable handoff for later discharge extraction.
The impact CSV preserves geographic cells and adds catchment-based candidates.
For later Step 23 work, use final `river_model_row_0based` and
`river_model_col_0based`, carrying correction/river-status uncertainty; do not
silently fall back to geographic cells for missing assignments. This Step does
not implement that extraction. The three-gauge CSV remains the Step 22 handoff. A reviewer can compare source coordinates,
grid indices, outlet location, map topology and Figure. Human review is
recommended, but does not gate processing. Do not treat a spatial assignment
as a validated river match or discharge comparison; tributary representation,
time conventions and discharge units may remain unresolved.
