# Flood Event Evaluation Process

**Status:** Reusable six-stage process. Tutorial 11 contains a partially developed Rhine 2021 sample; its maps and GFM products do not mean that a CaMa-Flood event simulation or quantitative evaluation has been completed.

## Agent workflow and report roles

Each `pXX-*.md` file is the Agent Workflow entry point. The agent receives inputs from the preceding Step, performs the research or processing, saves reusable data/settings, and prepares both a researcher-facing Survey Report and a developer-facing Work Report. After a first complete run, Human review is recommended and can lead to revisions; no review response is required for downstream processing. `proposed` and `approved` describe review state only and never gate execution. Missing inputs and failed data checks remain ordinary errors.

- **Agent Workflow Prompt — `pXX-*.md`:** defines inputs, tasks, outputs and reusable instructions. It is not a record that the work has been executed.
- **AI Survey Report — `AI_survey_report/`:** explains findings, quantitative evidence, scientific interpretation, uncertainty, figures and next research decisions. Write for the investigator/requester, not as a terminal log. Embed existing Figures by relative Markdown paths with captions; do not duplicate or regenerate images just for the report.
- **AI Work Report — `AI_work_report/`:** records the actual inputs, scripts/commands, outputs, checks, issues and handoffs for developers and future agents. When reconstructed after the original work, state that it is reconstructed from retained artifacts and distinguish recorded results from checks performed during reconstruction. Do not invent environment details or tests.
- **`metadata/`:** machine-readable Step handoffs. Preserve producing-Step prefixes when downstream Steps consume the data. Do not edit scientific settings merely to improve documentation.
- **`sXX-*.sh` / `fXX-*.sh`:** reproducible processing and Figure entry points from saved inputs. They supplement, but do not replace, the Prompt or the reports.
- **`development_log/`:** chronological project history and design changes. Keep it distinct from current Survey and Work Reports.

Report names are fixed: `AI_survey_report/01_flood_event_overview.md`, `02_analysis_domain_design.md`, `03a_satellite_availability.md`, `03b_gfm_download.md`, `03c_gfm_classification.md`, and `03d_focus_area_extraction.md`; corresponding Work Reports use the same Step names under `AI_work_report/`, with `01_event_research.md` and `02_domain_design.md` for the first two. Update the same file on later review; do not create `_v2` or `_final` variants.

Python files under `script/` follow the parent Step/Figure naming rules below: an `sXX` and `fXX` sharing Step-specific code use `sXX-*`; `fXX-*` is for code used only by that Figure; `event_*` is reserved for code shared across different Steps.

## Step inputs, tasks and outputs

| Workflow | Inputs | Main task | Survey/Work reports and handoff |
| --- | --- | --- | --- |
| **p01 — Event research** | Event identity, period and research objective | Review sources, build impact inventory and Figure 1 | `AI_survey_report/01_flood_event_overview.md`; `AI_work_report/01_event_research.md`; `metadata/01_impact_locations.csv`; Figure 1 |
| **p02 — Domain design** | Step 1 report/inventory/Figure, CaMa map, available gauges | Trace routing groups; design simulation and observation extents; Figure 2 | `AI_survey_report/02_analysis_domain_design.md`; `AI_work_report/02_domain_design.md`; `metadata/02_domain_selection.json`; Figure 2 |
| **p03a — Availability** | Step 2 period/domain and event context | Search catalogue and compare acquisition footprints; propose passes | Separate 3a reports; `metadata/03a_*`; selected-pass JSON; Figure 3a |
| **p03b — Download** | Selected-pass JSON, domain JSON and Step 3a catalogue | Acquire/reuse selected native GFM COGs and verify manifest | Separate 3b reports; ignored `Atlantis/` COGs, per-pass manifest and summary |
| **p03c — Classification** | p03b manifest/COGs and Step 2 domain | Native-grid classification, 1-minute Flood Fraction, focus selection and Figure 3c | Separate 3c reports; classification/provenance, fraction raster, `metadata/03c_focus_areas.json`, Figure 3c |
| **p03d — Extraction** | Classification raster and 3c focus JSON | Extract source-aligned 20 m focus areas and Figure 3d | Separate 3d reports; crop GeoTIFFs and `metadata/03d_extracted_areas.json`; Figure 3d |
| **4 — Simulation** | Adopted/candidate domains, forcing and model setup | Configure/run a specified CaMa-Flood event experiment | Future development; no event-specific Rhine run is recorded |
| **5 — Matching** | Model output and observation metadata | Define spatial, temporal and variable correspondence | Future development; no reusable matching tool/rule is complete |
| **6 — Evaluation** | Matched data and agreed target/metrics | Quantify and report event performance and uncertainty | Future development; no event score or validation claim is implied |

## 1. Select and research the event

Use [p01-event_research.md](p01-event_research.md). Establish the event chronology, major rivers, reported damage/localities, potential observations and source uncertainty. Figure 1 markers are approximate locality coordinates, not flood boundaries. Do not decide model Basin IDs or final domains here. Complete the initial report, CSV and Figure before offering optional review.

**Rhine 2021 sample:** Step 1 documents intense rainfall over 13–15 July 2021 and reported impacts across Germany, Belgium, Luxembourg and the Netherlands. Ahr/Erft tributaries, the Moselle system and the separate Meuse basin are distinguished. Fourteen localities are catalogued in `metadata/01_impact_locations.csv`; the listed places are not claimed exhaustive. Supplied discharge files contain Lobith, Speyer and Maxau, not Bonn; they are described as six-hour means with end-of-interval timestamps. Units, source time zone and original observing agency remain unresolved. See the [observation inventory](observation/observation_data_inventory.md).

## 2. Design simulation and observation domains

Use [p02-analysis_domain.md](p02-analysis_domain.md). Inspect the selected CaMa map's `basin`, `uparea` and `nextxy` as appropriate. Derive Basin IDs from the current map and trace the target upstream network and outlet. A model routing group is not necessarily a natural watershed. Simulation bounds contain the required upstream contributing area/routed network and outlet; do not size them only around damage points. Satellite analysis bounds may be smaller or split into several areas. Keep the map viewport distinct from both domains.

**Rhine 2021 sample:** On `glb_15min` (0.25°), sampled event localities and the three supplied gauges associate with Basin ID 74; Halen and Wavre associate with ID 1299. ID 74 is a Rhine–Meuse/Vesdre model routing group, not a pure natural Rhine watershed. The provisional simulation rectangle is 3.125–12.125°E, 45.875–52.375°N. The candidate satellite analysis rectangle is 4–8°E, 49–52°N, based on an existing target-grid extent. Neither is a finalized, fully validated domain. Figure 2 and supporting evidence are in the [Step 2 Survey Report](AI_survey_report/02_analysis_domain_design.md). The `metadata/02_domain_selection.json` remains the machine-readable handoff; its values and statuses are unchanged by this report reorganization.

## 3. Acquire and preprocess observations

### 3a. Survey satellite availability

Use [p03a-satellite_availability.md](p03a-satellite_availability.md). Search the configured period and bbox into date-separated local catalogue caches, group by verified Sentinel-1 platform/absolute orbit/datatake, compare source GRD `GeoFootprint` with GFM tile coverage, and record a proposed pass. Tile geometry, source-product footprint and valid flood pixels are different concepts. Neither footprint proves useful valid observation. `s03a` prepares metadata; `f03a` draws only from saved metadata/cache and does not repeat search.

**Sample:** The focused 14–16 July 2021 search contains 45 STAC Items, 6 passes and 27 source product slices. The current `metadata/03a_selected_passes.json` proposes 15 July S1A descending pass `S1A_o038784_dt049389` (11 Items; 5 source products; 3 source footprints intersect the candidate AOI). The 15 July S1B evening pass has no source-product footprint intersecting the current AOI. Catalogue geometry is not an observation-validity mask. See the [3a Survey Report](AI_survey_report/03a_satellite_availability.md).

### 3b. Download selected GFM assets

Use [p03b-download_gfm.md](p03b-download_gfm.md). `s03b-download_gfm.sh` reads selected passes/layers and the Step 2 bbox; it writes native COGs and a per-pass manifest/summary under ignored `Atlantis/`. The manifest is the next Step's input list. The summary's `ready_for_p03c` checks selected-item/layer mapping, files, checksums and readability; it does not depend on Human review. Do not reproject, mosaic or classify during 3b.

**Sample:** 11 selected Items produced 44 Item/layer references for four layers and 37 unique COG assets. The current summary records all 37 verified (52,333,157 bytes), no missing/failed files, and `ready_for_p03c: true`. The manifest lives under the ignored local `Atlantis/` directory. See the [3b Survey Report](AI_survey_report/03b_gfm_download.md).

### 3c. Classify and select focus areas

Use [p03c-gfm_classification.md](p03c-gfm_classification.md). The native categorical mosaic keeps source CRS/grid/alignment and distinguishes Land, Flood, permanent/seasonal/other water, Exclusion, Inconsistent and NoData. Do not turn missing observations into dry pixels. The 1-arc-minute Flood Fraction is class 1 divided by valid classes 0–4; a cell with no valid class is NoData. It is not a full cell-area inundation percentage. Focus selection should use flood counts and valid support, not reported-impact proximity. Save proposed boxes and their count/area/storage tradeoffs in the fixed `metadata/03c_focus_areas.json`.

**Sample:** The original source provenance records a 17,835 × 19,783 single-band uint8 COG, 20 m, lossless, 23,445,565 bytes, and the class counts in its JSON. The fraction raster is 240 × 180 EPSG:4326 at 1 arc minute; 35,225 cells have valid classified support and the fraction range is 0–75.91241%. Fifteen proposed focus areas retain 140,228 of 160,301 1-minute Flood pixels (87.48%) over about 9.78% of the candidate AOI. Projected, outward-aligned windows cover 34,950,179 unique pixels (90.09% fewer than the source extent); separate-file compression was estimated at 2,098,447 bytes. These are screening/storage diagnostics, not an optimized selection or complete flood inventory. The monolithic source TIFF is absent from the current worktree; these source statistics are inherited from its retained processing JSON, not freshly read from that TIFF. See the [3c Survey Report](AI_survey_report/03c_gfm_classification.md).

### 3d. Extract focus areas

Use [p03d-focus_area_extraction.md](p03d-focus_area_extraction.md). `s03d` projects each WGS84 bbox and snaps its rectangle outward to the existing 20 m grid without reprojecting, resampling or reclassifying. `metadata/03d_extracted_areas.json` is the formal downstream handoff; it lists source identity, class definitions, per-area WGS84/projected bounds, output path, dimensions, size and class counts. `f03d` builds Figure 3d from that manifest. The Figure uses OSM context and class layers; the CaMa river network is omitted. Crops may include source pixels just beyond the WGS84 boxes because bounds are snapped outward.

**Sample:** Metadata lists 15 crop GeoTIFFs with total 2,113,624 bytes (2.016 MiB), about 90.98% smaller than the recorded 23,445,565-byte monolithic source COG. All 15 listed crop files and Figure 3d are present in the current worktree. The source TIFF itself is absent, so the percentage uses recorded source size; no raster comparison is claimed by this documentation task. See the [3d Survey Report](AI_survey_report/03d_focus_area_extraction.md).

## 4. Configure and run CaMa-Flood

Before an event run, confirm map/version, forcing coverage/units/calendar, initialization and upstream inflow, domain mask and boundaries, restart treatment, outputs and time support. Record the exact experiment and runtime logs. The current GOSH examples are references, not a configured Rhine experiment. A successful launch alone is not scientific validation.

**Sample status:** No Rhine-specific CaMa-Flood simulation has been configured or run. The target of Rhine-only versus combined routing group, final basin scope and boundary treatment remain open.

## 5. Match model output and observations

Before scoring, define grid/CRS and spatial mapping, time intervals and acquisition/composite support, variables, units, missing/excluded/permanent-water handling and provenance. Do not fill satellite gaps with dry labels. The supplied discharge timestamps denote interval ends, but source timezone and units are unspecified. Station-to-model-cell and GFM-to-model support rules remain to be designed.

**Sample status:** No reusable matching implementation or approved matching rule is recorded.

## 6. Evaluate performance

Choose metrics after the scientific target, valid support, masks, time match and uncertainty are agreed. Report area/period, valid sample counts, missing/excluded coverage, units, thresholds and uncertainty; separate discharge from flood-extent evaluation. Do not infer event skill from one visual overlay.

**Sample status:** No event performance score, calibration or validation result is recorded.

## Record maintenance

When a Step is completed, update its Survey Report and Work Report along with the relevant handoff metadata as part of that Step. This document owns the common workflow; reports explain event-specific findings; Work Reports record how current results were produced; and `development_log/` preserves historical decisions. Existing Rhine reports reconstructed after the work are explicitly marked as retrospective and do not claim reruns.
