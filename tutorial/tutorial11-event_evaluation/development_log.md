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
