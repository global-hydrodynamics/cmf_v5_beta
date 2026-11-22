# Step 1 — Human–AI Event Research Instructions

## Purpose

Step 1 establishes the event evidence needed to plan a flood evaluation. It
summarizes the event's timing, development, major rivers and affected places,
records reported impacts as geographic data, and prepares information for the
Step 2 spatial-domain design. Step 1 does not select CaMa-Flood Basin IDs or
final simulation and satellite-analysis domains.

## Human instructions

Provide these two items to an AI agent:

1. **Flood event:** name, region and year (or known event dates).
2. **Research objective:** for example, evaluating simulated flood extent,
   river discharge, or both.

Use the prompt below after filling in the two bracketed fields. Run it from a
new, event-specific directory outside Tutorial 11. Keep the Rhine 2021
Tutorial 11 sample unchanged; reuse its formats and plotting approach only.

## Example AI agent prompt

```text
I am preparing a CaMa-Flood event evaluation.

Flood event: [EVENT NAME, REGION, YEAR]
Research objective: [RESEARCH OBJECTIVE]

Work only in the current event-specific directory. Treat the Tutorial 11 Rhine
2021 files as examples and do not edit them. First inspect the event overview,
impact-location CSV, Figure 1 Shell and PNG, and domain-design document to
understand their structure. Reuse a suitable Visualization Gallery method and
the current figure-making conventions; do not create an unnecessary plotting
framework.

Task 1 — Research the event
Use real, traceable scientific papers, public authority reports, and reliable
news or situation reports. Verify that each source exists and supports the
statement attributed to it. Summarize:
- event dates and documented temporal development;
- major rivers and watersheds named by sources;
- major affected places and reported impacts;
- relevant hydrologic characteristics;
- candidate observation data and their known limits;
- references with title, issuing body/authors, date, and working URL or citation.

Create `01_flood_event_overview.md`. Separate sourced facts, interpretations,
and unresolved information. Cite sources close to the claims they support; do
not invent event details or treat a candidate dataset as acquired or validated.

Task 2 — Build the impact-location inventory
Create `01_impact_locations.csv`, using the Tutorial 11 sample CSV as a schema
and content example. Record location name, river or river system, country or
region, concise source-reported impact, coordinates, source/citation, and
coordinate confidence where available. Add plotting-only labels or offsets
only when needed by the selected map method. Distinguish approximate town or
locality coordinates from surveyed damage locations and observed inundation
boundaries. Do not infer precise locations or impact severity from a town
marker.

Task 3 — Create the reported-impact map
Create an event-local `f01-reported_flood_impacts.sh` by adapting the Tutorial
11 Figure 1 Shell and a suitable Gallery method. Keep event-specific points
and display settings in the event directory; do not hard-code them into shared
plotting code. Generate `figure/f01-reported_flood_impacts.png` with an OSM
background, the major river network, and labelled reported-impact locations.
Retain required map attribution. Run the Shell and visually inspect the saved
figure for locations, labels, extent, readability, and consistency with the
sources. Do not depict town markers as flood extents.

Task 4 — Prepare the Step 2 handoff
Summarize the major rivers, concentrated impact areas, documented event timing,
candidate satellite search period, candidate observation sources, and
unverified questions that Step 2 should consider. Do not select or finalize
CaMa-Flood Basin IDs, simulation domains, or satellite-analysis domains in
Step 1. Leave those spatial decisions to Step 2, using map routing and event
evidence.

Expected outputs are:
1. `01_flood_event_overview.md`
2. `01_impact_locations.csv`
3. `f01-reported_flood_impacts.sh`
4. `figure/f01-reported_flood_impacts.png`

At completion, report sources checked, files created, commands and checks run,
and remaining uncertainty. Do not claim scientific validation from successful
plot generation.
```

## Expected outputs and human review

| Output | Role |
| --- | --- |
| `01_flood_event_overview.md` | Event background, evidence and references |
| `01_impact_locations.csv` | Geographic inventory of reported impacts |
| `f01-reported_flood_impacts.sh` | Reproducible Figure 1 entry point |
| `figure/f01-reported_flood_impacts.png` | Map of reported-impact localities |

Before proceeding to Step 2, the researcher reviews the event summary and its
sources, the selected impact locations, coordinate accuracy/confidence, and the
rendered Figure. The researcher decides whether the evidence is adequate for
spatial-domain design. Tutorial 11 already contains this Step 1 sample for the
July 2021 western European floods; applying this prompt to another event does
not require rerunning or replacing the Rhine 2021 work.
