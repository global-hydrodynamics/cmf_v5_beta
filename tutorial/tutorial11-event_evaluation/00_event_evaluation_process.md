# Rhine 2021 Flood Event Evaluation: Research Plan and Analysis Workflow

**Current scope:** This Tutorial develops an evaluation of CaMa-Flood for the
July 2021 western European floods, with a focus on the Rhine and related
regional river systems. Event research, spatial planning and GFM preparation
have produced sample outputs. A Rhine event simulation, model–observation
matching and quantitative performance evaluation have not been completed.

## 1. Research Objective

The research objective is to assess how well CaMa-Flood reproduces flood
behavior during the July 2021 event, using river discharge and satellite-derived
flood information where their spatial and temporal support permits comparison.
The event affected several connected and neighboring river systems. The
evaluation therefore needs to state whether a result concerns the Rhine main
stem, Rhine tributaries, or a broader model routing group; these are not
automatically interchangeable targets.

The study first establishes what happened and where impacts were reported. It
then relates affected reaches and available observations to the CaMa-Flood
network, and designs separate simulation and observation domains. Satellite
acquisitions and discharge records must be prepared with their timing,
resolution, masks, missing data and provenance intact. A CaMa-Flood event run
can then be configured for the selected hydrologic scope. Finally, model output
must be matched to each observation type and evaluated with metrics that account
for valid observation support and uncertainty.

The expected scientific outcome is a documented assessment of discharge and
flood-extent reproduction, including its limits and uncertainty. The present
Tutorial is still a preparation and data-processing sample: no event-specific
CaMa-Flood simulation or quantitative skill result is available yet. Step 1
background and evidence are summarized in the [event Survey Report](AI_survey_report/01_flood_event_overview.md).

## 2. Human–AI Collaborative Analysis

### 2.1 Human–AI Workflow

The researcher defines the study objective and gives the AI agent the relevant
Step Prompt, data access and event-specific constraints. The agent inspects
existing inputs, conducts the requested research or analysis, and prepares the
reproducible processing, metadata, figures and reports needed for the next
Step. It explains evidence, interpretation and unresolved questions so the
researcher can assess the result.

Research proceeds through feedback when useful: the researcher reviews the
scientific interpretation and may request a correction, alternative analysis
or additional evidence; the agent updates affected outputs and reports. Review
is recommended, but its absence does not stop later processing. The details for
review states, errors and agent conduct are defined in the Tutorial's
[AI-supported analysis rules](AGENTS.md). The staged scientific workflow
below is the research plan; per-Step execution instructions are in the
corresponding Prompts.

### 2.2 Directory and File Structure

| Directory or file | Role |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | Common AI-supported analysis rules for Tutorial 11 |
| [`00_event_evaluation_process.md`](00_event_evaluation_process.md) | Research objective, methods, stage relationships and current status |
| [`pXX-*.md`](p01-event_research.md) | Human-facing entry point and Agent Workflow for each Step |
| `sXX-*.sh` | Reproducible data acquisition, processing or calculation |
| `fXX-*.sh` | Reproducible Figure generation |
| [`script/`](script/) | Python programs used by the processing and Figure workflows |
| [`metadata/`](metadata/) | Machine-readable configuration, results and Step handoffs |
| [`observation/`](observation/) | Observation data and their inventories; some data are local/ignored |
| `Atlantis/` | Ignored local catalogue caches, downloaded assets and run records |
| [`figure/`](figure/) | Figures used to inspect and explain research results |
| [`AI_survey_report/`](AI_survey_report/01_flood_event_overview.md) | Researcher-facing findings and scientific interpretation |
| [`AI_work_report/`](AI_work_report/01_event_research.md) | Technical execution record and handoff for developers and agents |
| [`development_log/`](development_log/development_log.md) | Chronological development decisions and history |
| [`tests/`](tests/) | Focused checks for Tutorial processing workflows |

The Step Prompts and [Tutorial 11 rules](AGENTS.md) define how these artifacts
are maintained. The table describes their purpose rather than repeating their
naming or report-writing rules.

### 2.3 How to Use This Tutorial

Start with [p01-event_research.md](p01-event_research.md) and provide the event
and research objective. Review the resulting report and Figure, and request
changes where the evidence or interpretation needs attention. Continue through
the relevant Step Prompts, using each step's saved outputs as inputs to the
next. Human review is a recommended research practice, not a software approval
gate. Step-specific instructions, files and handoffs are documented in the
corresponding `pXX-*.md` file.

## 3. Analysis Workflow

### Step 1 — Event Research

**Objective:** establish the event chronology, affected river systems, reported
impact localities and potential observation sources that frame the evaluation.
**Method:** review scientific literature, public reports and other traceable
sources; distinguish reported impacts from approximate map locations; compile
an impact inventory and map reported localities with river context. These
outputs give Step 2 geographic and temporal evidence without deciding model
Basin IDs or final evaluation domains. See [p01](p01-event_research.md), the
[event Survey Report](AI_survey_report/01_flood_event_overview.md), the
[Work Report](AI_work_report/01_event_research.md),
[`metadata/01_impact_locations.csv`](metadata/01_impact_locations.csv), and
[Figure 1](figure/f01-reported_flood_impacts.png).

### Step 2 — Analysis Domain Design

**Objective:** define candidate spatial and temporal scopes that can support a
hydrologically meaningful model run and observation analysis. **Method:** map
target reaches and gauge/impact locations onto the selected CaMa-Flood network;
use basin identifiers, upstream-area information and downstream connectivity
to assess routing groups, contributing networks and outlets. Keep the
simulation domain, satellite-analysis domain and map viewport separate. A
simulation window must contain the required upstream network and outlet, not
just damaged locations. Model routing groups may differ from natural
watersheds. The saved Figure and domain settings provide a reviewable handoff
to satellite availability work; they are candidate design, not a configured
simulation. See [p02](p02-analysis_domain.md), the [domain Survey Report](AI_survey_report/02_analysis_domain_design.md),
the [Work Report](AI_work_report/02_domain_design.md),
[`metadata/02_domain_selection.json`](metadata/02_domain_selection.json), and
[Figure 2](figure/f02-analysis_domain_design.png).

### Step 3 — Satellite Observation Preparation

#### Step 3a — Satellite Availability

**Objective:** identify acquisitions that may provide useful event observations
for the candidate satellite-analysis area. **Method:** search the configured
period and extent in the GFM catalogue, group catalogue Items by their source
Sentinel-1 acquisition, and compare acquisition metadata and footprints. A GFM
tile footprint is not the original Sentinel-1 acquisition footprint, and
neither proves that valid flood pixels exist at a locality. The output is a
proposed pass selection and a documented basis for acquisition, not a claim of
complete event coverage. See [p03a](p03a-satellite_availability.md), the
[availability Survey Report](AI_survey_report/03a_satellite_availability.md),
the [Work Report](AI_work_report/03a_satellite_availability.md),
[`metadata/03a_selected_passes.json`](metadata/03a_selected_passes.json), and
[Figure 3a](figure/f03a-gfm-pass-footprints-01.png).

#### Step 3b — GFM Download

**Objective:** acquire the native GFM assets for selected passes and establish
a traceable input list for processing. **Method:** obtain or reuse the
requested GFM layers without resampling, and record Item-to-asset paths,
integrity and readability in a manifest and summary under the ignored local
`Atlantis/` workspace. Step 3c consumes that manifest rather than repeating
catalogue search or download. The local download record is not a Git-tracked
data package. See [p03b](p03b-download_gfm.md), the [download Survey Report](AI_survey_report/03b_gfm_download.md),
the [Work Report](AI_work_report/03b_gfm_download.md), and
[`s03b-download_gfm.sh`](s03b-download_gfm.sh).

#### Step 3c — GFM Classification and Focus-Area Selection

**Objective:** prepare an interpretable observation product and identify
compact regions for detailed native-resolution work. **Method:** classify the
selected observation on its native 20 m grid while preserving categorical
meaning, NoData, exclusions and the source grid. Aggregate flood detections and
valid classified support to a one-arc-minute Flood Fraction for regional
screening, then select focus areas using flood counts and support. This
fraction is conditional on valid classification and is not a full-cell
inundated-area fraction. Focus boxes are a subset for storage and inspection,
not a complete flood inventory. See [p03c](p03c-gfm_classification.md), the
[classification Survey Report](AI_survey_report/03c_gfm_classification.md),
the [Work Report](AI_work_report/03c_gfm_classification.md),
[`metadata/03c_focus_areas.json`](metadata/03c_focus_areas.json), and
[Figure 3c](figure/f03c-gfm_flood_fraction_1min.png).

#### Step 3d — Focus-Area Extraction

**Objective:** reduce the detailed observation data to the selected regions
while retaining the native grid and classes. **Method:** project each focus
box and extract source-pixel-aligned 20 m windows without reprojecting,
resampling or changing classes. The extraction metadata indexes bounds,
dimensions, class counts and output files; the resulting maps support visual
inspection and prepare observation data for a later model comparison. Crop
edges follow the native grid and may extend slightly beyond the requested
geographic boxes. See [p03d](p03d-focus_area_extraction.md), the [extraction
Survey Report](AI_survey_report/03d_focus_area_extraction.md), the [Work
Report](AI_work_report/03d_focus_area_extraction.md),
[`metadata/03d_extracted_areas.json`](metadata/03d_extracted_areas.json), and
[Figure 3d](figure/f03d-gfm_focus_areas_20m.png).

### Step 4 — River Discharge Observation Preparation

**Objective:** prepare the supplied river-gauge observations for later
event-evaluation work. **Method:** retain source files unchanged, identify
stations by ID, check time coverage/cadence/missing values and CSV–NetCDF
consistency, and plot the supplied July values without interpolation. The
Rhine sample uses data supplied by ECMWF, so station search and download are
omitted. Units, source time zone, original observing agency and exact map
allocation remain unresolved; the provided `Cama*` values are references, not
verified matching assignments. See [p04](p04-discharge_observations.md), the
[Survey Report](AI_survey_report/04_discharge_observations.md), the
[Work Report](AI_work_report/04_discharge_observations.md),
[`observation/README.md`](observation/README.md),
[`metadata/04_discharge_inventory.csv`](metadata/04_discharge_inventory.csv),
[`metadata/04_discharge_dataset.json`](metadata/04_discharge_dataset.json), and
[Figure 4](figure/f04-observed_discharge.png).

### Step 5 — Water-Level Observation Preparation

Water-level observation preparation is reserved for a future Step. Its input
data, provenance, vertical datum, units, timing and quality controls have not
yet been established.

### Steps 6–10 — Reserved

Steps 6–10 are intentionally reserved for future research activities and are
not currently specified or implemented.

### Step 11 — Model Experiment Setup

Design a reproducible event-specific CaMa-Flood experiment using the selected
hydrologic scope and prepared observations. Model version, map, forcing,
initialization, boundary conditions and outputs remain to be specified.

### Step 12 — Event Simulation

Run the configured experiment and document the exact inputs, settings,
execution environment and outputs. No Rhine 2021 event simulation has been
completed; sample runs and maps do not constitute one.

### Step 13 — Observation–Model Matching

Define defensible spatial, temporal and variable correspondence between
simulation output, discharge stations, water levels and satellite
classifications. Account for units, time semantics, grid/station mapping,
masks, permanent water, missing coverage and resolution. Matching rules and
reusable implementation have not been established.

### Step 14 — Event Evaluation

Quantify and interpret model performance only after the simulation and
matching support are defined. Select metrics for the research question, and
report sample coverage, uncertainty and limitations separately by observation
type. No event performance score, calibration result or validation conclusion
has been produced. Do not infer model skill from observation figures alone.

## 4. Expected Outcomes and Current Status

The intended outcome is a reproducible, evidence-based assessment of CaMa-Flood
for the July 2021 event: selected observation and simulation scopes, prepared
discharge and satellite data, an event experiment, documented model–observation
correspondence, and quantitative results with uncertainty. The retained
Prompts, processing scripts, metadata, figures and reports support that work,
but preparation outputs must not be confused with evaluation results.

| Stage | Existing artifacts and execution evidence | Current research status |
| --- | --- | --- |
| **1 — Event research** | Impact inventory, Figure 1, observation data guide, Prompt and reports exist. Reports were reconstructed from retained evidence; the original research and mapping outputs are preserved. | Event context is documented; impact locations are selected examples, and observation provenance questions remain. |
| **2 — Domain design** | Candidate domain JSON, Figure 2, Prompt and reports exist. | Candidate bounds and mapped routing groups are documented; hydrologic scope and model boundary conditions are not final. |
| **3a — Availability** | Pass metadata, selected-pass JSON, Figure 3a, Prompt and reports exist. | Catalogue survey is documented; pass selection is `proposed`, and footprints do not establish valid flood-pixel coverage. |
| **3b — Download** | Local `Atlantis/` manifest, summary and COG assets are present; the Prompt, downloader and reports exist. | The retained summary records acquisition checks and readiness for p03c. The assets are local/ignored and are not distributed through Git. |
| **3c — Classification** | Flood Fraction raster, focus-area metadata and Figure 3c are present; processing entry points and reports exist. The full-extent 20 m classification TIFF is absent from the current workspace; its provenance record remains. | Processing and screening are recorded, but the full source raster is unavailable here for a new pixel-level check. Focus areas remain proposals and do not represent all detected flooding. |
| **3d — Extraction** | Extraction metadata, 15 focus-area 20 m rasters and Figure 3d are present; extraction/figure entry points and reports exist. | Focus crops are prepared; they are derived observation subsets, not model comparisons or validation results. |
| **4 — Discharge observations** | Provider-supplied source files, Step 4 inventory/metadata, Figure 4 and reports are recorded. | Three Rhine gauge series are prepared; unit, time zone, original observing agency and verified model-cell mapping remain unresolved. |
| **5 — Water levels** | No water-level dataset or preparation workflow is recorded. | Reserved for future work. |
| **6–10 — Reserved** | No activities are specified. | Future research stages. |
| **11 — Model setup** | No Rhine event experiment setup is recorded. | Domain, forcing, initialization, boundary conditions and model configuration remain to be designed. |
| **12 — Simulation** | No Rhine event simulation result is recorded. | Event run remains future work. |
| **13 — Matching** | No matching method or implementation is recorded. | Spatial, temporal and variable correspondence remains to be designed. |
| **14 — Evaluation** | No quantitative event score or performance report is recorded. | Metrics, valid-sample treatment and uncertainty analysis remain future work. |

The Step Prompts, Survey Reports and Work Reports are linked in the Analysis
Workflow above. They provide the detailed instructions, scientific evidence and
execution record respectively; this document explains how those activities
form one research plan.
