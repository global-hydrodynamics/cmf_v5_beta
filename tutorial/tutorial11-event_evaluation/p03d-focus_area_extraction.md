# p03d — Extract GFM Focus Areas

### How to Use This Workflow

**Rhine 2021:** Use the current classification, focus selection and figure
settings. Supply the entire Markdown file as an attachment or copy its full
content, including Scientific limits.

**Another event:** Set the event-directory placeholder and review the source
raster, selected boxes and pass identity in the Step 03c handoff. Verify the
native CRS/grid, class values and NoData contract before applying the unchanged
extraction method. Inspect script paths and display dependencies; do not assume
that editing this file adapts them. Give the entire updated file to the agent
once required inputs and scientific choices are established. A retained Rhine
crop is not an output for the new event.

The execution block is part of the full document, not a standalone Prompt.

## Workflow Summary

### Inputs
- Native classification COG from Step 3c
- `metadata/03c_focus_areas.json`

### Tasks
- Extract each WGS84 focus bbox on the source-aligned Equi7 20 m grid and create a compact review Figure.

### Outputs
- `AI_survey_report/03d_focus_area_extraction.md`
- `AI_work_report/03d_focus_area_extraction.md`
- One uint8 GeoTIFF per focus area, `metadata/03d_extracted_areas.json`, and Figure 3d

## Human Instructions

Provide the event directory and ensure the source classification raster and focus-area JSON are present. `proposed` focus areas are executable; do not introduce an approval gate.

## Example AI Agent Prompt

```text
Complete Step 3d extraction for the selected GFM focus areas.

Event directory: [PATH]

1. Read the source raster and boxes from `metadata/03c_focus_areas.json`.
   Use `run_script/s03d-extract_gfm_focus_areas.sh`. Project and outward-align each box
   to the source grid. Do not reproject, resample or reclassify. Preserve source
   CRS, 20 m resolution/alignment, uint8 class values and NoData=255.
2. Write the per-area GeoTIFFs under `observation/GFM_extent/` and the canonical
   `metadata/03d_extracted_areas.json`. Record WGS84 and projected bounds,
   source/selection identity, dimensions, relative output paths, class counts,
   checksums and file sizes. Do not create versioned metadata copies.
3. Run `plot_script/f03d-gfm_focus_areas_20m.sh` to regenerate Figure 3d from the extraction
   metadata. Use the existing categorical display and OSM background; do not
   add the CaMa river network unless the established figure specification
   changes. Inspect readability and marker/class alignment.
4. Create/update `AI_survey_report/03d_focus_area_extraction.md` and
   `AI_work_report/03d_focus_area_extraction.md`. Explain each crop's spatial
   classification, size reduction, handoff utility and limitations. Record
   actual commands, input availability, checks, and any missing files. Separate
   verified current files from values inherited from prior metadata.

Complete the initial extraction and reports without waiting for Human review.
Review is recommended but not a program gate. Missing source files remain
ordinary processing errors; do not silently skip areas.
```

## Scientific limits

The extraction is a storage/spatial subset of an existing observation class map. Densified projected bbox edges snapped outward to source pixels can include pixels just outside the WGS84 rectangle. Cropped classes do not validate event inundation or model performance.
