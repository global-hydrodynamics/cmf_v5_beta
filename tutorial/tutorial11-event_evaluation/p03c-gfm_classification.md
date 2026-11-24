# p03c — GFM Classification and Focus-Area Selection

### How to Use This Workflow

**Rhine 2021:** Keep the current pass, domain, classification and display
settings; supply the entire Markdown file as an attachment or copy its full
content, reusing the established Step 03b handoff.

**Another event:** Set the event-directory placeholder and review the manifest,
selected pass, Step 02 domain and focus-area settings in their existing JSON/Shell
locations. Verify native CRS/resolution, target-grid support and compatibility
with the existing class definitions and precedence; do not silently change
classification or Flood Fraction semantics. Review valid support and focus-box
selection for the new observations, and inspect implementation dependencies.
Then provide the entire updated file to the agent. Changing event labels alone
does not make scripts or observations compatible.

The execution block and Interpretation section must be supplied together; the
block is not a standalone Prompt. Rhine's completed products do not establish
availability or completion for another event.

## Workflow Summary

### Inputs
- Step 3b download manifest/summary and native GFM COGs
- `metadata/02_domain_selection.json` for the candidate satellite-analysis domain

### Tasks
- Create the native 20 m classification mosaic, calculate 1 arc-minute Flood Fraction, select focus boxes, and render Figure 3c.

### Outputs
- `AI_survey_report/03c_gfm_classification.md`
- `AI_work_report/03c_gfm_classification.md`
- Classification GeoTIFF and provenance JSON, Flood Fraction GeoTIFF, focus-area JSON, and Figure 3c

## Human Instructions

Provide the event directory and confirm that Step 3b's manifest and required COGs are available. The agent must use the existing classification definitions and processing entry points. A proposed focus selection can be consumed by Step 3d.

## Example AI Agent Prompt

```text
Complete Step 3c GFM classification and screening for this event.

Event directory: [PATH]

1. Use the p03b manifest as the input list; do not re-search or redownload.
   Preserve original native CRS, 20 m grid/pixel alignment and categorical
   meanings. Keep NoData, Exclusion and Inconsistent distinct; do not infer dry
   pixels from missing observations. Follow existing classification precedence.
2. Run the existing `run_script/s03c-classify_gfm_extent.sh` workflow to produce the
   native-grid uint8 classification and provenance JSON. Do not change class
   codes or silently mix independent passes.
3. Run `plot_script/f03c-flood_fraction_1min.sh` to aggregate by source-pixel centres into
   WGS84 1-arc-minute cells. Flood Fraction is Code 1 divided by valid classes
   0–4, in percent. Codes 5, 6 and 255 are not denominator pixels; no valid
   support is NoData, while a supported zero fraction is 0. Do not describe
   this statistic as a full-cell inundated area fraction.
4. Review flood-pixel counts and valid support to select compact focus boxes
   inside the satellite-analysis candidate area. Do not use impact-location
   proximity as a selection criterion. Save proposed boxes/diagnostics in
   `metadata/03c_focus_areas.json` and include retained/missed Flood counts,
   area/pixel reduction and size estimate. Avoid overclaiming that the boxes
   are optimized or fully capture the event.
5. Render Figure 3c from the saved fraction, locations and focus JSON using
   `plot_script/f03c-flood_fraction_1min.sh`. Preserve existing figure conventions and
   inspect the image.
6. Create/update `AI_survey_report/03c_gfm_classification.md` and
   `AI_work_report/03c_gfm_classification.md`. The Survey Report explains the
   spatial pattern, values, focus-area tradeoff and scientific limits. The Work
   Report records actual inputs, commands, outputs, checks and Step 3d handoff.

Complete the initial proposed selection and outputs without waiting for Human
review. Feedback updates the same metadata and figure. Status does not gate
processing. Do not carry out Step 3d extraction in this workflow.
```

## Interpretation

GFM class 1 is an observation-derived classification, not independent truth. Fraction is conditional on usable classes 0–4; sparse support can yield high fractions. Focus boxes are a storage/inspection selection, not a claim that other flood detections did not occur.
