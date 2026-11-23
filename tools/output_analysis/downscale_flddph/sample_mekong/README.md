# Mekong downscaling sample

This is a portable example copied from the standalone `downscale_flddph` package. The Python files in `script/` are physical copies of the package scripts; the sample Shell settings point to the Mekong map and this directory's input and outputs. It does not import code from the parent package.

## Provenance and settings

- Simulation: `gosh_test/mek02-2year_netcdf.sh`, Mekong 15-minute map, annual NetCDF outputs for 2000 and 2001.
- Source data: `gosh_test/out/mek02/o_flddph2001.nc`, run on 2026-11-23. The tracked compact input `out/flddph_2001-09-01.nc` was extracted by exact CF timestamp `2001-09-01 00:00:00`; it has 120 × 80 cells and contains the 2-D `flddph` field plus coordinates and selection metadata.
- `out/input_cmf_2001.nam` is copied from the completed 2001 experiment as configuration provenance. It contains machine-specific paths and is not read by either package script.
- Map: repository `map/mekong_15min/`; high-resolution map: `1min`.
- Downscaling extent: 102–108°E, 9–15°N; output grid: 360 × 360 at 1 arc-minute.
- The sample snapshot contains 6,566 valid low-resolution cells. The generated high-resolution result contains 95,543 valid pixels, has maximum depth 17.5255909 m, and is approximately 108 KiB.

## Run

Activate a Python environment with NumPy, netCDF4 and Matplotlib, then from this directory run:

```sh
bash s01-downscale.sh
bash s02-visualize.sh
```

The first command writes `downscaled/flddph_1min_2001-09-01.nc`; the second writes `figure/flood_depth_2001-09-01.png`. The settings are at the beginning of each Shell script. The Figure follows p02-f04's side-by-side native and downscaled flood-depth presentation, using a 0–20 m shared color range and the p02-f04 `flddif` grayscale stretch. Undefined `flddif` cells use neutral gray where `elevtn` identifies land; unmapped background and the sea are white. The flood-depth overlay is masked where `catmxy` has no coarse-grid mapping.

The downscaling Shell defaults to `INPUT_FORMAT=auto`, `MAP_FORMAT=auto`, `TRIBUTARY_FILL=1`, and `PERMANENT_WATER=1`. Auto prefers NetCDF map layers and falls back to a matching Binary layer only when that NetCDF file is absent; it does not hide read or metadata errors by switching formats. To use the legacy Binary maps, change `MAP_FORMAT` to `binary`. The input may be NetCDF or one headerless little-endian Float32 Binary record with the map's `nx × ny` cells, x-fast and north-to-south. Binary snapshots have no time metadata. Tributary Fill OFF disables tributary and backwater adjustments; Permanent Water OFF independently removes only the 0.1 m minimum. Output NetCDF attributes list the formats and actual source-file paths relative to `map_directory`.

## Numerical comparison

The Python output was compared cell-by-cell with a fresh compilation and execution of the unchanged `etc/downscale_flddph/src/downscale_flddph_trib.F90`, using the same CF-selected snapshot, map, resolution, and extent. Both arrays have 360 × 360 cells, 95,543 valid cells, and identical valid/NoData masks. Of the valid cells, one differs; the maximum absolute difference is 2.3841858 × 10⁻⁷ m (less than 10⁻⁵ m). Tributary, backwater, and permanent-water diagnostics were non-zero (413, 468, and 16,486 pixels respectively, counted over the buffered working grid), exercising these code paths. The calculated extent used a 510 × 510 buffer, corresponding to the existing five coarse-grid-cell margin.

The generated Python result has the same valid mask as the regenerated p02-f04 Python result; their maximum absolute difference is 3.34 × 10⁻⁶ m, within the 10⁻⁵ m comparison tolerance. Agreement against this one sample is evidence of implementation fidelity for this case, not independent scientific validation or coverage of other maps.

### Format and option compatibility

The default NetCDF/NetCDF run exactly matches the tracked sample (95,543 valid cells; maximum absolute difference 0 m). NetCDF `flddph` with Binary maps and Binary `flddph` with NetCDF maps both match the default output exactly, including the valid mask. The four tributary/permanent-water combinations retain the same 95,543 valid cells. Tributary Fill OFF with Permanent Water ON matches the unchanged basic Fortran routine exactly for all shared cells and the missing-value mask. In this sample, disabling the permanent-water minimum changes 3,331 pixels. Map format/source paths and both option values are recorded in output NetCDF attributes. These checks establish compatibility for this sample only.
