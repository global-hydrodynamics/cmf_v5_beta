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
- `figure/f21-gauge_allocation.png` and `figure/f21-catchment_allocation.png`
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

Use `--catchment-only` when reviewing an existing impact table: it enriches that
table without rewriting the gauge CSV or any geographic-assignment column.
Without that flag the original gauge/geographic workflow is followed by the
same catchment enrichment; use it only when establishing the initial tables.

Reuse the p01-f04 reader and boundary method, as illustrated by Tutorial 02
Fig. 1d. Read actual `params.txt`/`location.txt` geometry and verify alignment
with the current model NetCDF axes. Locate the containing high-resolution
pixel using west/north-inclusive and east/south-exclusive edges, north-first
rows and west-first columns. Read the two little-endian int16 catmx/catmy
planes; their values are **one-based regional model x/y indices**, not the
pixel's geographic coarse-grid indices. Convert to row=y−1, col=x−1.
Never snap invalid, unassigned or coordinate-missing points to nearby channels.

Keep `model_row_0based`/`model_col_0based` and all other old columns unchanged.
Add `catmxy_*` fields for the selected model cell, center, outlet, area, width,
basin label and nextxy connection, plus `allocation_changed` and
`river_allocation_status/reason`. Preserve all report/location IDs, repeated
cells and old `ai_notes`; append new evidence with `ai_notes` still rightmost.
Save actual downstream paths and source fingerprints in
`metadata/21_catchment_review.json`. Review Ahr, Erft, Kyll and Prüm topology;
nondecreasing area alone does not establish named-river identity. Use
`confirmed`, `plausible`, `unresolved` or `not_represented` only as justified
by evidence; a valid lookup alone never means confirmed.

Keep the regional Figure and add a companion Ahr–Erft catchment view with
pixel-edge boundaries, standard outlet-based river links and downstream arrows,
reported locations, old geographic outlets and new catmxy outlets. The four
priority locations and their old/new outlets must remain visible. Edit the
companion extent in `f21-gauge_allocation.sh`. Do not modify the reference
Tutorial 02 or Visualization files, regenerate maps, simulate or implement
Step 23. If map data are absent, report the missing inputs rather than inventing
assignments. Update the Survey/Work Reports and retain scientific uncertainties.

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
For later Step 23 work, prefer assigned `catmxy_row_0based` and
`catmxy_col_0based`, carrying river-status and coordinate uncertainty; do not
silently fall back to geographic cells for missing assignments. This Step does
not implement that extraction. The three-gauge CSV remains the Step 22 handoff. A reviewer can compare source coordinates,
grid indices, outlet location, map topology and Figure. Human review is
recommended, but does not gate processing. Do not treat a spatial assignment
as a validated river match or discharge comparison; tributary representation,
time conventions and discharge units may remain unresolved.
