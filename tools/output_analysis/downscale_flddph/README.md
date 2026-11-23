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
- The low-resolution input is normally a CaMa-Flood `flddph` NetCDF with `lat`, `lon`, and `flddph`; CF `time` metadata is preserved when present and selected by the separate aggregation utility. The downscaler accepts a 2-D field or exactly one time record. A headerless, little-endian Float32 Binary snapshot is also supported with exactly `nx × ny` values in x-fast, north-to-south order; Binary has no timestamp. Set `INPUT_FORMAT=auto|netcdf|binary` in the Shell. Auto identifies NetCDF by `.nc`, `.nc4`, or `.cdf`, and Binary by `.bin`, `.dat`, or `.raw`.
- `MAPDIR` points to a matching CaMa-Flood map containing `params.txt` and the required low- and high-resolution layers. NetCDF map files are preferred by default, with the existing Binary map files retained as a compatibility format. Set `MAP_FORMAT=auto|netcdf|binary`. Auto resolves each required layer independently, preferring NetCDF and falling back to Binary only when the NetCDF file is absent. A present but invalid NetCDF file is reported as an error. Mixed formats are supported. The program records the actual source files and formats in output attributes and stdout; only high-resolution tiles intersecting the requested region are read.
- Low-resolution inputs are `nextxy` and `uparea`; high-resolution inputs are `catmxy`, `flddif`, `rivwth`, and either `downxy` or `flwdir`. NetCDF layers are checked against their expected dimensions and map cell-centre coordinates. Binary record lengths are checked against dimensions from the map metadata.
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

Edit the settings near the top of `s01-downscale.sh`: `PYTHON`, `MAPDIR`, `INPUT_FORMAT`, `MAP_FORMAT`, `INPUT_FILE`, `TRIBUTARY_FILL`, `PERMANENT_WATER`, `OUTPUT_NC`, the west/east/south/north output edges, and `RES`. Both calculation options default to `1`. `TRIBUTARY_FILL=0` skips tributary and backwater adjustments and uses the basic catchment-based depth; `PERMANENT_WATER=0` independently omits only the 0.1 m river-width minimum. Then run:

```sh
bash s01-downscale.sh
```

The output is a compressed NetCDF4 file containing Float32 `flddph(lat,lon)` in metres, WGS84 cell-centre coordinates, and `_FillValue=-9999`. Attributes record the source input and format, map directory and actual layer files/formats (source-file paths are relative to `map_directory`), high-resolution map tag, selected options, spatial method, output extent, and temporal-selection attributes copied from a NetCDF input. Binary input does not receive an inferred timestamp. The five-coarse-cell buffer is used internally and cropped away from the output.

Edit settings in `s02-visualize.sh` and run it separately to compare the native-grid input with the downscaled field over the same geographic extent. Visualization never reruns the downscaling calculation.

## Mekong sample

See [sample_mekong/README.md](sample_mekong/README.md) for the input provenance, settings, numerical comparison, and commands. From the sample directory, after activating an environment with the dependencies above:

```sh
bash s01-downscale.sh
bash s02-visualize.sh
```

The sample was tested against the pre-migration p02-f04 Fortran output and a fresh run of the unchanged legacy Fortran reference. Its comparison establishes port fidelity for one Mekong date/map/extent only; it does not independently validate the hydrologic method or demonstrate global-map compatibility.

## Method and limits

The Python code preserves the Fortran operation sequence: assign each high-resolution pixel to its low-resolution catchment, subtract `flddif` from catchment flood depth, identify mainstem and tributary outlet paths using `nextxy`/`uparea`, apply tributary adjustment, propagate backwater adjustment, and apply the 0.1 m permanent-water minimum using `rivwth`. Map and output arrays use north-first rows; binary map records are read in their existing x-fast layout. Float32 arithmetic is used for the scientific fields and comparison-sensitive operations.

This is a direct method port, not a replacement parameterization. Validation currently covers one 1-minute Mekong map sample. Other regions, map formats, resolutions, edge cases and compilers have not been exhaustively verified. The high-resolution Figure uses the same `flddif` percentile/square-root grayscale stretch as p02-f04. Where `flddif` is undefined but `elevtn` is valid, it draws neutral mid-gray land context; unmapped background and the sea are white. `catmxy` validity masks the flood-depth overlay, so no depth is drawn where a high-resolution cell has no coarse-grid catchment mapping. These background layers are map context, not additional scientific outputs.

### Input-format and option checks

For the Mekong 2001-09-01 sample, NetCDF `flddph` + NetCDF maps with both options ON reproduced the tracked sample exactly (95,543 valid cells; maximum absolute difference 0 m). NetCDF maps + Binary `flddph`, and Binary maps + NetCDF `flddph`, each had the same valid mask and exact values as the NetCDF/NetCDF run. The four option combinations all retained 95,543 valid output cells. Tributary Fill OFF with Permanent Water ON matched the unchanged basic `downscale_flddph.F90` output exactly over the shared cells and mask. Turning Permanent Water OFF changed 3,331 valid pixels in this sample; the ON output applies the 0.1 m minimum, while OFF leaves the underlying calculated values (including values below 0.1 m) unchanged. These are compatibility checks for this one Mekong map/date/extent, not global validation.
