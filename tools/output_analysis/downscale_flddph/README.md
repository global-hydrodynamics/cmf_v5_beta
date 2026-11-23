# Python flood-depth downscaling

This standalone package prepares a two-dimensional CaMa-Flood `flddph` field and maps it to the native grid of a higher-resolution CaMa-Flood map. Its scientific method is a Python port of `etc/downscale_flddph/src/downscale_flddph_trib.F90`.

Copy the complete `downscale_flddph/` directory into a research project. The Shell entry points resolve package files relative to their own location; edit their settings at the top to point to the project's map, input, output, extent, and Python environment. No Python module in the repository outside this directory is imported. The map itself remains an external input. `sample_mekong/` is an independent copied example, including copies of the package scripts.

## Contents

```text
downscale_flddph/
├── README.md
├── s01-downscale.sh
├── s02-visualize.sh
├── script/
│   ├── aggregate_flddph.py
│   ├── downscale_flddph.py
│   └── visualize_flddph.py
└── sample_mekong/
    ├── README.md
    ├── s01-downscale.sh
    ├── s02-visualize.sh
    ├── script/                 # physical copies of the three Python files
    ├── out/                    # compact 15-minute input snapshot and source namelist
    ├── downscaled/             # generated 1-minute NetCDF sample
    └── figure/                 # two-panel PNG sample
```

## Requirements and inputs

- Python 3 with NumPy and netCDF4 for snapshot/period selection and downscaling.
- Matplotlib is additionally required to render the comparison figure.
- The low-resolution input is a CaMa-Flood `flddph` NetCDF with `lat`, `lon`, `flddph`, and CF `time` when selecting a record. `flddph` must be in metres and use the map's grid dimensions, cell centres, and north-first row order. The downscaler accepts a 2-D field or exactly one time record; aggregate multi-time inputs before calling it.
- `MAPDIR` points to a matching CaMa-Flood map containing `params.txt`, `nextxy.bin`, `uparea.bin`, and the selected high-resolution map directory. The high-resolution map needs `location.txt`, `catmxy.bin`, `downxy.bin` (or `flwdir.bin`), `flddif.bin`, and `rivwth.bin` for each intersecting tile.
- The current implementation expects a regular geographic map grid whose requested extent and five-coarse-cell buffer align to the selected high-resolution pixel size. It does not reproject or resample.

## Select or aggregate time separately

`aggregate_flddph.py` writes a 2-D NetCDF snapshot or inclusive-period mean/maximum. Selection uses the CF time coordinate, excludes masked/fill values, and records the chosen timestamp or aggregation period and sample count in output attributes. For example:

```sh
python3 script/aggregate_flddph.py \
  --input /path/to/o_flddph2001.nc \
  --output /path/to/flddph_2001-09-01.nc \
  --mode snapshot --time 2001-09-01T00:00:00

python3 script/aggregate_flddph.py \
  --input /path/to/o_flddph2001.nc \
  --output /path/to/flddph_2001-09-01_02_mean.nc \
  --mode mean --start 2001-09-01T00:00:00 --end 2001-09-02T00:00:00
```

The `--start` and `--end` bounds are inclusive timestamps present on the CF time axis. A mean or maximum is computed independently at each cell over its unmasked samples. The downscaling program does no temporal aggregation.

## Run the package

Edit the settings near the top of `s01-downscale.sh`: `PYTHON`, `MAPDIR`, `INPUT_NC`, `OUTPUT_NC`, the west/east/south/north output edges, and `RES`. Then run:

```sh
bash s01-downscale.sh
```

The output is a compressed NetCDF4 file containing Float32 `flddph(lat,lon)` in metres, WGS84 cell-centre coordinates, and `_FillValue=-9999`. Attributes record the source input, map directory, high-resolution map tag, spatial method, output extent, and temporal-selection attributes copied from the prepared input. The five-coarse-cell buffer is used internally and cropped away from the output.

Edit settings in `s02-visualize.sh` and run it separately to compare the native-grid input with the downscaled field over the same geographic extent. Visualization never reruns the downscaling calculation.

## Mekong sample

See [sample_mekong/README.md](sample_mekong/README.md) for the input provenance, settings, numerical comparison, and commands. From the sample directory, after activating an environment with the dependencies above:

```sh
bash s01-downscale.sh
bash s02-visualize.sh
```

The sample was tested against both the existing p02-f04 Fortran output and a fresh run of the legacy Fortran reference. Its comparison establishes port fidelity for one Mekong date/map/extent only; it does not independently validate the hydrologic method or demonstrate global-map compatibility.

## Method and limits

The Python code preserves the Fortran operation sequence: assign each high-resolution pixel to its low-resolution catchment, subtract `flddif` from catchment flood depth, identify mainstem and tributary outlet paths using `nextxy`/`uparea`, apply tributary adjustment, propagate backwater adjustment, and apply the 0.1 m permanent-water minimum using `rivwth`. Map and output arrays use north-first rows; binary map records are read in their existing x-fast layout. Float32 arithmetic is used for the scientific fields and comparison-sensitive operations.

This is a direct method port, not a replacement parameterization. Validation currently covers one 1-minute Mekong map sample. Other regions, map formats, resolutions, edge cases and compilers have not been exhaustively verified. The visualized `flddif` background is map context and is not an additional scientific output.
