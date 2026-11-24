# p04 — River Discharge Observation Preparation

### How to Use This Workflow

**Rhine 2021:** Use the current supplied station files and July plotting
settings. Provide the entire Markdown file as an attachment or copy its full
content, including the Current Example and observation-data guidance.

**Another event:** Fill the event/objective, event-directory and observation
provenance placeholders. Review station inventories, the plotting period and
existing Shell settings; preserve original files and undeclared metadata.
Verify implementation assumptions about station IDs, formats and time support,
and establish data-use terms. Supply the entire updated file to the agent.
Rhine's supplied-data/no-download scope and checked results must not be mistaken
for observations available in the new study; additional acquisition still
requires its own authorization.

The block refers to this Step Prompt and must accompany the full document; it
is not an independent copy-and-paste Prompt.

## Workflow Summary

### Inputs
- Step 1–2 event and domain findings, including target rivers and evaluation purpose
- Supplied files in `observation/stations_data/`
- Existing observations and station metadata in `observation/stations_data/`; see `observation/README.md`

### Tasks
- Inspect the supplied station and time-series files; join stations by ID.
- Check CSV/NetCDF agreement, timestamp cadence, missing values and basic statistics.
- Plot the supplied July 2021 discharge records without interpolation or smoothing.
- Prepare the observation README, machine-readable metadata, Survey Report and Work Report.

### Outputs
- `observation/README.md`
- `metadata/04_discharge_inventory.csv` and `metadata/04_discharge_dataset.json`
- `figure/f04-observed_discharge.png`
- `AI_survey_report/04_discharge_observations.md`
- `AI_work_report/04_discharge_observations.md`

## Human Instructions

For another event, provide the event directory, evaluation objective, target
rivers/gauges if known, and the available observation files with their source
and redistribution terms. Do not transfer Rhine station IDs or assumptions to
another event. The Rhine 2021 example starts from an ECMWF-supplied dataset, so
station search and download are intentionally omitted.

## Example AI Agent Prompt

```text
Prepare Step 4 river-discharge observations for this event.

Event/objective: [EVENT / PURPOSE]
Tutorial event directory: [PATH]
Observation data and provenance: [PATHS / PROVIDER / PERMISSIONS]

Read the Step 1–2 findings, the observation README and this Step Prompt. Use
the supplied source files as read-only inputs. Do not infer undocumented units,
time zones, station identity, interval semantics, quality status or model-grid
correspondence.

1. Inspect station metadata and time-series formats. Match time-series columns
   to station records by the explicit station ID, not row position. Check
   timestamps, cadence, duplicate/missing records, valid-value masks, basic
   statistics, and CSV-NetCDF consistency where both formats are supplied.
2. Run `run_script/s04-prepare_discharge.sh` to write `metadata/04_discharge_inventory.csv`
   and `metadata/04_discharge_dataset.json`. Preserve provenance, file hashes,
   declared and undeclared fields, and any provider-supplied interpretation.
3. Run `plot_script/f04-observed_discharge.sh` to plot the original event-period values.
   Do not interpolate, smooth, resample or silently convert units or times.
4. Write the scientific findings and limitations to
   `AI_survey_report/04_discharge_observations.md`; record actual commands,
   inputs, checks, issues and handoff in `AI_work_report/04_discharge_observations.md`.
   Update `observation/README.md` with concise dataset instructions.
5. Present a complete first result without waiting for Human review. Human
   review is recommended and can request revisions, but is not a software
   gate. Do not proceed past missing or unreadable required inputs by guessing.

Keep raw source files unchanged. Do not calculate rating curves, allocate new
model cells, search for additional gauges, download data, or run the model
unless separately requested. Hand off source values and metadata for the later
matching step; do not claim that observation preparation validates the model.
```

## Current Example

Tutorial 11's Rhine sample is already implemented using three provider-supplied
stations. See [`observation/README.md`](observation/README.md), the
[Step 4 Survey Report](AI_survey_report/04_discharge_observations.md), and the
[Step 4 Work Report](AI_work_report/04_discharge_observations.md). The Prompt
describes a reusable workflow; the reports state what was actually checked in
this sample.
