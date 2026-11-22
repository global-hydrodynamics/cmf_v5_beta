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
See [event overview](01_flood_event_overview.md),
[candidate domains](02_domain_and_observation_design.md), and
[event setup findings](development_log/event_setup_report.md).

## 2. Select separate simulation and observation domains

### Simulation domain

CaMa-Flood represents river-basin water dynamics. For a flood evaluation, the
simulation must include the complete upstream contributing area and routed
network of the target river, together with the required downstream outlet.
Do not define the simulation domain from only the damaged locations, and do not
make a small rectangle an objective in itself. A rectangular model window may
enclose the whole target watershed and include surrounding cells needed for
domain boundaries. A large full-basin domain is appropriate when required by
the evaluation question.

Identify the model Basin IDs from the map data for each event; do not carry a
Basin ID from another map or hard-code an ID as a natural watershed name. Begin
with target rivers, impact localities and gauges from Step 1, map them to cells,
inspect the map's `basin` and `uparea` data, and trace `nextxy` connections to
understand upstream and downstream routing. Check the spatial extent and
neighboring routing groups, then choose a window that contains the full
required watershed and outlet. If basin labels alone do not establish the
connection, use the routed network. Record map name and resolution, IDs,
target watershed, domain bounds, boundary margin, mask and rationale. Model
Basin IDs may combine or divide natural watersheds; state that distinction.
Whether to include a neighboring routing group depends on map connectivity and
the evaluation purpose.

Confirm that map version, grid, forcing, initialization and configuration
support the proposed extent. The satellite/observation domain may be smaller
than the simulation domain.

### Observation domain

Choose one or more regions from documented impact locations, gauge coverage,
satellite scene footprints and usable-pixel masks. Observation AOIs may be
smaller or non-contiguous; they do not need to equal the simulation domain.
Record each W/S/E/N bbox, time interval, target rivers/locations, data source,
selection rationale and whether coverage is only a candidate.

For a visual review, use the reported-impact localities and river systems
summarized in Tutorial Figure 1 and its linked `impact_locations.csv`; carry
those same locations forward into the domain review. Use the reproducible River Map example
[f06 — OSM Background](../../visualization/river_map/README.md): **f06a** shows
basin/network context and the local extent; **f06b** shows event localities and
candidate observation areas. Its event-specific inputs are kept in the linked
JSON/CSV files. In the Tutorial 11 Step 2 figure, show a map extent broader
than the candidate simulation window, the candidate simulation and observation
boxes with distinct labels, and the relevant model routing groups, impacts and
gauges. A processed satellite target grid is evidence about the existing
product; it is not automatically a selected observation domain. If its bounds
are reused as a candidate, document that relationship and show the limited
valid-observation support. Neither a town marker nor a rendered rectangle
proves an observed inundation extent or complete satellite coverage.

Use the sequence **candidate extents → visual review against map connectivity
and event evidence → human decision → documented final domains**. A figure used
for this review presents candidates, not an approved model setup.

**Tutorial 11 status:** Figure 1 summarizes reported impact localities for
Step 1; Figure 2 carries them into the candidate simulation/observation-domain
review. Candidate bboxes and the current map's basin IDs and
location-to-network traces have been inspected, but natural-watershed
interpretation, final inclusion of neighboring routing groups, boundary
conditions and observation coverage still need confirmation. Values and
caveats are in [02_domain_and_observation_design.md](02_domain_and_observation_design.md) and
[event_setup_report.md](development_log/event_setup_report.md); the original planning proposal
remains in [event_setup_plan.md](development_log/event_setup_plan.md).

## 3. Acquire and preprocess observations

For each product, record provider and version, source identifiers, acquisition
or aggregation time, spatial and temporal support, units, grid/CRS, nodata and
quality masks, processing, citation and redistribution terms. Preserve original
observations and distinguish missing or excluded support from a valid dry
classification. For discharge, confirm station identity, units, time zone,
interval meaning and coordinate-to-model-cell mapping.

For GFM, survey catalogue availability before requesting imagery. Read the
event-specific search interval and candidate bbox from the Step 2 configuration,
search one date at a time into separate cache directories, group STAC Items by
verified Sentinel-1 platform/orbit/datatake, and compare both source Sentinel-1
product GeoFootprints and GFM Equi7 tile coverage on a shared map extent. These
are different geometries: tile Items
within a pass are not independent observations, and neither geometry is a map
of valid flood-observation pixels. Select pass IDs for researcher review before
downloading any COGs. For the subsequent acquisition and processing steps, use
the separate Atlantis environment and the local workflow in the [GFM workflow
note](gfm_3sec_workflow.md); its `s01`–`s03` steps acquire, convert and validate
the selected 3-arcsecond product. The native 20 m classification exporter and
its class rules are documented there as well. Do not infer full-event coverage
from one pass, a bounding box, or a rendered map.

**Tutorial 11 status:** The focused 14–16 July 2021 catalogue survey returned
45 STAC Items grouped into 6 acquisition passes over the candidate bbox,
centered on the 15 July disaster date; source acquisition-footprint comparisons
were rendered. The earlier 13–20 July scan remains in development history.
Image assets were not downloaded during the survey. Separately, a 15 July 2021 S1A morning GFM pass was acquired and
3-arcsecond preprocessing was exercised; a native 20 m classification and
inspection figure were produced. These are limited examples, not a complete
multi-day event dataset or observation archive. The local Atlantis environment
was unavailable during the catalogue survey; direct read-only EODC STAC results
were used for this survey and the `s03a-satellite_availability.sh` wrapper is
ready to repeat the metadata search when the environment is available. The
separate `s03b-download_gfm.sh` wrapper acquires the selected native 20 m COG
layers, while `f03a-satellite_footprints.sh` only redraws figures from cached
metadata. Discharge units/time zone
and GFM-specific redistribution clearance remain unresolved. See the
[Step 3a availability survey](03_satellite_availability_survey.md),
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
| Observations | Discharge inventory; catalogue survey of 18 GFM passes; one GFM pass acquired/preprocessed; native 20 m classification example | Review and select passes, resolve metadata/rights, then obtain fit-for-purpose temporal/spatial coverage |
| CaMa-Flood run | Existing v5 build/run documentation and generic GOSH examples | Configure, run and validate a specific event experiment |
| Matching | Data products and their grids/time semantics documented in part | Approve and implement spatial/temporal matching rules |
| Evaluation | No event performance results | Define metrics and report uncertainty and support |

Detailed Rhine event findings remain in the linked event documents. This process
document is the reusable sequence; it does not replace their data inventories,
figures, domain tables, acquisition commands or scientific caveats.
