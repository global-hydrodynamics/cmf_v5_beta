# Tutorial02 Map Format Compatibility — Work Report

**Date:** 2026-11-28  
**Development level:** L1 — focused compatibility validation

## Scope and implementation status

The active Tutorial02 visualization scripts were inspected against the current Mekong map. The requested migration is already present in the current source, so no visualization code or map data required modification:

- `v01-network_maps.py` reads geometry through the shared `map_metadata.read_map_geometry()` reader, selecting the v5 `params.nml` geometry.
- It reads the 1-minute tile inventory from `map/mekong_15min/1min/location.csv` through `hires_metadata.read_location_csv()`.
- It reads `1min.catmxy.nc` variables `catmxx` and `catmyy`, preserving `(lat, lon)` array orientation and one-based map indices.
- Base-resolution network fields, outlets, basin colors, and bifurcation parameters are read from individual NetCDF files at the map root. `v04` reuses the network helpers in `v01`.
- `v02`–`v04` read the existing NetCDF simulation outputs; no legacy map reader is used by those comparison scripts.

## Validation

The complete `v00-visualize_all.sh` workflow was run with the repository `.venv` Python in an isolated temporary mirror at `/tmp/tutorial02-map-check.Pwbue4/`. The map and four experiment-output directories were linked as read-only inputs; generated figures and analysis NetCDF files were written only in the temporary tree.

All commands returned status 0. The run reported:

- Map grid: 80 × 120; 6,566 valid river cells and 3,150 valid downstream connections.
- High-resolution `catmxy`: 1,200 × 1,800; 1,416,132 mapped pixels and 6,566 distinct mapped cells.
- `bifprm.nc`: 425 valid endpoints (77 channel and 348 overland paths).
- Figures `f01a`–`f01d` and `f02`–`f04` were generated. All seven generated images were visually inspected; the plotted layers and locations appeared coherent, with no obvious missing data or spatial displacement.
- Existing `sample_figure/` images were not modified. New images differed in raster dimensions from references by at most six pixels per axis; visual inspection found no material content or layout anomaly. No scientific interpretation was inferred from this rendering check.
- `v02`, `v03`, and `v04` regenerated their analysis NetCDF products in the temporary directory from the existing simulation outputs. Model simulations were not rerun.

## Deferred documentation issue

`tutorial_design.md` still contains two statements that say `v01-network_maps.py` expects retired `params.txt` and `location.txt` files and that migration is separate work (in the Figure 1 description and activity table). Those statements are obsolete, but the task specifically excluded Tutorial Design and Manual Design updates; they are left for a documentation-only follow-up.

## Limits

This confirms operational rendering against the local Mekong map and retained experiment outputs. It does not validate scientific results or assess unrelated Tutorial02 workflows. No source map, simulation output, or supplied reference image was changed.
