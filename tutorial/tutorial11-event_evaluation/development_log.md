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
- Created `flood_event_overview.md` and this development log. No analysis code,
  datasets, README or existing files were changed.

**Files created:**

- [flood_event_overview.md](flood_event_overview.md)
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

- `stations_data/allstations.csv`
- `stations_data/Qobs_06_2021_st153_63_28.csv`
- `stations_data/Qobs_06_2021_st153_63_28.nc`

**Checks performed:** Inventoried sizes, structures, NetCDF dimensions/types and
attributes; joined station metadata by ID; checked time decoding, cadence,
duplicates, missing/nonfinite values, full-period statistics and July maxima;
compared all CSV/NetCDF values with float32 representation explicitly accounted
for; checked coordinate/index consistency under a stated regular-global-grid
assumption. Source SHA-256 values were checked before and after the work.

**Files created:**

- [observation_data_inventory.md](observation_data_inventory.md)
- [figure/observed_discharge_2021-07.png](figure/observed_discharge_2021-07.png)

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
catalogue footprints and valid pixels are documented in `gfm_data_inventory.md`.

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

- `gfm_data_inventory.md`: acquisition/version/procedure, measurement definitions,
  file structure/sizes, timestamp/footprint metadata, results and limitations.
- `flood_event_overview.md`: current upstream/workspace, the completed one-day
  test, data definitions and observation-data clarification.
- `figure/gfm_2021-07-15_1arcmin.png`: daily fraction and valid-input coverage.
- `figure/gfm_2021-07-15_quality_1arcmin.png`: stored quality-companion codes.
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

**Files created or updated:** `event_setup_plan.md`, `evaluation_domain.md`, `event_setup_report.md`, `impact_locations.csv`, `figure/event_basin_overview.png`, `figure/event_flood_impact_area.png`, `visualization/river_map/script/f06-OSM_background.py`, `visualization/river_map/f06-OSM_background.sh`, `visualization/gallery/p01-f06-OSM_background.png`, and the related Visualization README/catalog entries.

**Decisions and limitations:** Simulation extent is derived from the complete model basin group plus a two-cell margin, not from the impact towns. At 0.25°, model ID 74 combines Rhine and Meuse/Vesdre routing and is not a pure natural Rhine watershed; ID 1299 includes separate nearby cells around Gete/Halen and Dyle/Wavre. The rectangle and satellite AOIs remain candidates. Town coordinates are approximate place-centre markers, not flood polygons. The existing 2021-07-15 GFM test does not cover all proposed AOIs and has partial valid-pixel coverage. No new GFM data or model simulation was run. OSM tiles were fetched only for the plotted extents and credited. Map Explorer supports browser OSM and manual Pins but not CSV point import or OSM-included PNG export; no broad GUI change was made.

**Testing performed:** Parsed the impact CSV and Gallery catalog, checked relevant Markdown links, ran `bash -n` and Python AST syntax validation, generated the OSM-backed Gallery image from the checked-in script, tested its `--no-osm` path, reviewed the two event figures, and ran `git diff --check`. No model run or GFM download was performed.

**Location-source clarification:** Wavre is treated as a Dyle locality (not Gete); its 15–16 July impact is cited to the municipal summary. Halen is recorded separately on the Gete/Velpe system. Coordinates remain approximate place centres. See the links in `impact_locations.csv`.

**Result:** The requested map products and reproducible general Gallery example are prepared. Hydrologic basin identity, boundary conditions, scene coverage, station metadata and evaluation choices remain to be confirmed before simulation.


## 2026-11-21 — Refine River Map f06 panels

**Objective:** Separate the default basin overview from local event annotations,
make Rhine-specific plotting settings editable data, and align names with the
River Map figure/panel convention.

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
