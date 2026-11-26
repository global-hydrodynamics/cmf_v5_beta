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

`t01-legacy_netcdf_map.sh` and `t03-convert_external_highres.sh` remain separate
legacy/external workflows; they are not replacements for the numbered map
conversion sequence. `s90-sample_netCDF_conversion.sh` remains as a deprecated
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
