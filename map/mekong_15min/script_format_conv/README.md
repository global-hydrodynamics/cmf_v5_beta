# Mekong Map Format Conversion

These map-local wrappers use the shared programs in `map/tools/code/` and the
repository registry. They read map data from `map/mekong_15min/` and place
optional Binary and COG products in `binary/` and `COG/` respectively. Standard
NetCDF maps remain at the map root; high-resolution NetCDF maps remain in
`1min/`. No `netcdf/` directory is used.

## Commands

Run from this directory. Conversion outputs overwrite existing outputs by
default, while inputs and unrelated files are preserved.

```sh
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

The INPMAT wrappers default to `ROFFTAG="test-1deg"`. Edit that setting near
the top of each wrapper when selecting a different `inpmat_<ROFFTAG>.nc` and
matching `diminfo_<ROFFTAG>.txt`. The Binary descriptor under `binary/` is
paired with the `.bin` filename; the source descriptor at the map root remains
paired with `.nc`.

The list files are written beside these scripts and may be edited before
conversion. `s09-write_ctl.sh` writes registered CTLs beside Binary products
and copies required geometry/text metadata. High-resolution operations use
`1min/location.txt` and store outputs under `binary/1min/` or `1min/`.

`s08` and `s18` convert the `subbsn-sample` and `subcol-sample` products created
by `script_params/s05-subbasin.sh`. For the complete workflow and supported
outputs, see [`map/tools/script_format_conv/README.md`](../../tools/script_format_conv/README.md).

`t01-legacy_netcdf_map.sh` runs from the target map's `script_format_conv/`.
Its default `MAP_DIR="../"` selects the parent map, `NEXTXY="nextxy.nc"`
includes regional-boundary connections, and `RIVWTH="rivwth_merit.nc"`
selects MERIT width (`rivwth.nc` is the empirical-width alternative).
It writes `rivclim.nc` and `rivpar.nc` in the selected map directory;
the existing `--force` behavior is retained.

## High-resolution selection

s03/s13 prompt for one or more source tags when `HIRES=""`: Enter chooses the
coarsest, `all` selects all, and e.g. `1min 3sec` selects both. Confirm once
with Enter/y, or cancel with n. Edit `HIRES="15sec 3sec"` for fixed tags;
non-interactive runs require explicit tags and do not prompt. `JOBS=8` retains
parallel processing and `--no-overwrite` is forwarded to Python.

s03 reads `../<tag>/*.nc` plus location.txt and writes `../binary/<tag>/`.
s13 reads `../binary/<tag>/*.bin`, or legacy `../<tag>/*.bin` when that Binary
directory is absent, and writes `../<tag>/*.nc`. Existing standard Binary
directories take precedence; Python validates metadata. External maps use the
same copied s13 workflow via `CMF_V50_ROOT`; the old t03 wrapper is retired.
See the [shared selection guide](../../tools/script_format_conv/README.md#high-resolution-selection-s03-and-s13).
