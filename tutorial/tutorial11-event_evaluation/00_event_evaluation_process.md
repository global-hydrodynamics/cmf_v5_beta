# Rhine 2021 Flood Event Evaluation: Research Plan and Analysis Workflow

**Current scope:** This Tutorial develops an evaluation of CaMa-Flood for the
July 2021 western European floods, with a focus on the Rhine and related
regional river systems. Event research, spatial planning and GFM preparation
have produced sample outputs. An operational Rhine event simulation and
spatial gauge allocation are available. Steps 22–23 provide exploratory
discharge/timing comparisons. Step24 completes
one time-selected inundation downscaling, visualization and scientific assessment;
formal model–observation inundation matching and quantitative performance
evaluation have not been completed.

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
flood-extent reproduction, including its limits and uncertainty. An event-specific
CaMa-Flood run and a preliminary time-selected inundation product are available.
Step24 is the final scientific assessment of this sample workflow; quantitative
skill has not been established. Step 1
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
an impact inventory and map reported localities with river context. Record distinct
source-supported timing evidence and detailed station coordinates in a linked
metadata ledger, separating gauge peaks from locality impacts and preserving
unknown time bases. These outputs give Step 2 geographic and temporal evidence
without deciding model Basin IDs or final evaluation domains. See
[p01](p01-event_research.md), the
[event Survey Report](AI_survey_report/01_flood_event_overview.md), the
[Work Report](AI_work_report/01_event_research.md),
[`metadata/01_impact_locations.csv`](metadata/01_impact_locations.csv),
[`metadata/01_reported_flood_timing.csv`](metadata/01_reported_flood_timing.csv), and
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
omitted. Step 21 later checks the three `Cama15` candidates against the current
map and verifies their spatial cells. Discharge units, source time zone,
original observing agency and reported-area units remain unresolved. See
[p04](p04-discharge_observations.md), the
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

### Step 11 — Regional Map Preparation

Prepare or verify the event-specific regional CaMa-Flood map from the selected
source map and Step 2 outer-edge bounds. Inspect existing map outputs before
running generators; reuse matching products and do not overwrite a retained
map automatically. Keep the global map-local data outside Git unless a separate
distribution decision is made. The Rhine sample uses `glb_15min` and a
candidate 3–13°E, 45–53°N outer-edge window. Existing regional products are
available; their preparation history is not inferred from their presence. See
[p11](p11-regional_map_preparation.md), the [Survey Report](AI_survey_report/11_regional_map_preparation.md),
the [Work Report](AI_work_report/11_regional_map_preparation.md), and
[`map/Rhine_15min/README.md`](../../map/Rhine_15min/README.md).

### Step 12 — ERA5-Land Hourly Runoff Preparation

Inspect or prepare event-specific runoff using the existing ERA5-Land
Product/Download/Convert workflow. The Rhine sample has researcher-prepared
hourly data for 2021-07-01 through 2021-07-31 and requests an area 0.5° beyond
the Step 11 regional map. Keep the initial candidate analysis window
(2021-07-10 through 2021-07-25), actual runoff acquisition period, and future
simulation/evaluation period distinct. July 1 does not prove adequate spin-up;
forcing must be extended if later evaluation dates are used. KG-0019 remains
open. See [p12](p12-era5land_runoff_preparation.md), the
[Tutorial runoff Registry](runoff_dataset.csv), the
[Survey Report](AI_survey_report/12_era5land_runoff_preparation.md), the
[Work Report](AI_work_report/12_era5land_runoff_preparation.md), and
[runoff metadata](metadata/12_era5land_runoff.json). The local source and
converted files are ignored by Git.

### Step 13 — Runoff Input Matrix Preparation

Use the Tutorial-local [runoff dataset Registry](runoff_dataset.csv), the
observed NetCDF grid and the selected regional map to generate a separate
map-specific Input Matrix and `diminfo`. The global `ERA5land_global` matrix
uses 3600 × 1801 input cells and is not interchangeable with the 111 × 91
regional subset. Record the actual map/grid pairing and index checks for Step
14. See [p13](p13-runoff_input_matrix.md), the [Survey Report](AI_survey_report/13_runoff_input_matrix.md), the [Work Report](AI_work_report/13_runoff_input_matrix.md), and [`metadata/13_runoff_input_matrix.json`](metadata/13_runoff_input_matrix.json).

### Step 14 — Simulation Setup and Execution

Use the Step 11 regional map, Step 12 runoff Registry and Step 13 regional
Input Matrix to define and run the requested experiment. The Rhine 2021 sample
has one 31-day, hourly, cold-start run from 2021-07-01 00:00 to the exclusive
end 2021-08-01 00:00. It uses daily ERA5-Land NetCDF input and hourly NetCDF
outputs plus an end-of-run NetCDF Restart. The current run uses the standard
`nextxy.nc` network. The earlier noedge output is no longer present in the
reused `experiment/Rhine2021/` directory. This is an operational run rather
than a spun-up, calibrated or scientifically validated event reconstruction.
KG-0019 remains open. See [p14](p14-simulation_setup-run.md),
the [Survey Report](AI_survey_report/14_simulation_setup.md), the
[Work Report](AI_work_report/14_simulation_setup.md), and
[`metadata/14_simulation_setup.json`](metadata/14_simulation_setup.json).
Generated experiment files are kept under the Git-ignored
`experiment/Rhine2021/` directory.

### Step 15 — Simulation Output Visualization

Use the retained hourly `outflw` and `pthflw` files from Step 14 to map the
signed local maximum absolute discharge over the run period. Fig. 15a shows
the full regional river network in the p02-f02b direction-aware vector style;
Fig. 15b shows the same method in the Step 2 satellite-analysis AOI. Per-link
and per-path peaks can occur at different hours, so neither figure is a
simultaneous flow snapshot. Visualization is an output inspection step; it does not establish
hydrologic skill, resolve the cold-start limitation or replace observation
matching. See [p15](p15-simulation_output_visualization.md), the [Survey
Report](AI_survey_report/15_simulation_output_visualization.md), the [Work
Report](AI_work_report/15_simulation_output_visualization.md),
[`metadata/15_simulation_output_visualization.json`](metadata/15_simulation_output_visualization.json),
and [`f15-maximum_discharge.sh`](f15-maximum_discharge.sh).

### Step 16 — Observation–Model Matching

Define defensible spatial, temporal and variable correspondence between
simulation output, discharge stations, water levels and satellite
classifications. Step 21 supplies checked current-map row/column indices for
the three discharge gauges. Step 22 extracts model flows at those cells and
makes a provisional nominal-time hydrograph overlay; observation time zone and
units remain unresolved, so formal temporal/value matching is still open.
Account for units, time semantics, maps, masks, permanent water, missing
coverage and resolution.

### Step 17 — Event Evaluation

Quantify and interpret model performance only after the simulation and
matching support are defined. Select metrics for the research question, and
report sample coverage, uncertainty and limitations separately by observation
type. No event performance score, calibration result or validation conclusion
has been produced. Do not infer model skill from observation figures alone.

### Step 21 — Gauge and Flood Impact Location Allocation

Keep the unchanged three-gauge CSV for Step22. Impact allocation retains three
levels in `metadata/21_impact_location_allocation.csv`: geographic `model_*`,
direct one-minute `catmxy_*`, and final `river_model_*`. Direct catchment lookup
is the default. For five lower-Ahr reports landing in a mixed mainstem catchment,
use the reviewed Schuld catmxy anchor only after verifying it is exactly one
nextxy edge upstream; record the correction and omitted downstream-area caveat.
Do not choose an arbitrary upstream branch or snap missing assignments.

Run `s21-gauge_allocation.sh --catchment-only` to retain old geographic/gauge
fields; `f21-gauge_allocation.sh` renders Fig. 21a (regional allocation) and Fig. 21b (catchments/proxies).
The prior remote scientific review is preserved in `prior_*` fields, and full
paths/source fingerprints in `metadata/21_catchment_review.json`. Final counts:
16 direct points, 5 upstream proxies, 1 coordinate-missing report. Refer to
[p21](p21-gauge_allocation.md), [Survey](AI_survey_report/21_gauge_allocation.md)
and [Work Report](AI_work_report/21_gauge_allocation.md). Local river support is
not established by lookup/area/topology alone.

Step23 was rerun on 2026-11-24 using the final integrated allocation. Its current
CSV/Figures contain 10 cells × 168 hours and 22 report rows. Fingerprints in
`metadata/23_handoff_status.json` establish input/output currency; the previous
five-selection stale-output notice is resolved. This rerun did not modify the
allocation or rerun the model.

### Step 22 — Model–Observation Hydrograph Comparison

Extract hourly `outflw` at the zero-based row/column cells in Step 21 and
compare it visually with the supplied six-hour station series for
2021-07-10 through 2021-07-31 (end-exclusive 2021-08-01 00:00). Keep both
native time samplings and values;
do not interpolate, average or calculate skill metrics in this exploratory
Step. The model time coordinate is `seconds since 2021-07-01 00:00` and its
reference timezone is interpreted as UTC under the CF convention (the output
file itself has no global `Conventions` attribute). Model `outflw` is in m³/s
and marked `time: mean`. Observation units and timezone remain unspecified;
provider correspondence describes six-hour mean values with interval-end
labels. The shared-axis Figure is therefore a provisional overlay of model UTC
and unadjusted observation labels, not a definitive timing or magnitude
comparison. The reproducible series and interpretation metadata are
[`metadata/22_hydrograph_timeseries.csv`](metadata/22_hydrograph_timeseries.csv)
and [`metadata/22_hydrograph_comparison_summary.json`](metadata/22_hydrograph_comparison_summary.json). See [p22](p22-hydrograph_comparison.md), the [Survey Report](AI_survey_report/22_hydrograph_comparison.md), the [Work Report](AI_work_report/22_hydrograph_comparison.md), and [Figure 22](figure/f22-hydrograph_comparison.png). No performance metrics or event skill conclusion are produced.

### Step 23 — Flood Impact Timing Comparison

For Fig23b, use `f23-impact_timing_comparison.sh --summary-only` to redraw only
the timing summary. Its separate settings default to July14 00:00–July16 00:00
UTC and six-hour ticks; saved peaks/search bounds remain unchanged. Read basin
colors from the Fig1 settings, keep all report rows, use compact uncertainty
codes and show actual timestamps for outside-view arrows. The event note warns
against reading independent tributary peaks as one propagating flood wave.
Fig23a's display and underlying extraction are unchanged.

Use Step 01's report-linked timing ledger and Step 21's reviewed impact
allocation to compare event timing with hourly model outflow. Extract one
series per selected model cell, retaining every report as a separate record.
Use a `confirmed` or `plausible` Step 21 river-assessment cell for local-river
context; preserve geographic containing-cell indices separately. For
`unresolved` or `not_represented` reaches, a containing-cell series is regional
context only and must not be interpreted as local tributary discharge. Search
the model maximum over July 12–18 and plot July 13–16 UTC. Keep unknown or
unconfirmed source timezones off the UTC axis. Compare only source-supported
UTC discharge peaks with lag values; water-level peaks are reference context,
and date-only impacts have no peak-time marker. Mark search-boundary maxima as
inconclusive. See [p23](p23-impact_timing_comparison.md), the [Survey
Report](AI_survey_report/23_impact_timing_comparison.md), the [Work
Report](AI_work_report/23_impact_timing_comparison.md),
[`metadata/23_impact_model_timeseries.csv`](metadata/23_impact_model_timeseries.csv),
[`metadata/23_impact_timing_comparison.csv`](metadata/23_impact_timing_comparison.csv),
[Figure 23a](figure/f23a-impact_hydrographs.png), and [Figure
23b](figure/f23b-impact_timing_summary.png). This remains exploratory timing
comparison, not formal validation or a performance score.

### Step 24 — Flood Inundation Downscaling, Visualization, and Assessment

This is the final assessment Step of the current Tutorial sample. Part A matches
one S1A orbit 038784 acquisition (15 July 2021 morning) to the nearest existing
CF model output: exact five-scene midpoint 05:50:39.8965 UTC →06 UTC (+560.1035 s).
Part B uses the maintained tributary-aware method with Rhine maps to downscale
15 arcmin flddph to 1 arcmin over 4–8°E,49–52°N. Part C visualizes the saved 180×240
product as Fig 24; dry and missing cells are distinct. These outputs already
exist and are retained without rerunning them for documentation completion.

Part D interprets the river-aligned depth distribution in the event's tributary
flood context. Separate model/hydrodynamic, forcing, downscaling and satellite
comparability limitations; distinguish river water from overbank flooding and
valid-support Flood Fraction from full-cell inundation. The appearance alone
does not establish underestimation or the dominant cause. Finer modeling and
terrain/downscaling address different uncertainties and are research options.
Permanent-water and regional-buffer caveats remain. No other acquisition,
quantitative GFM matching, accuracy metric or finer-resolution run is included.
See the [four-part Prompt](p24-inundation_downscaling.md),
[scientific Survey](AI_survey_report/24_inundation_downscaling.md),
[execution Work Report](AI_work_report/24_inundation_downscaling.md),
[Fig 24](figure/f24-inundation_1min.png) and
[technical handoff](metadata/24_downscaling_verification.json).

## 4. Expected Outcomes and Current Status

The intended outcome is a reproducible, evidence-based assessment of CaMa-Flood
for the July 2021 event: selected observation and simulation scopes, prepared
discharge and satellite data, an event experiment, documented model–observation
correspondence, and quantitative results with uncertainty. The retained
Prompts, processing scripts, metadata, figures and reports support that work,
but preparation outputs must not be confused with evaluation results.

| Stage | Existing artifacts and execution evidence | Current research status |
| --- | --- | --- |
| **1 — Event research** | The original 14-location inventory and Figure 1 remain; a source-linked timing/location ledger and qualified timing legend were added from official reports and regional studies. Survey/Work Reports, Prompt and process document were updated. | Gauge/system timing is available for selected river reaches; most town-specific onset or inundation-peak times remain unknown. Gauge timing must not be transferred to every impact locality. |
| **2 — Domain design** | Candidate domain JSON, Figure 2, Prompt and reports exist. | Candidate bounds and mapped routing groups are documented; hydrologic scope and model boundary conditions are not final. |
| **3a — Availability** | Pass metadata, selected-pass JSON, Figure 3a, Prompt and reports exist. | Catalogue survey is documented; pass selection is `proposed`, and footprints do not establish valid flood-pixel coverage. |
| **3b — Download** | Local `Atlantis/` manifest, summary and COG assets are present; the Prompt, downloader and reports exist. | The retained summary records acquisition checks and readiness for p03c. The assets are local/ignored and are not distributed through Git. |
| **3c — Classification** | Flood Fraction raster, focus-area metadata and Figure 3c are present; processing entry points and reports exist. The full-extent 20 m classification TIFF is absent from the current workspace; its provenance record remains. | Processing and screening are recorded, but the full source raster is unavailable here for a new pixel-level check. Focus areas remain proposals and do not represent all detected flooding. |
| **3d — Extraction** | Extraction metadata, 15 focus-area 20 m rasters and Figure 3d are present; extraction/figure entry points and reports exist. | Focus crops are prepared; they are derived observation subsets, not model comparisons or validation results. |
| **4 — Discharge observations** | Provider-supplied source files, Step 4 inventory/metadata, Figure 4 and reports are recorded. Step 21 later verifies their map cells. | Three Rhine gauge series are prepared; discharge units, time zone and original observing agency remain unresolved. |
| **5 — Water levels** | No water-level dataset or preparation workflow is recorded. | Reserved for future work. |
| **6–10 — Reserved** | No activities are specified. | Future research stages. |
| **11 — Regional map** | Local `map/Rhine_15min/` contains map, parameter, NetCDF/COG products and map-local workflow copies matching the requested domain; outputs were inspected, not regenerated for this Step. | Existing products are available to Steps 12–14; upstream hydrology and parameter scientific validation are not established by this inspection. |
| **12 — Runoff preparation** | Existing local Rhine ERA5-Land source and converted data, Step 12 Prompt, metadata and reports are recorded; data were inspected, not reacquired or reconverted for this Step. | Hourly labels and grid structure are documented; KG-0019 remains open, and spin-up adequacy is not established by the Step 14 dates. |
| **13 — Runoff Input Matrix** | Rhine-specific 111 × 91 matrix/diminfo were generated from the actual ERA5-Land grid using the map-local 1-minute catchment assignment; focused dimensions and index checks are recorded. | Step 14 loaded the retained matrix for the 31-day run; this operational check is not independent scientific validation. |
| **14 — Simulation setup and execution** | `s14-run_simulation.sh` ran the 31-day hourly cold-start experiment; 744-record NetCDF outputs and the Restart at 2021-08-01 00:00 were inspected. | Operational completion only; cold-start sensitivity and ERA5-Land time attribution remain unresolved. |
| **15 — Simulation output visualization** | Signed local peak discharge was calculated from the retained `outflw`/`pthflw` outputs; regional and AOI figures and the reusable plotting workflow are recorded. | Spatial output patterns were inspected; no simultaneous snapshot, spin-up assessment or skill evaluation is implied. |
| **16 — Matching** | No matching method or implementation is recorded. | Spatial, temporal and variable correspondence remains to be designed. |
| **17 — Evaluation** | No quantitative event score or performance report is recorded. | Metrics, valid-sample treatment and uncertainty analysis remain future work. |
| **21 — Gauge and impact-location allocation** | The gauge-only CSV remains intact. A separate report-linked impact allocation CSV records geographic cells and reviewed river-assessment candidates; Figure 21, Prompt and Survey/Work Reports were updated. | The geographic cell and river candidate are distinct. Ahr/Erft and several other tributary candidates are plausible at this coarse map scale; five Ahr reports use reviewed upstream proxies and exact local reach support remains uncertain; Prümzurlay uses its direct catchment. |
| **22 — Hydrograph comparison** | Model/observation time-series CSV, source/time summary JSON, three-panel Figure, reusable Prompt and Survey/Work Reports are recorded. | An exploratory overlay is available at the three Step 21 cells. Observation unit and timezone remain unknown; results are not a formal match or performance evaluation. |
| **23 — Impact timing comparison** | Report-linked hourly model series, source-timing comparison CSV, two Figures, reusable Prompt and Survey/Work Reports are recorded. | Three Ahr offsets are provisional (+6 h at Müsch, +2 h at Altenahr and −0.5 h at Bad Bodendorf), all sharing one model cell. Uncertain timing and unsupported river matches remain context-only; no formal score is produced. |
| **24 — Flood Inundation Downscaling, Visualization, and Assessment** | One S1A-time-selected 1min NetCDF, Fig24, provenance and four-part Prompt with scientific Survey/technical Work Report. | Workflow feasibility and limitations are assessed; no quantitative inundation skill claim or separate subsequent assessment Step. |

The Step Prompts, Survey Reports and Work Reports are linked in the Analysis
Workflow above. They provide the detailed instructions, scientific evidence and
execution record respectively; this document explains how those activities
form one research plan.
