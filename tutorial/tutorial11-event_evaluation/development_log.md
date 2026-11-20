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
