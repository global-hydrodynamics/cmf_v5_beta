# Tutorial 11 Development Log

This log records development of `tutorial11-event_evaluation` in chronological
order. Append an entry for each subsequent tutorial task; preserve earlier
entries rather than rewriting their history. Record the date (`YYYY-MM-DD`),
objective, work performed, files created or changed, result, and any significant
decisions or unresolved questions.

## 2026-11-20 — Documentation of the July 2021 Rhine flood event

**Objective:** Prepare background information for a future flood-event
reproducibility evaluation tutorial developed in collaboration with ECMWF.

**Work performed:**

- Organized event information shared through the ECMWF email thread “D2 report
  and deliverable” (2026-11-03 to 2026-11-13), using the maintainer's summary.
  The original emails and `stations_data.tar.gz` were not inspected in this task.
- Summarized the event dates, affected regions and principal rivers, separating
  destructive tributary flooding from Rhine main-stem behaviour.
- Documented the supplied discharge-series descriptions and ECMWF CaMa-Flood
  experiments, including the reported six-hour mean/end-timestamp convention.
- Described candidate satellite flood-extent products and the intended Atlantis
  use; checked public provider documentation and recorded verification limits.
- Created `01_flood_event_overview.md` and this development log. No analysis code,
  datasets, README or existing files were changed.

**Files created:**

- [01_flood_event_overview.md](../01_flood_event_overview.md)
- `development_log.md`

**Decisions and unresolved questions:**

- Keep correspondence-derived information separate from publicly verified
  product descriptions. Station-data origin, observation/simulation status,
  licences and redistribution permissions remain unconfirmed.
- Keep the analysis dates/domain provisional. Do not select evaluation metrics
  or an implementation design at this stage.
- Verify Kuro Siwo events 518 and 520 against the selected dataset version.
  EMSR517 resolution and observation dates are product-specific.
- The supplied Atlantis URL returned 404 during review; confirm access/location,
  capabilities and licence before adopting it.

**Result:** Initial flood event background documentation prepared.

**Next steps:** Review available datasets and design the event-based evaluation
workflow.


## 2026-11-20 — Inspection of river discharge observation data

**Objective:** Inspect the supplied observations and their metadata, compare CSV
and NetCDF, and prepare an initial July hydrograph without model evaluation.

**Files inspected:**

- `../stations_data/allstations.csv`
- `../stations_data/Qobs_06_2021_st153_63_28.csv`
- `../stations_data/Qobs_06_2021_st153_63_28.nc`

**Checks performed:** Inventoried sizes, structures, NetCDF dimensions/types and
attributes; joined station metadata by ID; checked time decoding, cadence,
duplicates, missing/nonfinite values, full-period statistics and July maxima;
compared all CSV/NetCDF values with float32 representation explicitly accounted
for; checked coordinate/index consistency under a stated regular-global-grid
assumption. Source SHA-256 values were checked before and after the work.

**Files created:**

- [observation/README.md](../observation/README.md)
- [observed discharge figure](../figure/observed_discharge_2021-07.png)

**Main findings and decisions:**

- The files contain Lobith/153, Speyer/63 and Maxau/28. Bonn/6 from the earlier
  email summary is absent. Do not relabel Speyer as Bonn.
- Each series has 1,460 complete six-hour records from 2021-01-01 06:00 through
  2022-01-01 00:00, with no missing values, duplicate times or irregular steps.
  CSV and NetCDF timestamps/IDs match; CSV values converted to float32 equal
  all 4,380 NetCDF values exactly.
- The six-hour mean/end-label convention supplied by ECMWF is consistent with
  coverage, but is not independently encoded by time bounds or cell_methods.
  Discharge/area units, source time zone, exact coordinate/grid conventions and
  original observing-agency provenance are not explicitly documented.
- The maintainer confirmed tutorial sharing/redistribution permission in this
  task, superseding the earlier unresolved permission status. No named licence
  is invented. Prior log entries and the initial background note are preserved.
- The figure uses three aligned panels and 124 original values per station for
  July intervals, with points only and no interpolation or smoothing. Its axes
  explicitly identify the missing unit/time-zone information. Visual inspection
  and canvas-bound checks were performed.

**Result:** Read-only inventory and initial hydrograph prepared; input hashes
unchanged. No source data, analysis framework, evaluation metrics, README or
model comparison were created or modified. Only the report, figure and this log
update are included in this task's commit.

**Next steps:** Confirm units/time zone and grid metadata, resolve the missing
Bonn selection with ECMWF, and document provider/citation details before planning
quantitative event evaluation.


## 2026-11-20 — GFM acquisition: change from eight days to a one-day test

**Objective and maintainer decision:** Complete and inspect one day before
attempting a longer satellite-data acquisition. Use **2021-07-15 only** and
retain the original box **5.6–10.0°E, 49.5–52.9°N**. Do not restart the eight-day
fetch, optimise at large scale, modify Atlantis source or implement evaluation
metrics. Keep all external software, environments, data, logs and checking
scripts in `/Users/yamadai/work/Atlantis/`; keep only documentation,
reproduction instructions and selected figures in Tutorial 11.

**Initial attempt and preserved evidence:** The 13–20 July catalogue search
succeeded (125 tile products, 73 distinct exact UTC timestamps). The actual
fetch ran for approximately 30 minutes without completed GeoTIFF outputs and
was manually interrupted (exit 130). This is not evidence of an authentication
failure. Default CLI logging did not expose item-level warnings/progress. The
proposed eight-day restart did not execute before the maintainer changed the
strategy. Logs, complete catalogue, pre-change inventory draft, historical
scripts and the original environment are retained under the dedicated
`archive/eight_day_attempt/` directory.

**Setup and one-day checkpoint:** Inspected current `opageo/atlantis` at commit
`9371dc4fc421949caf9a2a8eb03e5fb962872820`, including README, CLI, GFM overview,
pipeline and Pixi setup. Moved the external checkout/Pixi/cache to the dedicated
workspace. Pixi rejected relocation of the old environment, which was preserved
in the archive; recreated the environment from the unchanged lock. Shared
Python and existing CaMa-Flood environments were not altered. The requested
workspace is an alias of `/Volumes/work06_P32_84T/work_06/Atlantis/`.

The fresh one-day search confirmed **14 products and 10 exact UTC timestamp
groups**. Started `Rhine_2021_test` with verbose logging, the unchanged box,
`strategy all`, harmonisation and plotting, plus support-count diagnostics.
Transport settings remain default; CURL headers and a one-second process-tree
RSS monitor provide measurement only. At this checkpoint the raster run is
still in progress; no successful raster inspection is claimed yet.

**Interpretation established from source:** The CLI merges acquisitions by UTC
date. A daily raster is not an instantaneous flood map. Fractions are stored as
0–100 percent with 255 nodata; zero can include rounded small fractions.
Reference water alone does not establish SAR observation. Valid support uses
the flood-or-water validity rule. These definitions and the distinction between
catalogue footprints and valid pixels are documented in `../gfm_data_inventory.md`.

**Completion of the one-day checkpoint:** The acquisition completed with exit 0
at **18:30:15 JST**, after **955.06 s (15 min 55 s)** from 18:14:20. The final
checklist records 14/14 items and one plotted/harmonised date. The original box
was retained; no smaller-box or multi-day acquisition followed.

**Measured load and outputs:** Accessed 74 distinct COG URLs. The CURL log has
10,882 successful single-range GET responses, totalling 440,598,472 compressed
payload bytes (420.19 MiB), including rereads and excluding HEAD/bodyless
responses and protocol overhead. Unique source-file sizes total 278.63 MiB.
OS waited-child maximum RSS was 12.03 GiB; the one-second sampled process-tree
RSS sum peaked at 11.27 GiB (not unique physical memory). Produced 18 GeoTIFFs
and 18 Atlantis PNGs, 20,352,520 bytes total, outside Git. Metadata/log/cache and
inspection figures are additional files. No HTTP 4xx/5xx response was recorded.

**Inspection and validation:** The processed grid is 6,123 × 4,732 at nominal
80 m; the harmonised grid is 264 × 204, EPSG:4326, 1/60-degree spacing, correctly
aligned over the requested box. Main fraction values are 0–45%; 23,721 cells
(44.045%) have some valid input, 30,135 are nodata, and 294 have positive
fractions. Kept nodata separate from zero. Processed percentage/support-ratio
and valid-mask/positive-denominator checks passed. There are 437 processed
cells with positive flood support rounded to zero. Inspected exclusion and
advisory code distributions separately; valid contribution does not mean full
cell observation or quality-cleared usability. Opened both selected figures
and checked geographic axes, legends, equal map extents and readable export
layout. Fixed the local checker to match actual hyphenated harmonised date
filenames; retained its first path-error log. No re-download was needed.

**Important finding / unresolved issue:** Harmonised diagnostic counts lose
fractional support through rounding in the pinned Atlantis
`write_harmonised_raster` function. The harmonised flood-count TIFF is all zero
although the main fraction has 294 positive cells. Do not reconstruct fractions
or observation masks from these harmonised count files. Processed diagnostics
passed their consistency check and remain available for traceability. Atlantis
source was left unchanged; preserving diagnostic floats and verifying their
masks is a proposed future fix, not implemented work.

**Tutorial files created/updated:**

- `../gfm_data_inventory.md`: acquisition/version/procedure, measurement definitions,
  file structure/sizes, timestamp/footprint metadata, results and limitations.
- `01_flood_event_overview.md`: current upstream/workspace, the completed one-day
  test, data definitions and observation-data clarification.
- `../figure/gfm_2021-07-15_1arcmin.png`: daily fraction and valid-input coverage.
- `../figure/gfm_2021-07-15_quality_1arcmin.png`: stored quality-companion codes.
- `development_log.md`: append-only strategy, execution and result record.

**Result and stopping point:** One-day acquisition and local inspection
completed. No large/raw dataset, dependency or checking script is added to the
CaMa-Flood repository; source discharge hashes remain unchanged. No model
metrics, large optimisation or Atlantis source change was made. The eight-day
fetch remains stopped. This day supports exploratory inspection of observed
areas, not an event-wide peak-inundation evaluation.

**Knowledge-gap review:** Resolved current upstream/CLI, fraction/support
meaning, native codes, target-grid geometry and diagnostic-export rounding
through source and actual-file checks. Independent pass IDs, per-acquisition
valid-pixel footprints, event-specific quality screening, formal data
attribution/redistribution details and model-time/water-definition matching
remain for future work. July 14/16 usability was not established by this
single-day test. No additional acquisition was started to resolve those points.


## 2026-11-20 — Atlantis storage audit and preservation plan

**Objective:** Audit storage and propose a minimal Git/Dropbox preservation set,
without deleting, moving, copying or rebuilding existing files/environments.
No acquisition or Git commit/push was authorized or performed.

**Work performed:** Read-only directory/inode/allocation inventory, per-directory
top-20 files and type counts; checked package metadata, source Git status and
lock/spec hashes; reviewed GFM cache/fetch code; compared selected content hashes
and Tutorial figure copies. Distinguished logical content, reported allocation
and hardlink sharing. Created /Users/yamadai/work/Atlantis/storage_audit.md and
appended this log only.

**Findings:** About 7.84 GiB of archive is the superseded environment, not GFM
imagery. Its 286 Conda packages and 275 Python metadata distributions match the
active environment by identity/version, but its private/tmp prefix no longer
exists. There is one active installed environment, source/.pixi/envs/default;
eight pixi.toml declarations do not mean eight installed environments. Source
has no tracked modifications. About 7.21 GiB of regular-file allocation is
shared between environment and cache; du order explains source's 720 MiB
increment. Small-file allocation overhead also inflates reported usage.

**Reuse checks:** No complete 20 m GFM COG is preserved. The 4 KiB header probe
cannot supply pixels, and the configured data cache contains a font list only.
Read small windows from all 18 local TIFFs and performed a network-disabled,
in-memory 128x128 processed-fraction to 4x5 one-arcmin harmonisation. Bytecode
and PAM writes were disabled. No output files were written by these checks.
Native reclassification still needs original COG reacquisition; current fetch
code does not resume from existing processed outputs.

**Preservation proposal:** Git references comprise three existing documents,
two existing figures, four currently local helper scripts and the audit report,
about 0.3--0.35 MiB in total. Scripts require the external workspace layout or a
separately authorized portability change; they should not simply be run inside
Tutorial 11. The default Git plan adds no GFM TIFF. A 34-file Dropbox set totals
38,698,351 bytes (36.91 MiB), including data/evidence/version definitions; a
minimal data-only subset is 18,917,278 bytes. Installed environments, package/
font caches and regenerable Atlantis PNGs are excluded. Original COGs are
absent from this set. A six-TIFF Git sample is optional (30,474 bytes), subject
to GFM redistribution review.

**Candidates, not actions:** The old environment is the major future deletion
candidate (~7.84 GiB allocation). Cache-only removal would expose about 1.45 GiB
unshared allocation, not its entire displayed size. No files were deleted or
transferred. Previous log entries remain unchanged.

**Unresolved:** GFM-specific licence/attribution, server-side snapshot and
compression effects on actual freed space, native-COG/local-STAC offline replay,
and a lean GFM-only environment remain unverified. Preserve the documented
harmonised diagnostic-count rounding caveat with any shared data. No source,
environment or scientific data was changed by this audit.

**Final read-integrity check:** Decoded all 18 complete TIFF arrays offline;
shape, valid counts, zero counts and minima/maxima match the saved inventory.
No data output, acquisition, environment change or Git publication was performed.


## 2026-11-20 — Add the small GFM sample to Tutorial 11

**Objective / authorization:** The maintainer explicitly requested creating a
Tutorial 11 directory, copying the six recommended harmonised TIFFs and pushing
the result on the existing working branch.

**Work performed:** Created `gfm_sample/` with the six unchanged science/quality
TIFFs (30,474 bytes), `README.md` and `SHA256SUMS`. Added an inventory link and
provenance, grid, nodata, daily-composite and quality interpretation details.
Preserved all previous development-log entries, including the pending storage
audit record from the preceding task. No external storage audit report was
copied into Git.

**Validation:** Source/copy SHA-256 and exact six-file/30,474-byte scope checked;
GeoTIFF readability, dtype, CRS, extent, one-arcmin spacing, nodata and main
fraction statistics checked. Rounded count diagnostics and larger files are
excluded. Source files remain unchanged; no acquisition or environment change
was performed. Existing untracked discharge observations are not included.

**Limitations:** The sample supports initial raster inspection, not native
reprocessing or a complete event evaluation. GFM-specific attribution and
redistribution terms remain unverified; no new data licence is asserted.

**Result:** Small repository sample prepared for commit and push on the
existing `feature/package-builder` branch. No branch switch or main push.


## 2026-11-21 — Basin-wide event domains and OSM Gallery sample

**Objective:** Separate full-watershed simulation planning from localized flood-observation planning, and add a reusable OSM-backed CaMa river-network example.

**Work performed:** Inspected the global 15-minute `basin`, `nextxy`, `uparea` and COG products; mapped model Basin IDs 74 and 1299, supplied gauges and report-documented localities. Created the two required planning figures, separate candidate simulation/observation bboxes, an impact-location CSV, and event setup report/plan. Assessed Map Explorer's basin/network, OSM, Pin, import and PNG-export capabilities. Added Gallery method **p01-f06 · OSM_background**, its extent-limited renderer and OSM attribution.

**Files created or updated:** `event_setup_plan.md`, `../evaluation_domain.md`, `event_setup_report.md`, `../metadata/01_impact_locations.csv`, `../figure/event_basin_overview.png`, `../figure/event_flood_impact_area.png`, `../../../visualization/river_map/script/f06-OSM_background.py`, `../../../visualization/river_map/f06-OSM_background.sh`, `../../../visualization/gallery/p01-f06-OSM_background.png`, and the related Visualization README/catalog entries.

**Decisions and limitations:** Simulation extent is derived from the complete model basin group plus a two-cell margin, not from the impact towns. At 0.25°, model ID 74 combines Rhine and Meuse/Vesdre routing and is not a pure natural Rhine watershed; ID 1299 includes separate nearby cells around Gete/Halen and Dyle/Wavre. The rectangle and satellite AOIs remain candidates. Town coordinates are approximate place-centre markers, not flood polygons. The existing 2021-07-15 GFM test does not cover all proposed AOIs and has partial valid-pixel coverage. No new GFM data or model simulation was run. OSM tiles were fetched only for the plotted extents and credited. Map Explorer supports browser OSM and manual Pins but not CSV point import or OSM-included PNG export; no broad GUI change was made.

**Testing performed:** Parsed the impact CSV and Gallery catalog, checked relevant Markdown links, ran `bash -n` and Python AST syntax validation, generated the OSM-backed Gallery image from the checked-in script, tested its `--no-osm` path, reviewed the two event figures, and ran `git diff --check`. No model run or GFM download was performed.

**Location-source clarification:** Wavre is treated as a Dyle locality (not Gete); its 15–16 July impact is cited to the municipal summary. Halen is recorded separately on the Gete/Velpe system. Coordinates remain approximate place centres. See the links in `../metadata/01_impact_locations.csv`.

**Result:** The requested map products and reproducible general Gallery example are prepared. Hydrologic basin identity, boundary conditions, scene coverage, station metadata and evaluation choices remain to be confirmed before simulation.


## 2026-11-21 — Refine River Map f06 panels

**Objective:** Separate the default basin overview from local event annotations,
make Rhine-specific plotting settings editable data, and align names with the
River Map ../figure/panel convention.

**Work performed:** Replaced the single renderer with dedicated f06a and f06b
entry points and a shared OSM/network helper; added `f06_settings.json`; kept
Tutorial 11-derived locality and candidate-AOI data in CSV. The launcher now
writes `f06a-OSM_background-default.png` and
`f06b-OSM_background-local_info.png`, then combines them as
`f06-OSM_background.png`. OSM styling uses a subtle white blend and alpha
0.72/0.68; the f06a exterior basin veil uses alpha 0.36. f06b uses regular
1-degree longitude and 0.5-degree latitude ticks. Removed the f06 Gallery
registration while retaining the image file as an untouched local change.

**Limitations:** Basin ID 74 combines Rhine and Meuse/Vesdre model routing.
The AOI boxes are candidates, not observed inundation extents; locality points
are approximate town centers. OSM rendering uses its existing graceful
fallback. No hydrologic interpretation or model data were changed.


## 2026-11-21 — Adjust f06 map extent and geographic ticks

Set the f06b local-information extent to 4–8°E, 49–52°N. Both f06 panels
now use 1° labeled major ticks and 0.5° unlabeled minor ticks for longitude
and latitude. The f06a zoom rectangle reads the same extent from the existing
external CSV. The change affects map presentation only.


## 2026-11-21 — Publish p01-f06 OSM Background in the Gallery

**Authorization:** The maintainer explicitly requested formal Gallery
publication of `p01-f06 — OSM_background` on `feature/package-builder`.

**Work performed:** Registered f06a (default basin overview) and f06b (local
event information) using the existing per-panel catalog schema. Updated the
River Map project README, the Visualization Gallery README, and the catalog;
replaced the Gallery image with the latest combined project Figure. Reviewed
the development/review/publication workflow and clarified structured
event-specific settings, project README image order, and attribution/provenance
for hosted basemaps. The OSM cache refreshes after seven days under the public
tile policy fallback. Panel titles and geographic axis labels were aligned with
the shared figure guideline.

**Validation:** Regenerated both panels and the combined Figure with OSM tiles;
visually checked river layers, event points, AOIs, legend, attribution and labels.
Verified the Gallery PNG SHA-256 equals the project composite, catalog IDs are
unique, CSV parses, links and files exist, and `git diff --check` passes.

**Limitations:** Basin ID 74 combines Rhine and Meuse/Vesdre model routing.
Locality markers are approximate towns, and candidate AOIs are not confirmed
satellite coverage or observed inundation boundaries.

## 2026-11-21 — Native GFM acquisition and CaMa-aligned 3-second tiling

**Task:** Implement and execute separate native four-layer acquisition and local
3-second conversion for 15 July 2021, 4–8°E / 49–52°N.

**Existing work:** Yesterday's entire workspace had been moved to `old/`.
Reused the pinned Atlantis checkout/environment via a prefix-restoring symlink;
created new data/log directories. Did not reinstall, modify Atlantis, or change
old files. Canonical new scripts are Git-managed here; external workspace
scripts and the Figure reference them through symlinks.

**Work performed:** Re-searched STAC (17 Items), grouped by platform/orbit/
datatake, and confirmed official orbit metadata. Acquired only the 11-Item S1A
morning descending pass, relative orbit 37, 05:49:37–05:51:42 UTC: four layers,
37 original COGs, 49.91 MiB in 62.66 s. Afternoon Items remain inventoried only.
Implemented blockwise common-grid earliest-valid mosaic, common flood/water/
quality masking, binary area-support warps and 4800×3600 EPSG:4326 output.
Verified the actual CaMa NetCDF's 1-minute geometry and 20×20 subdivision.

**Issue found and corrected:** All-cell validation exposed different GDAL
min/max versus average edge footprints in source-owner rasters. Replaced raw
ID warps with per-owner binary-support warps using the same average kernel;
owner closure now differs by at most 5.96e-8. Kept the failed check in external
logs and described the correction rather than weakening provenance validation.

**Results:** Final conversion 289.42 s, 883.59 MiB peak process RSS; 13 fields,
7,258,263 cells with usable support (42.00384%), 21,078 with positive flood
fraction. Unknown flood/water fractions remain -9999. Independent complete
regeneration with blocked socket connections and 256-cell rather than 512-cell
blocks produces bitwise identical decoded arrays for all fields (306.28 s).
All 37 local COGs reused, zero network bytes. Thirteen focused tests and actual
all-cell validation pass. Rendered and inspected the three-panel Figure;
corrected a colorbar-label collision and added a measured clearance check.

**Files:** New `../scripts/s01-download_gfm.py`, `s02-convert_gfm_3sec.py`,
`s03-validate_gfm_3sec.py`, shared contracts/tests, Figure Shell/Python and PNG,
compact Item/asset/validation metadata, and `../gfm_3sec_workflow.md`. Updated GFM
inventory, domain context, development status and research records. Raw COGs,
3sec rasters, native intermediates, environment and full logs stay outside Git.

**Preservation:** All 204,586 old-tree metadata entries match the pre-task
snapshot; Atlantis remains clean. CaMa map data and original discharge/GFM
samples are unchanged. Research validator retains 14 pre-existing historical
broken links; no new ones were added.

**Unresolved/scientific limits:** The morning mosaic is incomplete and is not
a daily/event maximum. Conservative joint validity differs from yesterday's
OR denominator; area overlap is a documented local GDAL approximation. Review
these choices before model comparison. No evaluation metrics, model run,
afternoon processing or Gallery publication performed. See
[gfm_3sec_workflow.md](../gfm_3sec_workflow.md) for exact commands and evidence.

## 2026-11-22 — Native GFM 20 m categorical classification

**Task:** Produce the requested single-band uint8 classification for the local
S1A morning GFM pass, with focused L1 checks. No download, 3-second regeneration,
model-grid aggregation or model run was performed.

**Inputs and method:** The saved `native_mosaic.json` described a 17,843 × 19,791
20 m Equi7 Europe mosaic, but its referenced `native_mosaic.tif` was absent.
Processed the 37 checksum-matched raw COG assets in blocks using the existing
`gfm_common.merge_observation` same-pass, earliest-joint-valid priority. The
intermediate metadata, raw inputs, `old/`, and existing 3-second products were
not modified. Source combination frequencies are stored as per-item
observations including overlaps, separately from selected mosaic class counts.

**Classification/result:** Common-valid `F=0,W=0` is Land; `F=1,W=1` is Flood;
`F=0,W=1` is Permanent/Seasonal for reference 1/2, otherwise Other water.
With no common-valid observation, observed exclusion is Code 5, then a partial
F/W classification is Code 6; otherwise Code 255. Reference-only pixels remain
NoData. Counts: Land 91,545,271; Flood 183,271; Permanent 3,373,440; Seasonal
111,434; Other 0; Exclusion 157,673,029; Inconsistent 63,491; NoData
100,180,877. No selected direct Flood/Water contradiction occurred. The
source/output Flood counts both equal 183,271 pixels, 73.3084 km² under 400 m²
planar pixel area; this is not geodesic area or scientific flood validation.

**Files and checks:** Added `../scripts/s04-export_gfm_20m_class.py`, updated
`../gfm_3sec_workflow.md`, and generated
`../figure/gfm_20210715_20m_class.png` (436,930 bytes). The external
`tiles_20m/S1A_o038784_dt049389/gfm_20210715_20m_class.tif` is a single-band
uint8 ZSTD COG, 23,458,035 bytes, SHA-256
`56036e1bba7a3bca603221caa8ba0e8aa31cf322997e2efe8dfb6afe4f9483df`;
`classification.json` records classes, source tuple counts, grid and provenance.
Synthetic class precedence passed. The first real-data attempt exposed a
pre-publication check opening the final filename before the temporary COG was
moved; this was corrected before any TIFF was published, and the one-pass export
was rerun. The actual COG reopened with the same CRS, shape, transform and exact
decoded values as the pre-COG classified raster; allowed codes, class counts and
NoData passed. The confirmation figure was visually inspected.

**Limits:** Duplicate valid observations retain the established earliest-valid
selection; 244 flood and 244 water overlap disagreements are recorded and not
promoted to separate classes. Exclusion and NoData remain distinct. Dataset-
specific GFM redistribution terms still need confirmation; the GeoTIFF and JSON
were left outside Git. No commit or push was made in this task.

## 2026-11-22 — Establish the event evaluation process

**Objective:** Consolidate Tutorial 11's reusable event-evaluation workflow
without replacing the original planning proposal or treating candidate work as
completed validation.

**Work performed:** Added `../00_event_evaluation_process.md` with six stages covering
event/watershed selection, separate domains, observation acquisition and
preprocessing, model execution, model–observation matching, and performance
evaluation. Distinguished current map/GFM examples from unimplemented Rhine
simulation, matching and scoring; linked the existing f06, GOSH and Tutorial 11
reference documents. Added a short link from the event-specific findings report.

**Validation:** Checked the new local references against existing files and
reviewed status statements against the event setup, domain and GFM workflow
notes. No code, data processing, model run, or figure regeneration was performed.


## 2026-11-22 — Tutorial 11 Step 2 spatial domain and observation design

**Objective:** Reassess candidate model and observation domains using the current CaMa-Flood map, reported impacts, supplied gauges and existing 15 July GFM product; render and visually review two planning maps.

**Work performed:**

- Reused the f06a/f06b River Map renderers with Tutorial-local JSON/CSV settings and a Tutorial entry-point shell. Shared renderers gained optional point-group rendering and candidate-domain overlays; default settings remain available.
- Inspected the 0.25° glb_15min Basin raster and grid metadata: ID 74 has 391 cells, ID 1299 has 19 cells; the candidate rectangle remains provisional.
- Used the existing GFM validation record, not a new acquisition. The 15 July product has 42.0038% valid target cells; support is patchy.
- Replaced the candidate-domain note with 02_domain_and_observation_design.md, recording visual review, recommendations, evidence status and Step 3 questions. Updated direct links and preserved the earlier setup plan/report and planning figures.

**Files created or updated:** Tutorial 11 Step 2 settings, gauge plotting CSV, rendering shell and two figures; shared f06 helper/panel scripts; the Step 2 design document, direct links and this log. No GFM download, model run, Gallery publication or Catalog update was performed.

**Result and decisions:** Keep 3.125–12.125°E, 45.875–52.375°N as a provisional outer model window only. Do not call Basin ID 74 a natural Rhine basin. Retain separate Ahr–Erft–Swist/Kyll/Prüm and Meuse–Vesdre–Gete–Dyle observation AOIs. Additional tributary gauges and GFM acquisition-level valid coverage remain to be verified.

**Validation:** Both rendered figures were reviewed visually; f06 panels used existing map data and local OSM tile cache where available. Shell/Python syntax, configuration/CSV parsing, output paths, links and git diff --check were checked. No model simulation or new observation retrieval was run.

## 2026-11-22 — Refine Step 2 basin selection and candidate-domain map

**Work performed:** Rechecked the current `map/glb_15min/COG` basin, uparea and nextxy rasters at the reported impact-locality and supplied-gauge cells. Basin ID 74 maps the sampled Rhine/Meuse/Vesdre-side localities and the three supplied gauges; Halen and Wavre map to ID 1299. Updated the reusable Step 2 process with the full-upstream-watershed rule and map-derived Basin ID procedure. Revised f01a to distinguish the candidate simulation and satellite-analysis rectangles, show IDs 74 and 1299, and retain a map viewport wider than the candidate boxes. The satellite candidate uses the bounds of the existing processed GFM target grid; this relationship and its incomplete valid support are now explicit. f01b remains supplementary local detail.

**Validation and limits:** Rendered f01a/f01b from existing map, point and OSM-cache inputs and visually inspected them. The Tutorial shell syntax, Python AST, JSON/CSV parsing and `git diff --check` passed. The ambient `python3` lacked Matplotlib, so rendering used the repository `.venv`; no downloaded observations or model run were used. At 0.25° resolution and with approximate locality coordinates, cell assignment and nextxy tracing support model-routing-group association only; they do not prove natural catchment boundaries or precise site-to-channel correspondence. Final simulation scope, boundary treatment and satellite coverage remain subject to human/scientific review. No commit or push was made.

## 2026-11-22 — Renumber Tutorial 11 event and domain figures

**Work performed:** Recast the local OSM impact map as Tutorial Fig. 1 (Step 1) with town labels and distinct river-system colors, and the wide basin/domain map as Fig. 2 (Step 2). Fig. 1 has no candidate AOI boxes; Fig. 2 retains the candidate simulation and satellite-analysis bounds. Added existing river-group and cartographic label fields to `../metadata/01_impact_locations.csv` and used that Tutorial catalog as the point input for both maps. Renamed the figure-generation wrapper and output images, updated the Step 1/Step 2 documents and reusable process links, and kept the Gallery/Catalog unchanged.

**Validation and limits:** Regenerated both figures from the existing glb_15min map and cached OSM tiles, then visually inspected each. The 14 reported localities appear in Fig. 1, grouped by river system; Fig. 2 shows the two candidate boxes, IDs 74/1299, impacts and gauges. Shell syntax, Python AST, JSON/CSV parsing, local Markdown links and `git diff --check` passed. Rendering used the repository `.venv` because ambient `python3` lacks Matplotlib. No model run, new observation acquisition, Gallery publication, commit or push was performed.
# 2026-11-22 — Step 3a satellite availability survey

Read the Step 2 machine-readable domain selection and searched GFM STAC metadata
for 2021-07-13 through 2021-07-20 at the candidate bbox 4–8°E, 49–52°N. The
date-separated results contain 114 STAC Items grouped into 18 Sentinel-1
platform/orbit/datatake passes. Reused River Map f06 shared drawing helpers to
make three same-extent OSM, CaMa river-network and STAC-footprint comparison
pages, then visually reviewed the AOI frame, footprint shapes, labels and scale.
The expected Atlantis source/Pixi targets were broken, so no environment was
reinstalled: the existing 15 July cache was reused and other dates were queried
read-only from the EODC STAC API. No satellite assets were downloaded. Added the
Step 3a inventory and process handoff; pass selection remains for researcher
review.

## 2026-11-22 — Correct Step 3a satellite footprint interpretation

Rechecked the GFM STAC geometry against item projection metadata and the
`derived_from` source product IDs. STAC geometry repeats the geographic
outline of Equi7 tile products, not the original Sentinel-1 scene footprint.
Retrieved metadata-only Copernicus Data Space OData `GeoFootprint` values for
all 72 unique source GRD products across the 18 passes; no raster assets were
requested. For the 14 July S1B pass, 10 Items resolve to 4 source product
slices and 4 Equi7 tiles, with only 4 unique STAC tile geometries. Updated the
pass inventory to distinguish Items, tiles, source products and passes; the
figure now uses one uniform-opacity compound footprint per pass to prevent
overlap darkening.

**Validation:** inventory/metadata counts and orbit attributes were compared
against the cached STAC and Copernicus product responses. Figures were
regenerated from the tracked acquisition geometries and visually inspected; no
image assets or model data were downloaded.

## 2026-11-22 — Focus Step 3a survey on 14–16 July

Narrowed the catalogue review window to 14–16 July 2021, centered on 15 July
as the disaster date of interest. The Step 2 JSON remains the single source of
the search-period setting; the summarizer now filters cached date directories
to that inclusive range so earlier broad-scan caches cannot add extra panels.
Regenerated the pass inventory and one six-panel figure from the existing
metadata cache: 45 STAC Items, 6 acquisition passes and 27 source product
slices. Removed the now-out-of-scope second and third generated figure pages.
No catalogue query, COG/SAR download or model run was performed.

## 2026-11-22 — Separate Step 3a metadata, f03a plotting and Step 3b download

Moved the Tutorial 11 GFM Python programs and `gfm_common.py` into the
canonical `script/` directory, updated their imports, tests and active workflow
references, and kept the historical development-log paths unchanged. Split
the former combined survey wrapper into `s03a-satellite_availability.sh`
(STAC plus Copernicus metadata), `f03a-satellite_footprints.sh` (local-only
figure rendering), and `s03b-download_gfm.sh` (the selected 15 July S1A
descending pass and the four required native layers). The Step 2 JSON remains
the shared 14–16 July survey-period source. Atlantis caches, logs and raw
downloads remain under the ignored Tutorial `Atlantis/` directory.

**Checks:** Shell syntax and Python AST checks passed. The metadata builder was
run against existing local catalogues only (45 STAC Items, 6 passes, 27 source
footprints), and f03a regenerated and visually checked its one-page figure.
The existing GFM unit-test module could not import the converter because this
Python environment lacks `pyproj`; no dependency was installed. The actual
s03a network search and s03b COG download were not run.

## 2026-11-22 — Prepare Rhine discharge observations as Step 4

Reused the three ECMWF-supplied station files without changing them. Added the
Step 4 Prompt, observation README, reproducible inventory/consistency checks,
machine-readable CSV/JSON metadata and a July 2021 point-only hydrograph with
one panel per station. Migrated the former observation inventory's scientific
findings and technical details into the README, Step 4 Survey/Work Reports and
dataset JSON, then removed the superseded inventory and updated its active
references. Reorganized the process stages as Step 4 discharge preparation,
Step 5 water-level preparation, reserved Steps 6–10, and Steps 11–14 for model
setup, simulation, matching and evaluation.

**Checks:** reran both Step 4 Shells using the repository `.venv`; confirmed
three stations × 1,460 records, six-hour timestamps, zero missing records,
CSV-to-NetCDF equality after float32 casting, July peaks and unchanged source
hashes. Opened Figure 4 for visual inspection and checked active Step 4 links
and scripts. No observation download, model run or matching was done.

## 2026-11-23 — Clarify Step 2 simulation-window bounds

Changed the candidate `glb_15min` simulation window to integer-aligned outer
edges 3–12°E, 46–53°N. The previous decimal values are retained separately in
`metadata/02_domain_selection.json` as the earlier corner-cell-center
candidate, and the broader 3–13°E, 45–53°N map-edge reference is documented.
Updated the Figure 2 orange simulation box and expanded only its map viewport
to show the north edge and label. The 4–8°E, 49–52°N satellite-analysis AOI
was unchanged. The saved figure was visually checked; no basin/network
analysis or model run was repeated.

**Correction (2026-11-23):** The intended simulation-domain outer bounds are
3–13°E, 45–53°N (not 3–12°E, 46–53°N). Updated the JSON and Figure settings,
Survey/Work Reports, and redrew Figure 2 with south/east viewport margins. The
older corner-cell-center candidate remains recorded separately; the satellite
AOI remains unchanged.


## 2026-11-23 — Inspect existing Rhine regional map for Step 11

Recorded the Step 11 regional-map workflow and inspected the retained local
`map/Rhine_15min/` products against the current Step 2 candidate outer bounds
(3–13°E, 45–53°N). The map metadata and representative NetCDF/COG products
match the 40 × 32, 0.25° regional grid; the 1-minute auxiliary grid is 600 ×
480 over the same bounds. Existing channel, bifurcation, runoff-mapping,
permanent-water, subbasin and GRDC-allocation products were found. The
`test-1deg` ELSE_GPCC climatology mapping remains distinct from the
`ERA5land_global` ERA5-Land mapping. No map generator, converter, data download
or model run was executed; the retained map data remain ignored by Git, while
map-local scripts and documentation remain trackable. The Step 11 Survey and
Work Reports describe checks, limits and the Step 12 handoff.


## 2026-11-23 — Prepare ERA5-Land hourly runoff for Step 12

Inspected the retained Tutorial 11 Rhine ERA5-Land data rather than repeating
acquisition or conversion. The Product Shell requests 2021-07-01 to 2021-07-20,
hourly, over 2.5–13.5°E and 44.5–53.5°N, extending 0.5° beyond the regional
map edges. Twenty original daily files and twenty converted daily files were
present; their dates are complete and the converted files contain a continuous
480-record hourly label sequence on a 0.1° grid. Added Step 12 Prompt,
metadata, Survey/Work Reports and workflow references; corrected the Product
Shell's copied Japan description. Data and logs remain ignored. No re-download,
reconversion, Input Matrix generation or model simulation was run. KG-0019
remains open; Step 13 must select the simulation/spin-up period and verify
forcing coverage.

## 2026-11-23 — Separate Tutorial runoff registry and downstream responsibilities

Added a Tutorial 11-local `runoff_dataset.csv` with the shared registry schema;
the event-specific ERA5-Land row was not added to `inp/runoff_datasets.csv`.
Step 12 metadata now records the selected acquisition settings and inspection
results while linking to the registry for the dataset specification. Kept the
Step 1 candidate analysis window and undecided simulation period in
`metadata/02_domain_selection.json`; the July 1–20 runoff acquisition period
is maintained in Step 12 metadata. Updated the process and handoffs so Step 13
owns Input Matrix preparation/validation, Step 14 owns simulation setup and
GOSH preparation, and model execution follows in Step 15. Existing local runoff
data, Product Shell settings, conversion algorithms and map products were not
changed.


## 2026-11-23 — Generate Tutorial 11 regional runoff Input Matrix

Created and ran a Rhine-specific map-local wrapper around the shared
`param_inpmat_generate` program. The generated matrix uses the actual 111 × 91,
0.1° ERA5-Land regional grid and the existing `Rhine_15min/1min` catchment
assignment; it is separate from the 3600 × 1801 global `ERA5land_global` pair.
Checked the actual NetCDF coordinates, generated diminfo, matrix dimensions and
indices for all active river cells, plus representative Rhine locations. Map
binaries remain ignored. No model run was performed, and KG-0019 remains open.


## 2026-11-23 — Run Tutorial 11 Rhine cold-start experiment

Added `s14-run_simulation.sh` and ran one 20-day hourly simulation with the
Step 11 Rhine map, Step 12 ERA5-Land daily NetCDF files and Step 13 regional
Input Matrix. The model completed 480 steps, wrote eight hourly NetCDF output
files and a final NetCDF Restart at 2021-07-21 00:00. Run products remain in
the ignored `experiment/Rhine2021/` directory. This cold-start run is an
operational demonstration only; it does not assess model skill or resolve
KG-0019.


## 2026-11-23 — Visualize Tutorial 11 Step 14 simulation outputs

Added the Step 15 prompt and reusable Figure workflow. From the retained 480
hourly records, calculated each cell's signed `outflw` at its local maximum
absolute value and each `pthflw` path's peak after summing active-width layers
per record. Generated and visually inspected the regional map and the Step 2
AOI direction-aware network map; corrected the AOI extent ordering and legend
spacing. Saved derived peak values under the ignored experiment directory and
recorded the method, input checks, figures and limitations in Step 15 metadata
and reports. No model run, observation matching, or accuracy evaluation was
performed. The cold-start and KG-0019 limitations remain open.


## 2026-11-23 — Use standard nextxy and update Step 15 regional map

Changed the Step 14 Rhine run to use the map's standard `nextxy.nc` rather
than `nextxy_noedge.nc`. Reran the same 480-hour experiment in a separate
ignored `experiment/Rhine2021-nextxy/` directory, preserving the earlier
noedge outputs. Updated Step 14/15 metadata, reports and handoff paths.
Reworked Fig. 15a from a raster view to a full-basin, direction-aware vector
network in the p02-f02b style, with thin upstream-area-scaled lines so the
regional network remains legible. Fig. 15b now uses the same standard network.
Regenerated and visually inspected both figures; the latest Step 14 run and
Step 15 derived peak file are the inputs. No model code or map data changed.


## 2026-11-23 — Restore regional raster in Step 15

Updated Fig. 15a to follow Gallery p02-f01a: signed local peak `outflw` on
the native 40 × 32 Rhine grid, without interpolation and with missing cells
white. Fig. 15b remains the p02-f02b-style standard-nextxy direction-aware
network over the AOI. Reused the existing Step 14 standard-nextxy run and
peak calculation; no model rerun or scientific calculation change.
