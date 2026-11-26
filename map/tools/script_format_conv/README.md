# Map Format Conversion Workflows

These map-local Shell workflows implement the NetCDF-first map layout. Copy the
required wrappers from this directory to a map's `script_format_conv/` folder,
then run them from that directory. The Shell and Python programs keep it as
CWD; map-root products use `../` paths, and list files remain local to
`script_format_conv/`. The shared converters and
`variable_table/map_variables.csv` remain in the repository; map products stay
with the target map.

## Directory layout

```text
map/<MAPNAME>/
  *.nc                         # standard NetCDF maps
  inpmat_<ROFFTAG>.nc
  diminfo_<ROFFTAG>.txt        # paired text metadata
  params.txt
  <resolution>/*.nc            # high-resolution products and location.txt
  binary/*.bin, *.ctl          # optional legacy products
  binary/<resolution>/*.bin, *.ctl
  COG/*.tif
  COG/<resolution>/*.tif
```

NetCDF files live at the map root or in resolution directories. Binary and COG
outputs live in their own directories. The workflow does not create a redundant
`netcdf/` directory. Conversion outputs are overwritten by default; source
files and unrelated files are preserved.

The `filename` column in `variable_table/map_variables.csv` records standard
NetCDF filenames for numerical map products. The conversion tools derive the
optional Binary compatibility name by changing `.nc` to `.bin`; record order,
types, dimensions, and special values remain governed by the same registry
metadata. Text descriptors such as `diminfo_<ROFFTAG>.txt` retain their actual
names. Input matrices use the category-23 generic name
`inpmat_<ROFFTAG>.nc`, which also covers the existing `test-1deg` pair, with
the corresponding Binary form under `binary/inpmat_<ROFFTAG>.bin`.

## Workflow scripts

| Script | Operation |
| --- | --- |
| `s01-list_nc.sh` | List registered NetCDF products for Binary export |
| `s02-nc2bin.sh` | Standard map NetCDF → `binary/*.bin` |
| `s03-nc2bin_highres.sh` | High-resolution NetCDF → `binary/<resolution>/*.bin` |
| `s04-nc2bin_inpmat.sh` | `inpmat_<ROFFTAG>.nc` → `binary/inpmat_<ROFFTAG>.bin` |
| `s08-sample_nc2bin.sh` | s05 sample NetCDF maps → `binary/*-sample.bin` |
| `s09-write_ctl.sh` | Generate registered CTLs beside Binary files |
| `s11-list_bin.sh` | List registered Binary products for NetCDF migration |
| `s12-bin2nc.sh` | Standard `binary/*.bin` → map-root NetCDF |
| `s13-bin2nc_highres.sh` | High-resolution Binary → resolution-directory NetCDF |
| `s14-bin2nc_inpmat.sh` | Binary INPMAT → `inpmat_<ROFFTAG>.nc` |
| `s18-sample_bin2nc.sh` | `binary/*-sample.bin` → s05 sample NetCDF maps |
| `s21-nc2cog.sh` | NetCDF → `COG/` GeoTIFFs |

Numbering groups reflect direction: `s0X` covers NetCDF-based operations and
Binary export, `s1X` covers Binary-to-NetCDF migration, and `s2X` covers
NetCDF-to-COG conversion. Listing and conversion scripts use their matching
numbered list file in the current `script_format_conv/` directory. Wrappers use
the shared `CMF_V50_ROOT` initialization and `cmf_check_*` reporting functions;
Python program paths come from `CODE_DIR` and required inputs are visible in
the direct command calls.

## Typical use

```sh
cd map/<MAPNAME>/script_format_conv
./s01-list_nc.sh
./s02-nc2bin.sh
./s03-nc2bin_highres.sh
./s04-nc2bin_inpmat.sh
./s08-sample_nc2bin.sh
./s09-write_ctl.sh

./s11-list_bin.sh
./s12-bin2nc.sh
./s13-bin2nc_highres.sh
./s14-bin2nc_inpmat.sh
./s18-sample_bin2nc.sh

./s21-nc2cog.sh
```

`ROFFTAG` is set near the top of the INPMAT wrappers (default `test-1deg`);
edit that setting to select another pair. For the default, source metadata is
`diminfo_test-1deg.txt`. The NetCDF-side descriptor names the `.nc` product;
the Binary-side copy names the matching `.bin` product. Their dimensions and
grid metadata remain paired with that format's file.

Run the list script before its conversion script. The lists are editable and
can be used to limit conversions. Existing outputs are replaced by default;
`--no-overwrite` is available where supported by the individual wrapper.
`s09-write_ctl.sh` copies `params.txt`, high-resolution `location.txt`, and
missing diminfo files into `binary/` while retaining a format-specific INPMAT
descriptor already present there.

## High-resolution selection (s03 and s13)

Edit the settings at the top of either wrapper:

```sh
HIRES=""             # Interactive selection from available source resolutions.
VARS="all"           # Or space-separated registered file stems, e.g. catmxy hand.
JOBS=8               # Maximum parallel conversion workers.
# s13 additionally uses COMPRESSION_LEVEL=3.
```

With interactive stdin, empty `HIRES` displays available source tags in order
`1min 30sec 15sec 5sec 3sec 1sec`. Enter selects the coarsest available tag;
type `1min 3sec` for several or `all` for all available sources. Invalid tags
prompt again; duplicates are removed and the result follows resolution order.
The final selection is displayed and one `Proceed with conversion? [Y/n]`
confirmation precedes conversion. Enter/y confirms; n cancels without conversion.

For a fixed selection, edit `HIRES="15sec 3sec"`. Interactive sessions still
confirm, but do not ask for tag selection. Non-interactive runs require explicit,
nonempty tags and never prompt (e.g. run the configured script with stdin from
`/dev/null`). The empty default exits with a configuration message.

- **s03 NetCDF→Binary:** discovers registered `*.<stem>.nc` products with
  `location.txt` in `../<tag>/`; writes `../binary/<tag>/`.
- **s13 Binary→NetCDF:** discovers registered `*.<stem>.bin` products in
  `../binary/<tag>/`, or legacy `../<tag>/` if the standard Binary directory
  does not exist. `location.txt` may be in either layout; the converter prefers
  the canonical map-root copy. An existing standard Binary directory takes
  precedence even if empty: sources are not silently mixed between layouts.
  Outputs and any needed location copy go to `../<tag>/`, not `<tag>_nc/`.

Discovery inspects filenames and metadata presence only; empty directories or
unregistered-only products are not offered. Python validates tile metadata,
geometry and data. The shared `cmf_select_hires_for_conversion` helper is loaded
through `$CMF_V50_ROOT/tools/cmf_shell_functions.sh`; the preprocessing selector
`cmf_select_hires_tag` remains separate and unchanged.

Each wrapper starts Python once with the complete tag list, `VARS` and `JOBS`.
The NetCDF→Binary CLI dispatches tags to its unchanged per-resolution converter;
its worker pool remains available within each resolution. The Binary→NetCDF
converter retains its existing multi-tag planning/parallelism. Outputs overwrite
by default; `./s03-nc2bin_highres.sh --no-overwrite` and
`./s13-bin2nc_highres.sh --no-overwrite` forward that option to Python.

For external map packages, copy `script_format_conv/` into the target map and
run s13 there with `CMF_V50_ROOT` pointing to the shared repository. The former
t03 external wrapper is retired: no separate external converter or multi-map
batch orchestrator is needed. Its redundant `<tag>_nc/location.txt` side copy
is not reproduced; conversion itself already writes to `<tag>/`.

## s05 sample map conversions

`script_params/s05-subbasin.sh` creates `subbsn-sample` and `subcol-sample`.
Use `s08-sample_nc2bin.sh` to export those NetCDF products to `binary/`, and
`s18-sample_bin2nc.sh` to restore them. These scripts use the registered
`subbsn.bin` and `subcol.bin` layouts while retaining the `-sample` output
names. For the s05 NetCDF variable names (`subbsn-sample` / `subcol-sample`),
s08 supplies the corresponding source-variable alias while preserving the
registered Binary type and dimensions. s18 writes the registered `subbsn` or
`subcol` variable into the same `-sample.nc` filename, matching the existing
Binary-to-NetCDF conversion behavior. They overwrite their own outputs by
default and accept `--no-overwrite`.

`t01-legacy_netcdf_map.sh` remains a separate legacy-container workflow;
it is not a replacement for the numbered map conversion sequence. `s90-sample_netCDF_conversion.sh` remains as a deprecated
compatibility alias for s18; use the directional s08/s18 scripts for new work.

The conversion tools preserve registered dimensions, record/layer order,
storage types, missing values, coordinate orientation, and map-local paths.
For COG options and supported variables, consult the wrapper's `--help` and
`map/tools/code/convert_netcdf_to_cog.py` documentation.

`t01-legacy_netcdf_map.sh` runs from the target map's `script_format_conv/`.
Its default `MAP_DIR="../"` selects the parent map, `NEXTXY="nextxy.nc"`
includes regional-boundary connections, and `RIVWTH="rivwth_merit.nc"`
selects MERIT width (`rivwth.nc` is the empirical-width alternative).
It writes `rivclim.nc` and `rivpar.nc` in the selected map directory;
the existing `--force` behavior is retained.

## s02 overwrite setting

Choose one assignment in `s02-nc2bin.sh`'s `User settings` section:

- `NO_OVERWRITE=""`: overwrite existing Binary outputs (default).
- `NO_OVERWRITE="--no-overwrite"`: preserve existing Binary outputs.

These are alternatives, not consecutive assignments. Run `./s02-nc2bin.sh`
without Shell flags; its old `--no-overwrite`/`--help` parser is removed.
The Python CLI and other scripts' command-line options are unchanged.
