# Map Format Conversion Workflows

These map-local Shell workflows implement the NetCDF-first map layout. Copy the
required wrappers from this directory to a map's `script_format_conv/` folder,
then run them there. `--map-dir PATH` can be used when running from elsewhere.
The shared converters and `variable_table/map_variables.csv` remain in the
repository; map products stay with the target map.

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
| `s09-write_ctl.sh` | Generate registered CTLs beside Binary files |
| `s11-list_bin.sh` | List registered Binary products for NetCDF migration |
| `s12-bin2nc.sh` | Standard `binary/*.bin` → map-root NetCDF |
| `s13-bin2nc_highres.sh` | High-resolution Binary → resolution-directory NetCDF |
| `s14-bin2nc_inpmat.sh` | Binary INPMAT → `inpmat_<ROFFTAG>.nc` |
| `s21-nc2cog.sh` | NetCDF → `COG/` GeoTIFFs |

Numbering groups reflect direction: `s0X` covers NetCDF-based operations and
Binary export, `s1X` covers Binary-to-NetCDF migration, and `s2X` covers
NetCDF-to-COG conversion. Listing and conversion scripts use their matching
numbered list file in the current `script_format_conv/` directory.

## Typical use

```sh
cd map/<MAPNAME>/script_format_conv
./s01-list_nc.sh
./s02-nc2bin.sh
./s03-nc2bin_highres.sh
./s04-nc2bin_inpmat.sh
./s09-write_ctl.sh

./s11-list_bin.sh
./s12-bin2nc.sh
./s13-bin2nc_highres.sh
./s14-bin2nc_inpmat.sh

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

## Other map-local scripts

The distinct `s90-sample_netCDF_conversion.sh` remains a focused conversion
example. `t01-legacy_netcdf_map.sh` and `t03-convert_external_highres.sh` are
separate legacy/external workflows and are not replacements for the numbered
conversion sequence. Keep their scope and outputs distinct.

The conversion tools preserve registered dimensions, record/layer order,
storage types, missing values, coordinate orientation, and map-local paths.
For COG options and supported variables, consult the wrapper's `--help` and
`map/tools/code/convert_netcdf_to_cog.py` documentation.
