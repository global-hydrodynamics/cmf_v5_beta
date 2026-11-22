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
and leaves outputs ready for the next Step. Human review is recommended, not a
workflow gate: the researcher may give feedback and request revisions, while
no response leaves complete outputs `proposed` and the workflow continues.
When the researcher reviews and adopts a recommendation, record it as
`approved` where the output has a review-status field. The agent updates the
same files and reruns affected work when requested; it does not wait for a
response, approval, or a fixed iteration count. Status fields document review
state only and never control execution. Ordinary processing errors, including
missing required inputs, are handled as before. This is fail-open with respect
to review status: absent Human approval does not pause the workflow, while
missing inputs or other ordinary processing failures still do.

- `pXX-*.md` describes and guides the complete Agent Workflow; it is not a
  substitute for the executed research result.
- `sXX-*.sh` reproduces applicable data acquisition, processing or calculation
  from saved inputs and settings.
- `fXX-*.sh` regenerates Figures from saved inputs and final display settings,
  without requiring the agent's exploratory session.
- `01_*.md`, `02_*.md`, etc. record research results, rationale and uncertainty.
- CSV/JSON catalogs, handoff values and event-specific settings belong under
  `metadata/` where appropriate. Name Step-owned metadata with its producing
  Step prefix: `01_`, `02_`, `03a_`, `03b_`, `03c_` or `03d_`. Keep that
  prefix when a later Step consumes the file. Use `event_` for event-specific
  settings shared across Steps; retain the existing names
  `event_figure_settings.json` and `event_map_extents.csv`. A downstream
  handoff uses one fixed filename; revise its contents in place instead of
  adding `_v2` or `_final` variants.
- Name Python files under `script/` for their parent workflow: use `sXX-*`
  when called by the `sXX` processing workflow; use `fXX-*` only when used by
  one Figure workflow and not by an `sXX` workflow. If both `sXX` and `fXX`
  use the same Step-specific code, name it `sXX-*`. Use `event_*` only for
  code shared across different Steps. The prefix identifies the parent Step,
  not an internal processing order.

Prompts, reproducible Shell workflows and research outputs serve different
purposes. Save the current processing and Figure settings, including their
proposed/reviewed status where applicable; do not create Shells for every
exploratory attempt. A Prompt may direct an agent to create or update the
needed `sXX` and `fXX` entry points and run them. This Tutorial's Rhine 2021
files are a worked sample and are not rerun when a Prompt is adapted for
another event.

## 1. Select and research the flood event

For a new event, the Human provides its name, region/year and research
objective, then gives the AI agent the reusable [Step 1 event research
workflow](p01-event_research.md). The agent researches traceable papers,
public reports and reliable news; distinguishes evidence, interpretation and
uncertainty; creates `01_flood_event_overview.md` and
`metadata/01_impact_locations.csv`; prepares and runs
`f01-reported_flood_impacts.sh`; and visually checks Figure 1. It presents the
sources, outputs and remaining questions to the Human. Human review of the
science, sources, location choices and map is recommended. If the researcher
does not respond, the complete Step 1 outputs remain proposed and can be used
by Step 2; they are not treated as approved. Feedback may prompt revisions to
the same files and reruns of affected work, without waiting for an iteration
to be declared complete. Keep the Figure reproducible from its CSV, saved
display settings and Shell. Literature research itself need not be
reproducible by Shell.

Do not finalize CaMa-Flood Basin IDs, routing groups, simulation bounds or
satellite-analysis domains during Step 1; those decisions require the map-based
Step 2 assessment. The Step 1 overview and impact inventory provide Step 2's
river, locality, timing and uncertainty evidence, with their review status
recorded separately from their availability as inputs.

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
7. Hand the current domain design and its caveats to Step 3, whether it remains
   `proposed` or has been reviewed. Later evidence about actual satellite
   coverage, forcing support or model boundaries may justify revisiting a
   candidate.

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
review state and must not be treated as an execution gate. The Tutorial 11
`s03b-download_gfm.sh` reads the selected pass/date/layers and the Step 2
satellite-analysis bounds, acquires the native 20 m COGs under the ignored
`Atlantis/` directory, then writes a download manifest and summary for each
pass. Existing acquisitions are reused on rerun.

The handover files are stored beside the acquisition metadata as
`Atlantis/catalogue/<date>/metadata/download_manifest_<pass-id>.csv` and
`download_summary_<pass-id>.json`. Each CSV `local_path` is relative to the
Tutorial's `Atlantis/` root. The Summary's `dataset_root` is `Atlantis` relative
to the Tutorial directory, and its `manifest_path` is relative to that root;
p03c resolves CSV paths from `dataset_root`. The summary's `ready_for_p03c` is
computed from selected Item/layer correspondence, file presence, recorded
size/checksum and GeoTIFF readability. It does not
depend on Human review or the selection's `proposed`/`approved` status. p03c
uses the Manifest as its input list and does not repeat STAC search or download;
it must not proceed with incomplete or unreadable inputs. Regenerate the
handover without acquiring data by running
`script/s03b-build_download_manifest.py` with the selection, catalogue and
Atlantis-root arguments used by the Shell.

### p03c — Native 20 m classification mosaic

Run `bash s03c-classify_gfm_extent.sh` to create a one-band, lossless uint8 COG in
`observation/GFM_extent/` from the p03b Manifest. For each pass, p03c reads the
Satellite analysis domain bbox from Step 2's
`metadata/02_domain_selection.json`, projects its WGS84 boundary with edge
densification, and clips the classification mosaic to the smallest outward
pixel-aligned rectangle that contains that projected AOI. The output keeps the
source Equi7 Europe CRS, 20 m pixel size and pixel alignment; it does not
reproject, resample, or apply an exact polygon mask. Its bounds and dimensions
are recorded with the original WGS84 bbox in the neighboring processing JSON.
Each selected pass is written separately. For the current S1A 2021-07-15 pass,
the output name is
`GFM_S1A_20210715_o038784_dt049389_extent20m.tif`; its neighboring JSON records
the input Manifest/Summary, source COG hashes, grid, class counts and processing
order. A small inspection image and temporary processing files are kept only
under ignored `Atlantis/runs/p03c/`.

The script reuses the existing `script/s03c-gfm_20m_class.py` class
encoding and `event_gfm_common.merge_observation` rules. Source codes remain
unchanged: flood and water extent use 0/1/255, reference water uses 0/1/2/255,
and exclusion uses 0/1/255. The derived class codes are 0 Land, 1 Flood,
2 Permanent water, 3 Seasonal water, 4 Other water, 5 Exclusion,
6 Inconsistent, and 255 NoData. The earliest Item with jointly known flood
and water values and no exclusion owns each valid pixel; reference water only
refines an observed water pixel. Reference-only coverage remains NoData.
Exclusion is kept distinct from missing coverage, and incomplete or conflicting
flood/water classifications are not silently treated as dry.

**Tutorial 11 p03c result:** The selected `S1A_o038784_dt049389` pass (11 STAC
Items, 37 input COGs; 52,333,157 input bytes) produced an AOI-clipped 17,835 ×
19,783 pixel COG of 23,445,565 bytes. Its EPSG:27704 bounds are
`[4390700, 1804600, 4747400, 2200260]` metres, containing the projected Step 2
WGS84 bbox `[4, 49, 8, 52]` with 20 m source-grid alignment. Class counts are
0=91,484,129; 1=182,974; 2=3,372,171; 3=111,433; 4=0; 5=157,602,754;
6=62,162; 255=100,014,182. The counts sum to the 352,829,805 output pixels.
The mosaic recorded 274,817 overlapping valid candidates, with 244 flood and
244 water classification conflicts; the existing deterministic earliest-Item
rule was retained and its counts are in the provenance JSON. Every pixel in
the AOI output matched the corresponding window of the previous full-extent
COG (352,829,805 pixels; zero differences). This consistency check does not
independently validate GFM scientific interpretation or event-wide coverage.

The earlier 30,000 × 30,000 pixel, 32,093,269-byte full-tile output was
replaced using the same filename. AOI clipping reduced the pixel count by
60.8% and the file size by 8,647,704 bytes (27.0%).

The default command expects a Python environment with rasterio, NumPy and
Matplotlib. Re-running `bash s03c-classify_gfm_extent.sh` updates the fixed
GeoTIFF and JSON filenames from the current Manifest and Step 2 AOI. Do not add
the large p03b source COGs under `Atlantis/` to Git; the AOI-clipped
classification COG and its processing JSON are inputs for later Tutorial
steps.

For a compact view of the selected pass, run
`bash f03c-flood_fraction_1min.sh`. It bins native 20 m pixel centres into
global WGS84 1-arc-minute cells inside the Step 2 satellite-analysis bbox
(west/south inclusive, east/north exclusive), without reprojecting or
resampling the source raster. Flood Fraction is class-1 pixels divided by
class-0–4 pixels, in percent; classes 5, 6 and 255 are excluded. A cell with
no valid classified pixels is NoData, while a covered cell with zero Flood
pixels is a valid 0%. The Git-tracked output is
`observation/GFM_extent/GFM_S1A_20210715_o038784_dt049389_floodfrac_1min.tif`;
the valid-pixel count companion is kept under ignored `Atlantis/analysis/`.
The OSM/CaMa context Figure is
`figure/f03c-gfm_flood_fraction_1min.png`; it overlays purple reported-impact
localities and names from `metadata/01_impact_locations.csv`. These reported
locations are distinct from satellite-detected Flood pixels. This derived
fraction map is a spatial screening aid, not a replacement for the native
classification or an independent validation of GFM observations. To redraw the
Figure from the existing fraction raster without rerunning aggregation, use
`bash f03c-flood_fraction_1min.sh --figure-only`.

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
`proposed` status is descriptive and does not gate a later Step. For the
subsequent acquisition and processing steps, use the separate Atlantis
environment and the local scripts under `script/`. Earlier `s01`–`s03` steps
acquire, convert and validate the selected 3-arcsecond product. Do not infer
full-event coverage from one pass, a bounding box, or a rendered map.

**Tutorial 11 status:** The focused 14–16 July 2021 catalogue survey returned
45 STAC Items grouped into 6 acquisition passes over the candidate bbox,
centered on the 15 July disaster date; source acquisition-footprint comparisons
were rendered. The earlier 13–20 July scan remains in development history.
Image assets were not downloaded as part of the catalogue survey itself.
Separately, the selected 15 July 2021 S1A morning pass has 11 Items and 37
native 20 m COGs (49.91 MiB) in the ignored Tutorial-local `Atlantis/` store.
Its per-pass download manifest and summary record file paths, integrity and
readiness for p03c. p03c produced one native-grid classified COG in the
Tutorial's Git-managed `observation/GFM_extent/`; it and its class counts are
recorded above. The earlier 3-arcsecond preprocessing remains a limited
example, not a complete multi-day event dataset or observation archive. The
local Atlantis environment
was unavailable during the catalogue survey; direct read-only EODC STAC results
were used for that survey, and the `s03a-satellite_availability.sh` wrapper is
ready to repeat the metadata search when the environment is available.
`s03b-download_gfm.sh` reads `metadata/03a_selected_passes.json`, reuses matching
local COGs, and refreshes the handover files on each successful run.
`f03a-satellite_footprints.sh` redraws figures from cached metadata. Discharge
units and time zone remain unresolved. The GFM Product User Manual states
that the CEMS terms apply to GFM. The current CEMS terms allow reproduction,
distribution and adaptation with source attribution; these focus-area crops
and the figure carry the required modified-information notice. See the
[GFM Product User Manual](https://extwiki.eodc.eu/gfm_assets/gfm4.0_pum_2025.pdf)
and [CEMS terms and conditions](https://global-flood.emergency.copernicus.eu/terms-of-service/).
The
`S1A_o038784_dt049389` first-processing candidate is recorded as `proposed` in
`metadata/03a_selected_passes.json`; this does not certify its coverage or
require an approval state for later execution. See the
[Step 3a satellite data survey](03_satellite_data_survey.md),
[observation inventory](observation/observation_data_inventory.md), and the
[p03c output provenance](observation/GFM_extent/GFM_S1A_20210715_o038784_dt049389_extent20m.json).

### p03d — Extract native GFM focus areas

Run `bash s03d-extract_gfm_focus_areas.sh` to read the proposed WGS84 boxes in
`metadata/03c_focus_areas.json` and extract each one from the existing native
classification COG. The densified projected bbox is rounded outward to source
pixel boundaries; outputs retain the source Equi7 CRS, 20 m resolution,
pixel alignment, uint8 class codes and NoData=255 without resampling or
reclassification. The per-area GeoTIFFs are written under
`observation/GFM_extent/`. `metadata/03d_extracted_areas.json` is the canonical
handover manifest: it records each source bbox, actual projected bounds, file
path, dimensions, size and class counts, plus the shared grid and class
definitions. `proposed` remains descriptive and does not gate extraction.

Run `bash f03d-gfm_focus_areas_20m.sh` to recreate
`figure/f03d-gfm_focus_areas_20m.png` from that manifest. It shows the native
categorical classes over a softened OSM background; the model river network
is omitted so the observation classes remain prominent. These local maps are
inspection views of the selected observation crops; they do not imply that
unobserved pixels are dry or that the selected areas validate hydrologic
performance. Land and Exclusion are drawn at 50% opacity to reveal OSM below;
water classes use 60% opacity, while NoData remains transparent.

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
| Observations | Discharge inventory; catalogue survey of 18 GFM passes; one GFM pass acquired and classified at native 20 m | Review pass coverage and data terms, then obtain fit-for-purpose temporal/spatial coverage |
| CaMa-Flood run | Existing v5 build/run documentation and generic GOSH examples | Configure, run and validate a specific event experiment |
| Matching | Data products and their grids/time semantics documented in part | Approve and implement spatial/temporal matching rules |
| Evaluation | No event performance results | Define metrics and report uncertainty and support |

Detailed Rhine event findings remain in the linked event documents. This process
document is the reusable sequence; it does not replace their data inventories,
figures, domain tables, acquisition commands or scientific caveats.
