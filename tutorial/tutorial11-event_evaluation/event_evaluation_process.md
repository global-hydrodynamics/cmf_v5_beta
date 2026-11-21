# Flood Event Evaluation Process

**Status:** Reusable process for planning and developing an event evaluation. The
Tutorial 11 Rhine example is still provisional; the process below does not mean
that a complete CaMa-Flood event evaluation has been run.

This document describes six stages that can be adapted to other flood events.
Keep each event's dates, basin IDs, domain bounds, datasets and results in its
event-specific documents. Mark evidence as **implemented and exercised**,
**pilot/example only**, **candidate**, or **not implemented**; do not promote a
candidate setting to a validated choice because a map or script can display it.

## 1. Select the event and hydrologic target

1. Define the flood event, analysis question, relevant dates and rivers from
   documented event sources. Distinguish the flood-producing rainfall period,
   reported impacts, discharge response and satellite acquisition times.
2. Inventory available gauges, model maps, routed network data and authoritative
   watershed evidence. Record source, version and limits for each.
3. Identify candidate CaMa-Flood Basin IDs and inspect their routed connections,
   upstream area, outlets and neighboring basins. Compare the model routing group
   with natural watershed boundaries before naming the simulated basin.
4. Decide whether the target is one natural basin, a model routing group, or
   several separately analyzed groups. Report any combined routing explicitly.
   Reported damage points identify observation priorities; they do not define
   the simulation watershed.

**Tutorial 11 status:** Event background and candidate model basin groups have
been inspected. On the current 0.25° map, Basin ID 74 combines Rhine and
Meuse/Vesdre routing; it is not a pure natural Rhine watershed. Basin ID 1299
also covers nearby cells. Rhine-only versus combined-group scope remains open.
See [event overview](flood_event_overview.md),
[candidate domains](evaluation_domain.md), and
[event setup findings](event_setup_report.md).

## 2. Select separate simulation and observation domains

### Simulation domain

Include the complete selected model-represented watershed and routed network,
including the upstream boundary and downstream outlet. If the executable needs
a rectangular window, derive it from the whole basin and record the margin,
domain mask and boundary treatment. Confirm that map version, grid, forcing,
initialization and configuration support the proposed extent.

### Observation domain

Choose one or more regions from documented impact locations, gauge coverage,
satellite scene footprints and usable-pixel masks. Observation AOIs may be
smaller or non-contiguous; they do not need to equal the simulation domain.
Record each W/S/E/N bbox, time interval, target rivers/locations, data source,
selection rationale and whether coverage is only a candidate.

For a visual review, use the reproducible River Map example
[f06 — OSM Background](../../visualization/river_map/README.md): **f06a** shows
basin/network context and the local extent; **f06b** shows event localities and
candidate observation areas. Its event-specific inputs are kept in the linked
JSON/CSV files. The two Tutorial 11 planning figures are separate event
artifacts; neither f06 nor a town marker proves an observed inundation extent or
satellite coverage.

**Tutorial 11 status:** Candidate simulation and observation bboxes and the
basin/impact planning figures are documented. Basin interpretation, boundary
conditions and observation coverage still need confirmation. Values and
caveats are in [evaluation_domain.md](evaluation_domain.md) and
[event_setup_report.md](event_setup_report.md); the original planning proposal
remains in [event_setup_plan.md](event_setup_plan.md).

## 3. Acquire and preprocess observations

For each product, record provider and version, source identifiers, acquisition
or aggregation time, spatial and temporal support, units, grid/CRS, nodata and
quality masks, processing, citation and redistribution terms. Preserve original
observations and distinguish missing or excluded support from a valid dry
classification. For discharge, confirm station identity, units, time zone,
interval meaning and coordinate-to-model-cell mapping.

For GFM, the demonstrated path uses the separate Atlantis environment and local
STAC/COG workflow. Search and inventory first, identify a same-pass group by
source metadata, acquire only the required native layers, and process that pass
without mixing different acquisitions. Follow the exact commands and outputs in
the [GFM workflow note](gfm_3sec_workflow.md); its `s01`–`s03` steps acquire,
convert and validate the selected 3-arcsecond product. The native 20 m
classification exporter and its class rules are documented there as well. Do
not infer full-event coverage from one pass, a bounding box, or a rendered map.

**Tutorial 11 status:** Supplied discharge files and a 15 July 2021 S1A morning
GFM pass have been inventoried. The one-day GFM acquisition and 3-arcsecond
preprocessing were exercised; a native 20 m classification and inspection
figure were produced. These are limited examples, not a multi-day event dataset
or a completed observation archive. Discharge units/time zone and GFM-specific
redistribution clearance remain unresolved. See the
[observation inventory](observation_data_inventory.md),
[GFM inventory](gfm_data_inventory.md), and
[GFM processing note](gfm_3sec_workflow.md).

## 4. Configure and run CaMa-Flood

After the watershed and domains are approved:

1. Select and record the CaMa-Flood source revision, map/grid version, runoff
   forcing, model configuration, Input Matrix and dimension metadata.
2. Confirm forcing coverage, time step, units, calendar, initialization and
   required upstream inflow. Check domain mask, upstream and outlet boundaries,
   restart policy and output variables/intervals.
3. Set a model period that covers the relevant event response and any necessary
   initialization. Record the exact time convention and runtime environment.
4. Run the model through a documented v5 workflow, retain configuration and
   logs, and apply the checks required for that model change/run. Do not treat a
   successful launch as scientific validation.

The maintained [GOSH workflows](../../gosh_test/README.md) illustrate current
v5 execution conventions; they are not a ready-made Rhine event experiment.

**Tutorial 11 status:** No event-specific CaMa-Flood simulation has been
configured or run. The Rhine-versus-routing-group choice, forcing and
initialization, final domain mask, boundary conditions and event-run settings
must be resolved first. Do not present the current candidate bbox as an
approved simulation setup.

## 5. Match model output to observations

Specify the comparison contract before computing scores:

- **Spatial match:** record the model and observation grids, CRS, cell/area
  treatment, basin/station mapping and any transformation. Preserve valid,
  excluded, permanent-water and nodata semantics. Do not create observations by
  filling uncovered satellite pixels.
- **Temporal match:** compare acquisition intervals or composite support with
  model output support. For gauges, align interval means and timestamp meaning;
  for satellite products, use actual acquisition time and pass/composite
  definition. Do not equate file grouping with temporal averaging.
- **Variable match:** state physical quantity, units, thresholds and masks for
  each comparison. Keep discharge validation separate from inundation-extent
  validation unless a documented method joins them.

Store matched data and its provenance so that a result can be traced to the
original model run and observation product.

**Tutorial 11 status:** No reusable model–observation matching tool or approved
spatial/temporal matching rule has been implemented. Station-cell mapping,
GFM-to-model support treatment and timestamp alignment need an explicit design
before quantitative comparison.

## 6. Evaluate event performance

Choose metrics only after the observation support, matching rules, target
variable and scientific question are agreed. Report the analyzed period and
area, valid sample count, missing/excluded coverage, thresholds, units,
uncertainty and reference data. Separate discharge and satellite flood-extent
results, and distinguish calibration from independent evaluation where both
occur. Include maps or hydrographs that show coverage and timing alongside
summary scores. Do not call unobserved or quality-excluded cells dry, or claim
skill from a single visual overlay.

**Tutorial 11 status:** No event-specific performance metric, model–observation
score, calibration or evaluation result has been implemented. Metrics and
acceptance criteria remain future work, not an implied consequence of the
existing inventory, maps or preprocessing products.

## Current deliverables and open work

| Stage | Current evidence | Remaining before a full evaluation |
| --- | --- | --- |
| Event and watershed | Event background and candidate Basin IDs inspected | Decide hydrologic target and validate model routing against basin evidence |
| Domains | Candidate simulation/observation bboxes and planning maps | Confirm full-basin scope, boundary treatment and valid sensor coverage |
| Observations | Discharge inventory; one GFM pass acquired/preprocessed; native 20 m classification example | Resolve metadata/rights and obtain fit-for-purpose temporal/spatial coverage |
| CaMa-Flood run | Existing v5 build/run documentation and generic GOSH examples | Configure, run and validate a specific event experiment |
| Matching | Data products and their grids/time semantics documented in part | Approve and implement spatial/temporal matching rules |
| Evaluation | No event performance results | Define metrics and report uncertainty and support |

Detailed Rhine event findings remain in the linked event documents. This process
document is the reusable sequence; it does not replace their data inventories,
figures, domain tables, acquisition commands or scientific caveats.
