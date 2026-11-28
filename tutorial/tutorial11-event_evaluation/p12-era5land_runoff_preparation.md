# p12 — ERA5-Land Hourly Runoff Preparation

### How to Use This Workflow

**Rhine 2021:** Keep the researcher settings in Human Instructions and
Rhine 2021 settings and interpretation below. Supply the entire Markdown file
as an attachment or copy its full content; reuse the downloaded/converted data
rather than repeating successful processing.

**Another event:** Review the event Product Shell, acquisition dates, requested
area, dataset paths/identifier and grouping settings below. Edit the authoritative
Shell/Registry locations identified here rather than creating a second settings
source. Check actual grid/units/time support, access credentials and terms, and
implementation dependencies. The Rhine grid sizes and acquisition/completion
records are case-specific. Supply the entire updated file, including the
interpretation and handoff sections, to the agent; execute only when needed
inputs and scientific decisions are established. Keep KG-0019 unresolved unless
separately investigated; changing event settings does not resolve conversion
semantics or automatically adapt the existing implementation.

The block is an execution directive within the full file, not a standalone
Prompt. Completed Rhine downloads do not authorize skipping a new event's needs.

## Workflow Summary

### Inputs
- Step 11 regional map: `tutorial/tutorial11-event_evaluation/map/Rhine_15min/`
- Step 2 event/domain context: `metadata/02_domain_selection.json`
- Existing ERA5-Land Product/Download/Convert tools under `inp/download_ERA5-Land/`
- Rhine Product Shell: `tutorial/tutorial11-event_evaluation/run_script/s12-prepare_runoff.sh`
- Existing local ERA5-Land data, if available

### Tasks
- Confirm the researcher-selected acquisition period and requested area.
- Inspect and reuse existing raw and converted files; download/convert only if required.
- Verify file coverage, hourly labels, NetCDF variables, units, coordinates and missing values.
- Register the Tutorial 11 runoff dataset in `runoff_dataset.csv`.
- Record this Step's settings, processing state and checks in Step 12 metadata/reports.
- Hand off the Registry and data to Step 13 for map-specific Input Matrix preparation and validation.

### Outputs
- Local original and converted ERA5-Land runoff data
- `runoff_dataset.csv` — Tutorial-local runoff specification registry
- `metadata/12_era5land_runoff.json` — Step 12 execution record and handoff
- `AI_survey_report/12_era5land_runoff_preparation.md`
- `AI_work_report/12_era5land_runoff_preparation.md`

## Human Instructions

For Rhine 2021, the researcher has already downloaded and converted the data.
Ask the AI agent to inspect and reuse the files in
`tutorial/tutorial11-event_evaluation/inp/ERA5land-Rhine2021Jul/`; avoid repeating successful download or
conversion work. Keep all downloaded data and logs local and ignored by Git.
The former dataset ID `tutorial11-ERA5land-Rhine2021Jul` is retained in the
historical Step 12 metadata; the current Tutorial registry and Product Shell
use `ERA5land-Rhine2021Jul` for the same data under its Tutorial-local path.

The researcher-selected acquisition period is July 1–31, 2021, to retain a
pre-event preparation interval before the initial July 10–25 candidate analysis
window. It does not establish the model simulation period or adequate spin-up.
The selected CDS bounds (2.5–13.5°E, 44.5–53.5°N) intentionally extend 0.5°
beyond each edge of the Step 11 Rhine map (3–13°E, 45–53°N). Record the actual
NetCDF grid coordinates; Step 13 verifies their mapping to the model grid.

For another region or period, review and edit the Product Shell's user settings
and then run it when new files are needed. Step 13 generates and validates a
separate regional Input Matrix for the actual 111 × 91 subset; the global
`ERA5land_global` pair is not interchangeable:

```sh
bash tutorial/tutorial11-event_evaluation/run_script/s12-prepare_runoff.sh
```

Use an appropriately named copy for a different event. Do not edit the shared
s01/s02 processing algorithms as part of routine event configuration. A real
CDS download requires credentials and acceptance of the dataset terms.

## Example AI Agent Prompt

**Current Rhine 2021 configuration:** Event names, paths, periods, geometry
and researcher-selected settings in this block describe this application.
For another event, review and replace them using its own inputs and decisions;
the general methods and limits still apply. Supply the complete file.

```text
Prepare Step 12 ERA5-Land hourly runoff for this event.

Read the repository/Tutorial instructions, `inp/download_ERA5-Land/README.md`,
KG-0019, the Step 2 metadata, Step 11 report and map, the Product Shell, and the
Tutorial-local `runoff_dataset.csv` schema. Inspect the local dataset and logs
before running anything. Existing complete files must be reused; do not
redownload or reconvert them without a concrete need.

For Rhine 2021, preserve these researcher settings in
`tutorial/tutorial11-event_evaluation/run_script/s12-prepare_runoff.sh`:
- Dataset `ERA5land-Rhine2021Jul`
- 2021-07-01 through 2021-07-31 inclusive
- Requested area 2.5–13.5°E, 44.5–53.5°N (0.5° beyond each Step 11 map edge)
- Timestep 1 hour, daily download grouping, daily output grouping
- NetCDF, NCPUS=2

1. Check the complete raw and converted daily file sequence and available logs.
   Confirm hourly ordering/count, NetCDF readability, variables, units,
   coordinates and missing-value metadata from the actual files.
2. Keep the source accumulated `ro` in metres distinct from converted
   `runoff` in millimetres per hourly record. Daily file grouping is not an
   average. Retain KG-0019 and do not alter conversion semantics.
3. Add or update the dataset row in `runoff_dataset.csv`, using the same column
   schema as `inp/runoff_datasets.csv`. Distinguish observed data properties
   from Product Shell settings. This Tutorial registry is authoritative for
   Steps 13 and 14; do not add the event-specific row to the shared registry.
4. Write `metadata/12_era5land_runoff.json` as an execution record, not a
   duplicate registry. Link it to the registry row; record selected settings,
   processing status, validation summary, limitations and the next-step handoff.
5. Update the Step 12 Survey and Work Reports and the event process links.
   Clearly distinguish the event period, initial candidate analysis period,
   selected runoff acquisition period and the Step 14 simulation period.
6. Hand the Registry and actual NetCDF grid evidence to Step 13. Step 13 owns
   Input Matrix creation/validation. Step 14 owns the simulation-period/forcing
   decisions, creates the GOSH script and executes the requested simulation;
   Step 15 visualizes the retained simulation outputs. Do not configure or run
   the model here.

Do not redownload/reconvert a complete dataset, regenerate a map, change
scientific algorithms, run CaMa-Flood, compare observations, or publish the
data package. Report checks actually performed and unresolved items.
```

## Rhine 2021 settings and interpretation

The exact researcher-selected settings are retained in the Product Shell and
summarized in the Tutorial Registry. Step 1's initial 2021-07-10 to 2021-07-25
candidate analysis window remains unchanged. The July 1–31 runoff acquisition
period provides pre-event and post-event forcing context; it is a forcing-data specification, not independent proof of simulation
conditions or sufficient spin-up. Step 14 separately records the executed
July 1–August 1-exclusive, 744-hour cold-start run.

ERA5-Land's source runoff is accumulated depth (`ro`, metres); the shared
converter outputs timestep runoff (`runoff`, millimetres per input timestep).
`DOWNLOAD_UNIT`/`OUTPUT_UNIT` only group files. The generated information file
reports `IFRQ_INP=1`, `DROFUNIT=3600000`, `CROFFREQ="DAY"`, `CVNTIME="time"`
and `CVNROF="runoff"`; Step 14 must compare these to the final model settings.
The requested CDS area intentionally has a 0.5° margin around the regional
map. The actual grid center coordinates are registered in `runoff_dataset.csv`.
Step 13 must verify the map-specific Input Matrix; Step 12 does not claim that
matrix is valid for this forcing.

KG-0019 remains open: the ERA5-Land 00 UTC accumulation covers the preceding
24 hours, and converter first-record and period-boundary behavior has not been
scientifically resolved. Structural completeness does not resolve this timing
question.

## Registry and downstream handoff

`runoff_dataset.csv` is the Tutorial 11 specification registry, using the
shared runoff registry's schema. Steps 13 and 14 should read this row for the
input path, file pattern, grid, units and conversion settings.
`metadata/12_era5land_runoff.json` records the selected run's state and checks
and points to the Registry; it does not replace the data specification.

Step 13 prepares or validates the map-specific `ERA5land_Rhine2021Jul` Input Matrix
and documents its actual alignment with the observed NetCDF grid. Step 14 then
decides simulation conditions and prepares the reproducible GOSH script.
Neither step may infer an approved simulation period from the July 1–31
acquisition interval.
