# Mekong Flood Depth and Duration sample

This directory contains a portable copy of the package scripts. The Python files in `script/` are physical copies; they do not import from the package parent. The Mekong map and annual simulation output remain external inputs.

## Inputs and configuration

- Run the `gosh_test/mek02` 2001 simulation first. The default annual input is `gosh_test/out/mek02/o_flddph2001.nc`; change `SOURCE_NC` at the top of the sample Shells if it lives elsewhere.
- Depth uses the exact CF snapshot `2001-09-01T00:00:00`. If `out/flddph_2001-09-01.nc` is absent, `s01-downscale_flddph.sh` extracts it with the copied `aggregate_flddph.py`. An existing snapshot is reused and never removed or overwritten by the preparation step.
- Duration reads the annual NetCDF directly and does not copy it into this directory. This input has 365 timestamps from 2001-01-02 through 2002-01-01. They are daily end-time samples for the 2001 simulation interval; `t01-downscale_duration.sh` uses these exact inclusive CF dates.
- The default map is `map/mekong_15min/`, with its 1-minute high-resolution layers. Change `MAPDIR` in the Shells when using the sample independently.
- Both products cover 102–108°E, 9–15°N at 1 arc-minute (360 × 360).

## Run in order

Activate an environment with NumPy and netCDF4; Matplotlib is also needed for Figures. From this directory:

```sh
bash s01-downscale_flddph.sh
bash s02-visualize_flddph.sh
bash t01-downscale_duration.sh
bash t02-visualize_duration.sh
```

The first command prepares/reuses the depth snapshot and generates the high-resolution depth file. The second renders its native/downscaled comparison. The third calculates the low-resolution 401-level depth-duration table and maps the `flddif` threshold lookup to a 1-minute `flood_duration` field plus a separate `permanent_water` mask. The fourth renders the native-grid and high-resolution duration panels. All settings are grouped at the top of their Shell.

## Products and Git policy

- `out/` is ignored by Git. It contains the regenerable 2001-09-01 input snapshot and intermediate depth-duration table. The legacy copied `input_cmf_2001.nam` is not needed.
- `downscaled/flddph_1min_2001-09-01.nc` and `downscaled/flood_duration_1min_2001.nc` are compact generated examples and are tracked.
- `figure/flood_depth_2001-09-01.png` and `figure/flood_duration_2001.png` are tracked sample Figures.
- The annual input and map data are never copied into the sample.

## Scientific method and checks

Flood Depth preserves the existing tributary-aware Python port. The Duration workflow ports `calc_depth-duration.F90` and `downscale_fldprd.F90`: thresholds use strict `flddph > max(0.01, k × 0.05 m)`, high-resolution threshold selection uses `catmxy` and `flddif`, negative `flddif` yields zero days, and no tributary/backwater filling is performed. Permanent water is stored separately; the legacy `999` value is not treated as a day count.

The 2001 sample uses 365 daily records. The generated 401 × 120 × 80 duration table matched the compiled legacy `calc_depth-duration.F90` output exactly. In the 360 × 360 high-resolution result, all 84,184 non-permanent valid pixels matched the Fortran `downscale_fldprd` output exactly; all 11,359 permanent-water pixels corresponded to the legacy 999 marker; the NoData mask also matched. This is implementation-parity evidence for this one Mekong map, 2001 period and extent, not independent validation of the hydrologic method or proof for other grids.

The Duration Figure labels the native panel as days above the 0.01 m minimum threshold. The high-resolution panel uses per-pixel `flddif` thresholds, so both use day units but not one common depth threshold. Permanent water uses a distinct teal overlay and is not part of the duration colorbar.
