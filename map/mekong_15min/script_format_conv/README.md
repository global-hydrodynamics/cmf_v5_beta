# Mekong map format conversion

This map-local copy uses the shared templates and converters documented in [`map/tools/script_format_conv/`](../../tools/script_format_conv/README.md). `s01`/`s02` convert registered binaries in the Mekong map root; `s03` converts registered high-resolution tiles from `1min/`.

Run the scripts with this map-local directory as the current directory. The parent map is detected automatically; no map name or `MAP_DIR` edit is needed:

```sh
cd map/mekong_15min/script_format_conv
./s01-list_binary.sh
```

Review `bin2nc_list.txt` in this directory and comment out files that should not be converted. Then, without changing directories, convert the selected files:

```sh
./s02-convert_netcdf.sh
```

The candidate list is created in the current directory and follows numeric `category_id` and registry row order. It lists supported, registered `.bin` files directly in the map root once each. The editable list is preserved unless regenerated interactively. The conversion script replaces selected NetCDF outputs by default; pass `--no-overwrite` to keep existing files.

The shared template README documents supported raster layouts, warnings, output verification, and configuration for other maps.

## High-resolution tile conversion

Run the map-local `s03` to convert the selected registered `1min/` tile binaries. Its `VARS="all"` reads all high-resolution products from the canonical CSV,
currently `catmxy catmz100 catmzz downxy elevtn flddif flwdir grdare hand rivwth
uparea visual`. Present Binary tiles convert; absent products are reported and
skipped. Preflight lists all selected inputs and existing/new output counts.
Selected outputs are replaced by default; pass `--no-overwrite` to preserve existing files.

```sh
./s03-convert_highres_netcdf.sh
```

Binary inputs are read from `binary/1min/`. Outputs go to `1min/`, one NetCDF file per area and source binary (for example, `1min.catmxy.nc`); `1min/location.txt` is copied there as geometry metadata. Multi-record files contain all registered records as separate variables. The default compression level is 3 with lossless zlib/shuffle, and `JOBS=8` sets the maximum number of parallel Python workers. Edit `COMPRESSION_LEVEL` (0–9; 0 disables deflate) or `JOBS` at the top of the script. Existing NetCDF files are replaced by default; use `./s03-convert_highres_netcdf.sh --no-overwrite` to preserve them. `--map-dir PATH` explicitly selects the target map. See the shared guide for configuration and limitations.

## Legacy consolidated NetCDF files

To create the older two-container input format, run the independent `t01` script:

```sh
./t01-legacy_netcdf_map.sh
```

It creates the legacy consolidated containers `netcdf/rivclim.nc` (`nextx`, `nexty`, `lon`, `lat`, `ctmare`, `elevtn`, `nxtdst`, `rivlen`, and all `fldhgt` layers) and the legacy consolidated container `netcdf/rivpar.nc` (`rivwth`, `rivhgt`, `rivman`). These files are for the explicit `LMAPCDF=.TRUE.` compatibility route; ordinary individual NetCDF map rasters remain at the map root. Defaults select `nextxy_noedge.nc` and `rivwth_merit.nc`; change the `NEXTXY` or `RIVWTH` setting in the script to choose the alternative individual map. Existing outputs are replaced by default; pass `--no-overwrite` to preserve them.

Use these containers with `LMAPCDF=.TRUE.` and `CRIVCLINC`/`CRIVPARNC` pointing to the generated files. This is the legacy consolidated reader; ordinary individual `.bin`/`.nc` inputs use `LMAPCDF=.FALSE.` instead. If bifurcation is used, also set `LPTHOUT=.TRUE.` in `&NRUNVER` and retain the `CPTHOUT` path in `&NMAP`. The shared README lists optional legacy variables and their controlling settings: `LGDWDLY` (`gdwdly`), `LSLOPEMOUTH` (`elevslope`), `LSLPMIX` (`mask_slope`), `LMEANSL` (separate `CMEANSLNC`), and MPI region input (`CMPIREGNC`). The generator does not fabricate missing data. Its read-back validation is data-level only; a model run through the legacy path is a separate follow-up.

## Target selection and explicit overrides

s01–s03 use the parent of the current `script_format_conv/` directory by default.
`SCRIPT_DIR` locates the development repository's shared Python tools and
variable registry, independently of the target map. `bin2nc_list.txt` stays in
the caller's current directory for both s01 and s02.

Use `--map-dir PATH` to override the target, including an external map under
`cmf_v5_package_data/map/`; relative paths are relative to the caller. For
example, `./s02-convert_netcdf.sh --map-dir /path/to/map --force` reads the list
in the current directory and writes into that explicit map. Keep the same
working directory and target between s01 and s02. Invocation from another
working directory requires `--map-dir` unless that directory itself is a valid
map-local `script_format_conv/`. The shared template directory is not an implicit
map target. See the [shared guide](../../tools/script_format_conv/README.md#explicit-target-including-external-package-maps)
for a complete external-map example. This rule applies to s01–s03 only;
legacy t* helper settings are unchanged.

Before `s02` converts anything, it validates every selected input and reports
selected-input, existing-output and new-output counts. Existing selected outputs
are replaced by default; pass `--no-overwrite` to preserve them. Unselected
outputs are untouched.


## Numeric COG visualization caches (`s05`)

Run `./s05-convert_netcdf_to_cog.sh` here. This copy uses `RESOLUTIONS="auto"` (resolving to `base 1min` from `1min/`)
and `VARS="all"`; absent registered products skip. Model-grid root-level `*.nc` becomes
`COG/*.tif`, while native `1min/<area>.*.nc` becomes `COG/1min/<area>.*.tif`.
These are optional numeric caches; scientific source files remain unchanged.
The shared guide documents dependencies, bands, average/nearest internal overviews,
full native byte checks, skip/force/atomic publication and unsupported formats.
Explorer COG reading is not implemented. Generated caches are not tracked or
registered in Package Additional Data by this task.

For `s03-convert_highres_netcdf.sh`, an empty `HIRES` proposes the coarsest
installed Binary directory in `1min`, `30sec`, `15sec`, `5sec`, `3sec`, `1sec`
order. The selected path is shown before `[Y/n]` confirmation (Enter = Yes).
No lists the available resolution tags and asks which one to use. Explicit
nonempty `HIRES` lists remain supported as the initial proposal. EOF stops
execution; `--no-overwrite` preserves output files and does not bypass resolution
selection. The algorithms are unchanged.

## Binary restoration resolution selection (s04)

With `HIRES=""`, s04 searches `1min/`, `30sec/`, `15sec/`,
`5sec/`, `3sec/`, `1sec/` in coarsest-first order. It shows the
selected NetCDF resolution and asks `[Y/n]`; Enter means Yes. No lists the
available tags (for example, `1min` or `15sec`) and asks which one to restore.
Only NetCDF source directories are candidates, regardless of existing Binary
directories. A Japan map with only `15sec/` therefore selects `15sec`.
An explicit nonempty `HIRES` list remains the initial proposal. No available
source, or EOF at confirmation, stops before conversion. `--no-overwrite`
preserves existing Binary files; it does not bypass resolution confirmation.
Existing `location.txt` handling is unchanged.

## Sample variants (`s90`)

`./s90-sample_netCDF_conversion.sh` uses a byte-identical copy of the
[shared template](../../tools/script_format_conv/s90-sample_netCDF_conversion.sh).
Run here, or pass `--map-dir PATH` explicitly. The top-level `VARIANTS` settings
map `subbsn-sample.bin:subbsn.bin` and `subcol-sample.bin:subcol.bin` to
`../subbsn-sample.nc` (`subbsn`) and `../subcol-sample.nc` (`subcol`).
The CSV defines standard variables; Shell manages concrete experimental filenames.
These variants no longer appear in the standard conversion list or CTL discovery.
Before conversion, selected/existing/new counts are shown. Existing outputs are
replaced by default; pass `--no-overwrite` to preserve them. New outputs are
converted normally; Binary inputs remain unchanged.

The original Mekong examples use 30,000 / 5,000 km² two-stage thresholds from
`s06-subbasin.sh`: Stage 1 IDs/boundaries are preserved and Stage 2 assigns only
previously unassigned network cells. Thresholds do not guarantee minimum segment
area. Zero denotes unassigned network, -9999 missing/outside network; positive
subbsn values are IDs and positive subcol values are display categories.
See the [variant contract and future inpmat design](../../tools/script_format_conv/README.md#variant-binary-conversion-s90)
for multi-record inputs, partial selection, errors and atomic file publication.


## Standard MPI regions through s01/s02

The existing `mpireg-4.bin`, `mpireg-8.bin` and `mpireg-16.bin` are standard
MPI partition maps. `s01` discovers these and any other existing positive-numbered
`mpireg-N.bin` using the single CSV `mpireg.bin` definition. `s02` explicitly
references that definition and writes `mpireg-N.nc`, variable `mpireg`.
Run the usual list/review/convert sequence above; s02 replaces selected outputs
by default and accepts `--no-overwrite`. No MPI entry is added to s90. See the [standard MPI-region
contract and provenance](../../tools/script_format_conv/README.md#standard-numbered-mpi-region-maps).

## Default high-resolution Binary restoration

By default, `s04-restore_highres_binary.sh` restores all registered high-resolution
variables available in the selected NetCDF map (`VARS="all"`). Missing optional
NetCDF products are skipped. Existing Binary files are replaced by default;
pass `--no-overwrite` to preserve them. Set `VARS` to explicit registered stems to restore a subset; an
explicitly requested missing input remains an error.
