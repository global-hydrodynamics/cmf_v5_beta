# Tutorial 11 Map and Runoff Relocation

Date: 2026-11-28

## Scope

Moved the Rhine event Map and ERA5-Land Runoff into Tutorial-owned directories:

- `map/Rhine_15min/` → `tutorial/tutorial11-event_evaluation/map/Rhine_15min/`
- `inp/tutorial11-ERA5land-Rhine2021Jul/` → `tutorial/tutorial11-event_evaluation/inp/ERA5land-Rhine2021Jul/`
- Tutorial-specific downloader settings → `run_script/s12-prepare_runoff.sh`

The Runoff directory contains 126 files (35,022,371 bytes); every file retained
its pre-move size and SHA-256. The map contained 94 files (4,370,863 bytes);
all files remain present. Its numerical products retained their hashes; the
seven changed files are three map-local READMEs and four map-local Shells with
intended path/documentation updates. No dataset was regenerated or downloaded.

Added optional `--inp-root` support to the shared ERA5-Land workflow. Its
default remains the repository `inp/`; Step 12 passes the Tutorial-local root
and current dataset ID `ERA5land-Rhine2021Jul`. The previous
`tutorial11-ERA5land-Rhine2021Jul` ID remains recorded as historical metadata.
The Step 13 current contract now points to the relocated NetCDF matrix and
DIMINFO; historical Binary-generation records and validation details remain
unchanged. Step 14 and Step 15 have explicit current-location metadata
contracts while retaining their past execution paths.

Updated the Tutorial README, active Step 11–15/21/24 Prompts, runoff registry,
shared downloader README, moved Map READMEs and Map-local allocation/source
paths. Removed the Rhine-specific ignore rule from `map/.gitignore`; the
Tutorial `.gitignore` keeps Map/Runoff data ignored while allowing small local
workflow scripts and READMEs to be tracked.

## Focused validation

- `bash -n` passed for all 57 affected Map-local, Tutorial run/plot and shared
  downloader Shell files. Python syntax, all Tutorial metadata JSON, the CSV
  registry, NetCDF matrix variables/shapes (30 × 32 planes) and a runoff file
  shape (24 × 91 × 111) passed focused checks.
- Step 12 `--dry-run` resolved the output to the Tutorial-local directory and
  planned the retained July download/conversion requests; no download ran.
- Step 14 path contract resolves to the local Map, Runoff, NetCDF Input Matrix
  and DIMINFO. The simulation was not rerun.
- Step 15 read the retained 744-record simulation and relocated map, writing
  its analysis NetCDF and two review figures under `/tmp`; the regional figure
  was visually checked.
- Step 21 ran on a disposable copy of the relocated map. Its existing GRDC
  allocation prerequisite was generated in that temporary copy only; the
  workflow allocated all three gauges and 22 impact reports. Both review
  figures were written under `/tmp` and checked. The retained map and metadata
  were not changed.
- Step 24 downscaling read the retained simulation and relocated Map, wrote a
  180 × 240 NetCDF and temporary metadata under `/tmp`, and rendered a temporary
  review figure. The figure was visually checked.
- Git-ignore checks confirmed that regional Map products and Runoff files are
  ignored while the Map README and Shell scripts remain trackable. Markdown
  links in moved Map READMEs and `git diff --check` passed.
- The broader Tutorial landing-page link check found its pre-existing link to
  `AI_survey_report/00_scientific_results_en.md` has no local target because
  that file was already deleted in the working tree. The deletion was preserved
  and excluded from this relocation commit.

No CaMa-Flood simulation, map generation, ERA5-Land download, GFM acquisition,
or scientific reassessment was performed. The pre-existing Step 21 map-local
`GRDC_alloc.csv` is absent; full validation used a generated temporary copy.
KG-0019 time attribution remains unresolved. Historical report/metadata paths
and local scientific results were preserved.
