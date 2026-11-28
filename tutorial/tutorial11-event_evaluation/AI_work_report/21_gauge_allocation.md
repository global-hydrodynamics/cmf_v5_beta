# Step 21 — Integrated Allocation Work Report

Integrated local `8871bcfa` and remote `d3016eac` (including `72aee06c`) on the
existing `feature/package-builder` branch, with maintainer authorization to
adopt catmxy and use reviewed one-step upstream tributary correction. No new
branch, history rewrite, map regeneration or simulation run.

## Inputs, preservation and implementation

Use the restored 40 × 32 Rhine map, 600 × 480 one-minute catmxy, Step01 inventories
and 22-row impact CSV. The reader/boundary functions remain the unchanged p01-f04
implementation. Binary is two complete little-endian int16 x/y planes; indices
are one-based regional model cells, converted to row=y−1,col=x−1. Pixel geometry
and Binary/NetCDF equality were verified in VR-0211.

Three assignment levels remain explicit: original geographic model_* fields,
direct catmxy_* fields, and final river_model_* fields. Preserve published remote
review fields/notes in prior_* columns and original notes before the appended
review suffix. The gauge CSV and unrelated bin2nc_list.txt edits are preserved.
The final selection uses 16 direct points and five named Ahr upstream proxies;
Eupen remains unassigned. Every proxy derives its candidate from the directly
mapped Schuld anchor and verifies that candidate's actual nextxy points exactly
to the report's raw catchment, with valid outlet/width and smaller positive area.
Missing/invalid anchors or topology leave the evaluation unresolved. No arbitrary
incoming branch, coordinate-nearest outlet or largest-area rule is used.

Existing remote Kordel scientific confirmation is retained only when its reviewed
cell equals direct catmxy; Prüm's old no-candidate assessment is superseded by
the verified direct 580.627 km² cell. Old review evidence remains visible.

## Execution and affected outputs

```sh
MPLCONFIGDIR=/tmp/cmf-mpl-cache bash run_script/s21-gauge_allocation.sh --catchment-only
MPLCONFIGDIR=/tmp/cmf-mpl-cache bash plot_script/f21-gauge_allocation.sh
```

Writes the impact CSV, full-path/source-hash JSON and two Step21 Figures. The
regional Figure and catchment companion show only adopted `river_model_*`
outlets and connectors. Historical/geographic/raw alternatives remain in the CSV
but are excluded from both Figures; labels and legends identify final cells.
Prompt, Survey Report, this report, process/log/dashboard and research evidence
are aligned to the final contract.

Step23 integration is limited to propagating the final selection method from
Step21 into the existing cell-selection interface. No Step23 extraction or
peak comparison is executed. Its remote CSV/PNG outputs remain byte-identical;
metadata/23_handoff_status.json marks them as requiring re-extraction for five
changed report selections. This is an explicit historical handoff, not a claim
that old timing results use the new cells.

## Validation and remaining questions

L1 checks cover 22 IDs and original geographic fields/notes, direct lookup
preservation, all five immediate predecessor edges, valid outlets/areas, invalid
anchor/edge behavior, final Step23 selector compatibility, no invalid-point snap,
repeat-output stability, gauge CSV equality, source hashes, Shell/AST/links/diff,
and visually reviewed Figures. The prior research validator has 22 unrelated
errors, which remain outside scope. Exact lower-Ahr reach support remains open
(KG-0039); upstream proxies omit downstream area. Existing observation timezone/
units and forcing-time limitations remain. No model-skill conclusion follows.

## Subsequent Step23 rerun — 2026-11-24

The maintainer subsequently authorized Step23 re-execution. It now contains
10 cells × 168 hours and all 22 reports using the final evaluation cells.
The earlier integration-only stale-output statement above is historical;
23_handoff_status.json records current input/output fingerprints. The Step23
Work Report describes the execution; Step21 allocations were unchanged.


## Current map-interface follow-up — 2026-11-28

Updated the Step 21 scripts to use shared `params.nml` geometry, current map-root NetCDF layers, and `location.csv` plus NetCDF `catmxx/catmyy` through the maintained p01-f04 reader. The current-format catchment-only processing and both figures completed using a temporary copy of the allocation CSV and outputs under `/tmp`; retained CSVs, metadata and figures were not overwritten. The Figure 21 outputs were visually inspected.

The current local map produces one changed direct assignment relative to the retained allocation: `impact-pruem-pruemzurlay` changes from one-based (x=14,y=12), zero-based row/column (11,13), outlet (6.447917°E,49.850418°N), upstream area 580.627 km² to (x=14,y=13), row/column (12,13), outlet (6.499584°E,49.811249°N), upstream area 4,221.565 km². The old Binary catmxy/location files referenced by the preserved historical hashes are absent locally, so exact Binary-versus-NetCDF equivalence cannot be checked. This map/data-dependent scientific difference was not adopted; the retained allocation and Step 23 handoff remain unchanged and require researcher review before any refresh.
