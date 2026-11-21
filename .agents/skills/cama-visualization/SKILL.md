---
name: cama-visualization
description: Use when creating or modifying CaMa-Flood visualizations, visualization project scripts or data settings, Tutorial figures that follow the visualization conventions, or Visualization Gallery/catalog entries.
---

# CaMa-Flood Visualization Workflow

Use this workflow only for visualization-related work. The formal requirements remain in the repository guides; read them rather than copying their rules here.

## Before implementation

1. Read `visualization/repository_development_guide.md`, `visualization/figure_making_guideline.md`, and the applicable `AGENTS.md` instructions.
2. Inspect `visualization/visualization_catalog.csv` and the closest relevant implementation and project README. Search by scientific purpose as well as by ID or filename.
3. Classify the task: new Figure, Figure modification, visual adjustment, data/settings update, documentation-only, or Gallery publication.
4. Identify the Figure/Panel IDs, method and option names, Shell/Python files, inputs and their provenance, output paths, documentation, and the checks needed for this task. Make a focused plan before editing.
5. If the request conflicts with a formal convention or leaves a scientific meaning materially ambiguous, state the conflict and resolve the scope with the maintainer before dependent changes.

## During implementation

- Follow the project structure and naming rules in the development guide; reuse a scientifically suitable catalog method or shared code where practical.
- Keep scientific data handling and presentation accurate: preserve variable meaning, units, missing-value behavior, coordinate order, river connectivity, spatial extent, and provenance. Do not infer undocumented science from visual similarity.
- Keep Shell focused on user-facing paths, settings, and workflow; keep plotting/data processing in the project implementation. Store numerous event-specific locations or display settings in a clear external data/config file when useful, and avoid maintaining the same setting in two places.
- Generate project figures under the project's `figure/` directory. Ordinary development and review must not alter `visualization/gallery/`; publication requires explicit user authorization.
- Limit edits to the assigned visualization and directly necessary documentation. Do not refactor unrelated figures or components.

## Before completion

Compare the actual implementation against the relevant guide requirements; do not report only that the guides were read. Check applicable items below and repair in-scope mismatches.

| Task | Focused checks |
| --- | --- |
| New Figure | Structure and naming; reproducible inputs; scientific meaning and provenance; render and visually inspect the figure; documentation and catalog consistency. |
| Figure modification | Changed behavior and dependent files; applicable scientific/display conventions; run the affected workflow and inspect the result when rendering is affected. |
| Visual adjustment | Inspect the rendered target for extent, axes/ticks, colors, contrast, legend, panel alignment, and aspect ratio as relevant. |
| Data/settings update | Verify input paths, schema, units/coordinates/meaning and provenance; confirm affected outputs or a focused dry-run. |
| Documentation only | Check terminology, IDs, filenames, and modified local links against current files and catalog entries. |
| Gallery publication | Confirm explicit authorization; check the approved image, Gallery README, project README, catalog IDs/paths/status, and attribution/provenance together. |

For a multi-panel Figure, verify panel names and outputs against the combined Figure. Set catalog validation status only when the described workflow was run and its output reviewed; distinguish syntax/path checks from rendering, and rendering from scientific validation. Gallery publication is a separate approval step, not implied by successful development or review.

Report the files changed, the focused checks and their results, any limits to visual or scientific verification, and unresolved issues. Do not run unrelated figures or the full visualization suite unless the task calls for it.
