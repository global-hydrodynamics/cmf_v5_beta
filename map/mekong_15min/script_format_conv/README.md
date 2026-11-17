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

The candidate list is created in the current directory and follows numeric `category_id` and registry row order. It lists supported, registered `.bin` files directly in the map root once each. Existing lists are not replaced without confirmation; non-interactive use preserves them. The conversion script prompts before replacing each existing NetCDF, skips it in non-interactive mode, and accepts `--force` for an explicit non-interactive overwrite.

The shared template README documents supported raster layouts, warnings, output verification, and configuration for other maps.

## High-resolution tile conversion

Run the map-local `s03` to convert the selected registered `1min/` tile binaries. Its `VARS="all"` reads all high-resolution products from the canonical CSV,
currently `catmxy catmz100 catmzz downxy elevtn flddif flwdir grdare hand rivwth
uparea visual`. Present Binary tiles convert; absent products are reported and
skipped. Preflight lists all selected inputs and existing/new output counts before
one **Overwrite all** prompt. Yes authorizes all selected existing outputs; No or
Enter uses individual confirmations. Noninteractive use preserves existing outputs.

```sh
./s03-convert_highres_netcdf.sh
```

Outputs go to `1min_nc/`, one NetCDF file per area and source binary (for example, `1min.catmxy.nc`); `1min/location.txt` is copied there as geometry metadata. Multi-record files contain all registered records as separate variables. The default compression level is 3 with lossless zlib/shuffle, and `JOBS=8` sets the maximum number of parallel Python workers. Edit `COMPRESSION_LEVEL` (0–9; 0 disables deflate) or `JOBS` at the top of the script. Existing NetCDF files are preserved without overwrite approval; use `./s03-convert_highres_netcdf.sh --force` to rebuild them. Forced conversion preserves the old file unless the replacement completes successfully. `--map-dir PATH` explicitly selects the target map; `--force` allows replacement of existing NetCDF outputs. See the shared guide for configuration and limitations.

## Legacy consolidated NetCDF files

To create the older two-container input format, run the independent `t01` script:

```sh
./t01-legacy_netcdf_map.sh
```

It creates `netcdf/rivclim.nc` (`nextx`, `nexty`, `lon`, `lat`, `ctmare`, `elevtn`, `nxtdst`, `rivlen`, and all `fldhgt` layers) and `netcdf/rivpar.nc` (`rivwth`, `rivhgt`, `rivman`). Defaults select `nextxy_noedge.nc` and `rivwth_merit.nc`; change the `NEXTXY` or `RIVWTH` setting in the script to choose the alternative individual map. Existing outputs are protected by default; answer `y` to overwrite interactively or pass `--force`. Non-interactive runs skip existing outputs.

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
selected-input, existing-output and new-output counts. If existing outputs are
present in a terminal, `Overwrite all … existing selected outputs? [y/N]` asks
once: `y`/`Y` overwrites all selected outputs without further prompts; `n`/Enter
uses individual overwrite prompts. At an individual prompt, `y`/`Y` overwrites
only that file and `n`/Enter preserves it. Unselected outputs are untouched.
Explicit `--force` skips prompts. Noninteractive use without `--force` still
preserves existing outputs. No bulk prompt appears when all outputs are new.


## Numeric COG visualization caches (`s05`)

Run `./s05-convert_netcdf_to_cog.sh` here. This copy uses `RESOLUTIONS="auto"` (resolving to `base 1min` from `1min_nc/`)
and `VARS="all"`; absent registered products skip. Model-grid `netcdf/*.nc` becomes
`COG/*.tif`, while native `1min_nc/<area>.*.nc` becomes `COG/1min/<area>.*.tif`.
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
execution; `--force` controls output overwriting and does not bypass resolution
confirmation. The subsequent overwrite confirmation and conversion algorithms
are unchanged.

## Binary restoration resolution selection (s04)

With `HIRES=""`, s04 searches `1min_nc/`, `30sec_nc/`, `15sec_nc/`,
`5sec_nc/`, `3sec_nc/`, `1sec_nc/` in coarsest-first order. It shows the
selected NetCDF resolution and asks `[Y/n]`; Enter means Yes. No lists the
available tags (for example, `1min` or `15sec`) and asks which one to restore.
Only NetCDF source directories are candidates, regardless of existing Binary
directories. A Japan map with only `15sec_nc/` therefore selects `15sec`.
An explicit nonempty `HIRES` list remains the initial proposal. No available
source, or EOF at confirmation, stops before conversion. `--force` still only
controls overwriting; it does not bypass resolution confirmation. Existing
Binary and `location.txt` handling is unchanged.
