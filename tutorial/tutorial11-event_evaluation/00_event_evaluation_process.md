# Flood Event Evaluation Process

**Status:** Reusable process for planning and developing an event evaluation. The
Tutorial 11 Rhine example is still provisional; the process below does not mean
that a complete CaMa-Flood event evaluation has been run.

This document describes six stages that can be adapted to other flood events.
Keep each event's dates, basin IDs, domain bounds, datasets and results in its
event-specific documents. Mark evidence as **implemented and exercised**,
**pilot/example only**, **candidate**, or **not implemented**; do not promote a
candidate setting to a validated choice because a map or script can display it.

## Agent-driven workflow and file roles

A reusable `pXX-*.md` Prompt is the entry point for an AI agent to carry out a
research Step. On the first run, the agent completes the available
investigation, prepares and executes necessary processing/visualization
scripts, records evidence-based recommendations and settings as `proposed`,
and presents the result. The researcher reviews scientific meaning and fit to
the research purpose, gives feedback, and may request revisions. The agent
updates the same files and reruns affected work; iteration has no fixed count.
An agent does not silently represent its recommendation as a Human-approved
scientific decision. Status fields document review state only; they are not
program execution gates. A later Step may use complete `proposed` values unless
a separate scientific or data-access rule requires a decision.

- `pXX-*.md` describes and guides the complete Agent Workflow; it is not a
  substitute for the executed research result.
- `sXX-*.sh` reproduces applicable data acquisition, processing or calculation
  from saved inputs and settings.
- `fXX-*.sh` regenerates Figures from saved inputs and final display settings,
  without requiring the agent's exploratory session.
- `01_*.md`, `02_*.md`, etc. record research results, rationale and uncertainty.
- CSV/JSON catalogs, handoff values and event-specific settings belong under
  `metadata/` where appropriate. Prefix metadata filenames with their owning
  Step number (for example, `02_domain_selection.json` and
  `03a_satellite_pass_inventory.csv`) unless a file is intentionally shared
  across Steps. A downstream handoff uses one fixed filename; revise its
  contents in place instead of adding `_v2` or `_final` variants.

Prompts, reproducible Shell workflows and research outputs serve different
purposes. Save the adopted processing and final reviewed Figure settings; do
not create Shells for every exploratory attempt. A Prompt may direct an agent
to create or update the needed `sXX` and `fXX` entry points and run them. This
Tutorial's Rhine 2021 files are a worked sample and are not rerun when a Prompt
is adapted for another event.

## 1. Select and research the flood event

For a new event, the Human provides its name, region/year and research
objective, then gives the AI agent the reusable [Step 1 event research
workflow](p01-event_research.md). The agent researches traceable papers,
public reports and reliable news; distinguishes evidence, interpretation and
uncertainty; creates `01_flood_event_overview.md` and
`metadata/01_impact_locations.csv`; prepares and runs
`f01-reported_flood_impacts.sh`; and visually checks Figure 1. It presents the
sources, outputs and remaining questions to the Human. The Human reviews the
science, sources, location choices and map, then gives feedback. The agent
revises and reruns applicable work as needed until the Human accepts the result.
Keep the final Figure reproducible from its CSV, saved display settings and
Shell. Literature research itself need not be reproducible by Shell.

Do not finalize CaMa-Flood Basin IDs, routing groups, simulation bounds or
satellite-analysis domains during Step 1; those decisions require the map-based
Step 2 assessment. The accepted overview and impact inventory provide Step 2's
river, locality, timing and uncertainty evidence.

**Tutorial 11 status:** The Rhine 2021 sample already contains the event overview,
`metadata/01_impact_locations.csv`, Figure 1 and its generation Shell. These
are retained as the worked example; the reusable Prompt is not run to recreate
or replace them. See [event overview](01_flood_event_overview.md),
[candidate domains](02_analysis_domain_design.md), and
[event setup findings](development_log/event_setup_report.md).

## 2. Design simulation and observation domains with Human–AI review

Step 2 turns the event evidence and impact locations from Step 1 into a
map-specific, reviewable spatial design. For a new event, use the reusable
[Step 2 analysis-domain instructions](p02-analysis_domain.md) in that
event's own directory. Tutorial 11's Rhine 2021 materials are a worked
example; do not rerun the prompt there or copy its map IDs, extents or station
set to another event.

The agent reviews the Step 1 evidence and selected map, proposes initial
domains, prepares and runs `f02-analysis_domain.sh`, and presents the Figure,
routing evidence, bounds and open questions to the Human. Researcher review
and iteration are recommended parts of the scientific process; the initial
complete `proposed` design may be passed to a later Step without waiting for
approval. When feedback is available, the agent adjusts domains or Figure
settings and reruns affected work. Status is descriptive metadata, not an
execution condition. Save the current settings, rationale and reproducible
Shell for Step 3; do not represent a candidate as approved without the
researcher's decision.

The workflow is iterative:

1. Review the Step 1 overview, `metadata/01_impact_locations.csv`, Figure 1,
   and any researcher-specified target rivers or gauges.
2. Inspect the selected CaMa-Flood map and version. Associate target reaches,
   impacts and gauges with model cells; use `basin`, `uparea` and `nextxy` to
   identify model routing groups, upstream contributing networks and the
   necessary downstream outlet. Derive Basin IDs from the selected map rather
   than carrying IDs across maps or events.
3. Propose a **simulation domain**, a **satellite analysis domain**, and a
   **map viewing extent** as separate things. The simulation domain must
   include the target river's required upstream contributing area, routed
   network and downstream outlet; do not choose it from damaged locations
   alone or minimize its size as an objective. A rectangular model window may
   include surrounding cells and neighboring groups where map connectivity
   and the evaluation question require them. The satellite analysis domain may
   be smaller or non-contiguous. Until actual acquisition footprints and
   usable-observation masks are checked, label it as a candidate. The viewing
   extent is only the Figure viewport and does not define either domain.
4. Generate candidate Figure 2 using the selected map, event locations,
   available observation sites and clearly differentiated candidate boxes.
   Choose a broad enough viewport to explain the geographic context; label
   proposed bounds as candidates and distinguish them from processed product
   coverage.
5. On the initial Prompt run, choose and save the best-supported candidate
   domains, mark their review state `proposed`, and generate Figure 2 before
   presenting the result. Do not wait for Human approval to produce the first
   complete candidate. The researcher may then review and request revisions;
   the agent updates the same settings and reruns the Figure as needed. There
   is no preset review-round count. A viewport-only change must not be recorded
   as a change to an analysis domain.
6. Record the evidence, rationale, uncertainty and questions in
   `02_analysis_domain_design.md`. Store spatial/temporal handoff values in the
   fixed `metadata/02_domain_selection.json`; use `proposed`, `approved` or
   `undecided` as descriptive status where appropriate. Keep event-specific
   Figure settings in metadata and ensure `f02-analysis_domain.sh` regenerates
   Figure 2 from the saved settings. Status does not gate the Shell or later
   Steps when required values are present.
7. Hand the reviewed domain design and its caveats to Step 3. Later evidence
   about actual satellite coverage, forcing support or model boundaries may
   justify revisiting a candidate.

Model Basin IDs and natural watersheds are not necessarily one-to-one. Check
whether a routing group combines or divides natural basins, and use routed
connections when basin labels alone cannot establish the target network. A
successful map render is not hydrologic validation, proof of complete satellite
coverage, or approval of model boundary conditions.

**Tutorial 11 status:** Figure 1 summarizes reported impact localities for
Step 1; Figure 2 carries them into a provisional Rhine 2021 domain review. On
the current 0.25° `glb_15min` map, Basin ID 74 combines Rhine and Meuse/Vesdre
routing and is not a pure natural Rhine watershed; Basin ID 1299 includes the
nearby Gete/Dyle localities. The map routing-group associations, candidate
bboxes and location-to-network traces have been inspected, but
natural-watershed interpretation, final inclusion of neighboring routing
groups, boundary conditions and observation coverage still need confirmation.
The candidate simulation and satellite bounds remain provisional. Values and
caveats are in [02_analysis_domain_design.md](02_analysis_domain_design.md);
the original planning proposal and setup findings remain in
[development_log/event_setup_plan.md](development_log/event_setup_plan.md) and
[development_log/event_setup_report.md](development_log/event_setup_report.md).

## 3. Acquire and preprocess observations

For a new event's GFM survey, use [p03a — Satellite Availability Agent
Workflow](p03a-satellite_availability.md). On its first run, the agent reads
`metadata/02_domain_selection.json`, runs `s03a-satellite_availability.sh` for
catalogue/orbit metadata only, renders pass comparisons with
`f03a-satellite_footprints.sh`, and records an evidence-based initial
recommendation in the fixed `metadata/03a_selected_passes.json`. The initial
selection is `proposed`; it is ready for Human review but is not blocked from
being read by a later Step. Feedback updates the same settings, metadata and
figures rather than creating versioned copies.

`03a_selected_passes.json` is the intended Step 3b input contract: it identifies
pass IDs, catalogue dates and requested layers. Its `status` fields describe
review state and must not be treated as an execution gate. Existing download
Shells retain their ordinary input/file checks; this workflow update does not
add approval checks or alter download behavior. The current Tutorial 11
`s03b-download_gfm.sh` is not yet wired to read this selection JSON.

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
of valid flood-observation pixels. Record an initial pass recommendation in the fixed
`metadata/03a_selected_passes.json` and present it for researcher review; the
`proposed` status is descriptive and does not gate a later Step. For the subsequent acquisition and processing steps, use
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
separate `s03b-download_gfm.sh` wrapper currently acquires its explicitly
configured native 20 m COG layers; it is not yet wired to read
`metadata/03a_selected_passes.json`. `f03a-satellite_footprints.sh` redraws
figures from cached metadata. Discharge units/time zone
and GFM-specific redistribution clearance remain unresolved. The
`S1A_o038784_dt049389` first-processing candidate is recorded as `proposed` in
`metadata/03a_selected_passes.json`; this does not certify its coverage or
require an approval state for later execution. See the
[Step 3a satellite data survey](03_satellite_data_survey.md),
[observation inventory](observation_data_inventory.md),
[GFM inventory](gfm_data_inventory.md), and
[GFM processing note](gfm_3sec_workflow.md).

## 4. Configure and run CaMa-Flood

Use the current Step 2 domain values when they contain the inputs required by
the model. Their `proposed`/`approved` labels document research review; they
do not block scripts from running. Human review is recommended before treating
the chosen setup as a scientifically accepted evaluation design:

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
