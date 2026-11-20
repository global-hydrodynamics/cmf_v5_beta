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
