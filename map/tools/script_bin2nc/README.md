# Binary-to-NetCDF map conversion template

This shared template converts registered base-resolution and high-resolution Binary map rasters into individual NetCDF files. Copy the scripts into a map-local `script_bin2nc/` directory and run there. No map name or `MAP_DIR` setting needs editing. The Mekong sample contains a ready-to-use copy at [`map/mekong_15min/script_bin2nc/`](../../mekong_15min/script_bin2nc/).

The scripts reuse [`convert_map_binary_to_netcdf.py`](../code/convert_map_binary_to_netcdf.py), [`convert_highres_binary_to_netcdf.py`](../code/convert_highres_binary_to_netcdf.py), and the authoritative [`variable_table/map_variables.csv`](../../../variable_table/map_variables.csv) registry. `s01`/`s02` handle binaries directly in the map root; `s03` handles registered high-resolution tile binaries.

## Select files and convert

1. Copy the templates to the target map. The parent of the current `script_bin2nc/` directory becomes the target automatically:

   ```sh
   mkdir -p map/your_map/script_bin2nc
   cp map/tools/script_bin2nc/s01-list_binary.sh map/your_map/script_bin2nc/
   cp map/tools/script_bin2nc/s02-convert_netcdf.sh map/your_map/script_bin2nc/
   cp map/tools/script_bin2nc/s03-convert_highres_netcdf.sh map/your_map/script_bin2nc/
   ```

2. Change to the map-local script directory, then generate the candidate list. The list is written to the current directory as `bin2nc_list.txt`:

   ```sh
   cd map/your_map/script_bin2nc
   ./s01-list_binary.sh
   ```

   The same scripts work in any map-local `script_bin2nc/`, including Mekong and global maps. Candidates are ordered by numeric `category_id` and then registry row order. A file listed in multiple categories appears once under its first category. Only registered files directly in the map root and supported by the converter are listed. Unregistered binaries and registered but unsupported layouts are reported as warnings. The current `NX,NY,INPN` runoff input matrices are not handled as map rasters and are omitted. If a list already exists in the current directory, `s01` asks before replacing it; non-interactive use preserves it.

3. Review `bin2nc_list.txt` and comment out every file that should not be converted by placing `#` at the beginning of its line. The generated list starts with all supported candidates selected.

4. Convert the remaining entries in list order:

   ```sh
   ./s02-convert_netcdf.sh
   ```

   Files are written to `<map>/netcdf/<binary-stem>.nc`. For example, `nextxy.bin` becomes `nextxy.nc` with `nextx` and `nexty`; `fldhgt.bin` retains all registered floodplain layers. The converter checks registry metadata, map dimensions, record sizes, and reads each written variable/layer back for exact value comparison.

5. Review the conversion log and the NetCDF files in `<map>/netcdf/`. Existing outputs are skipped by default in non-interactive use. In a terminal, a preflight summary shows selected, existing and new output counts.
   `Overwrite all … existing selected outputs? [y/N]` offers one approval for the
   selected list. Answer `y`/`Y` to overwrite all selected existing outputs without
   further prompts. Answer `n`/Enter to confirm each existing file individually;
   Enter at an individual prompt skips that file. Pass `--force` to overwrite selected outputs without prompts:

   ```sh
   ./s02-convert_netcdf.sh --force
   ```

Run both scripts from the same map-local `script_bin2nc/` current directory so `s02` reads the list created by `s01`. The target map comes from the current directory; only the shared converters and registry are resolved from `SCRIPT_DIR` in the development repository. They only inspect `.bin` files directly under `MAP_DIR`; high-resolution subdirectories are never searched.

## Explicit target, including external package maps

Normal use is argument-free from the map-local directory:

```sh
cd map/glb_15min/script_bin2nc
./s01-list_binary.sh
# Review bin2nc_list.txt, then:
./s02-convert_netcdf.sh
./s03-convert_highres_netcdf.sh
```

All three scripts use **Current Directory First, Explicit Override**. Without
`--map-dir`, the physical current directory must be named `script_bin2nc` and
its parent must contain `params.txt`. Calling a script by path does not change
this rule. The shared `map/tools/script_bin2nc/` directory is not a map and is
rejected as an implicit target.

To process an external map without copying scripts outside the repository,
use the repository's shared scripts with an explicit target. For example, from
the repository root (replace `/path/to/work` with your workspace):

```sh
./map/tools/script_bin2nc/s01-list_binary.sh --map-dir /path/to/work/cmf_v5_package_data/map/glb_15min
# Review ./bin2nc_list.txt; keep the same working directory for s02.
./map/tools/script_bin2nc/s02-convert_netcdf.sh --map-dir /path/to/work/cmf_v5_package_data/map/glb_15min
./map/tools/script_bin2nc/s03-convert_highres_netcdf.sh --map-dir /path/to/work/cmf_v5_package_data/map/glb_15min
```

Relative `--map-dir` paths are relative to the caller's current directory;
paths containing spaces must be quoted. `s01` always writes `bin2nc_list.txt`
in that current directory, and `s02` reads the same file there, regardless of
`--map-dir`. Review/regenerate the list when changing targets. NetCDF outputs
are written under the selected map, including an external map; this is an
explicit operation that changes that external map's generated outputs.
Converters and `variable_table/map_variables.csv` always come from the development
repository. `--force` remains available on s02 and s03, in either option order.
Keep `HIRES`, `VARS`, `COMPRESSION_LEVEL` and `JOBS` at the top of s03 for
map-specific choices. Legacy `t*` helpers have their own settings and are not
covered by this s01–s03 target-selection rule.

## Build legacy consolidated NetCDF inputs

The individual files written by `s02` are used with `LMAPCDF=.FALSE.`. A separate helper can assemble the historical consolidated containers used with `LMAPCDF=.TRUE.`; the two formats follow different model-reader paths.

The `t01-legacy_netcdf_map.sh` script creates `netcdf/rivclim.nc` with `nextx`, `nexty`, `lon`, `lat`, `ctmare`, `elevtn`, `nxtdst`, `rivlen`, and all `fldhgt` layers. It creates `netcdf/rivpar.nc` with `rivwth`, `rivhgt`, and `rivman`. The defaults match the Mekong simulation examples: `nextxy_noedge.nc` and `rivwth_merit.nc`. Edit `NEXTXY` and `RIVWTH` near the top to choose `nextxy.nc` or `rivwth.nc` instead.

Run the map-local script independently of `s01` and `s02`:

```sh
cd map/mekong_15min/script_bin2nc
./t01-legacy_netcdf_map.sh
```

Existing consolidated outputs are kept in non-interactive use. In a terminal, answer `y` to replace them; Enter or `N` keeps them. Pass `--force` for explicit overwrite. The Python program stages both outputs, reads them back, checks variable values, then replaces the targets.

The current legacy reader additionally uses `gdwdly` from `rivpar.nc` when `LGDWDLY` is enabled (the reader sets it to zero if absent), `elevslope` for `LSLOPEMOUTH`, and `mask_slope` for `LSLPMIX`; the latter two must exist in `rivpar.nc` when their options are enabled. `LMEANSL` reads `meansl` from the separately configured `CMEANSLNC`, and MPI legacy mode reads `mpireg` from `CMPIREGNC`. This generator does not synthesize these optional variables. The basic Mekong containers omit them; do not enable the corresponding option unless its required input is supplied.

Example model settings for the consolidated path:

```fortran
&NMAP
LMAPCDF   = .TRUE.
CRIVCLINC = ".../netcdf/rivclim.nc"
CRIVPARNC = ".../netcdf/rivpar.nc"
CPTHOUT   = ".../bifprm.txt"
/
```

This is only the Map namelist fragment. If bifurcation is used, enable `LPTHOUT=.TRUE.` in `&NRUNVER`; the model also requires its normal dimension, time, and other run settings.

The NetCDF C library and Python standard library are sufficient. Validation here checks source/output variable values and layout; it does not replace a model run. Execution through the legacy consolidated reader remains a separate validation step.

## Convert high-resolution tiles (`s03`)

Copy `s03-convert_highres_netcdf.sh` to the map-local `script_bin2nc/` directory, set `HIRES`, `VARS`, `COMPRESSION_LEVEL` and `JOBS` near the top, then run from that map-local directory. No `MAP_DIR` edit is needed; use `--map-dir PATH` when running elsewhere. The commented `HIRES` and `VARS` examples show the available choices; select only directories and registered file stems present in the target map. The template now selects 11 common products: `catmxy`, `catmz100`, `catmzz`,
`downxy`, `elevtn`, `flddif`, `grdare`, `hand`, `rivwth`, `uparea`, and `visual`.
The old seven-product default omitted four available products; the converter
already supports their registered types. The Mekong copy additionally selects
`flwdir` (12 products) and is configured for `1min/`. Keep `flwdir` selected only
where that Binary exists; Japan's listed 15sec data do not include it. For Japan,
set `HIRES="15sec"` and use the 11-product list. Explicit selections remain strict:
a missing selected input is an error, rather than silently skipping a product.

To complete an older seven-product conversion, update the local script settings
and run `s03` again **without `--force`**: the seven existing outputs are retained
and the missing NetCDF products are added. Integer `catmz100`, `catmzz` and
`visual` remain signed int8; `grdare` remains float32 with registered units and
missing values. No values, assignment codes or categorical classes are rescaled.

For the bundled Mekong example:

```sh
cd map/mekong_15min/script_bin2nc
./s03-convert_highres_netcdf.sh
```

For each selected variable, `s03` calls the shared high-resolution converter. It reads each tile's geometry from `<MAP_DIR>/<HIRES>/location.txt`, and registered variable names, signed type, record index/count, missing value, and dimensions from `variable_table/map_variables.csv`. Unregistered files are ignored; a registered tile with a missing file, inconsistent metadata, or a Binary size that does not match `location.txt` fails explicitly. A multi-record file such as `catmxy` or `downxy` is written as one NetCDF containing all registered variables in record order.

Outputs are individual tiles at `<MAP_DIR>/<HIRES>_nc/<AREA>.<VAR>.nc`; the wrapper also copies `<MAP_DIR>/<HIRES>/location.txt` to `<MAP_DIR>/<HIRES>_nc/location.txt` as geometry metadata. NetCDF variables use `(lat,lon)` dimensions, cell-center coordinates, and the binary's row/record order; data are copied in bounded chunks and checked by reading each chunk back byte-for-byte. NetCDF4 uses lossless zlib/deflate compression with shuffle and a 256-by-256 maximum chunk shape. `COMPRESSION_LEVEL` defaults to 3; set it to 0–9, where 0 disables deflate. No scaling, offset, precision reduction, or quantization is used. `JOBS` defaults to 8 and controls the maximum number of Python worker processes; use `JOBS=1` for sequential conversion. Python schedules each registered variable/tile pair once, and the shell wrappers do not start background jobs. Existing NetCDF outputs are skipped by default, so changing the level does not recompress files already present; run with `--force` to rebuild them. Forced conversion stages a complete replacement before atomically replacing the previous output, preserving it if conversion fails. The input Binary and source `location.txt` are read-only. A successful conversion verifies stored values and file layout, not scientific correctness or model-reader compatibility.

Focused tests target CaMa-Flood's Binary-to-NetCDF contract: types, records, coordinates, chunk/task assignment, parallel error reporting, and the requested compression settings. They do not re-test the internal lossless algorithms provided by zlib, HDF5, or NetCDF. Broader map-package and model-reader integration is a separate pre-merge check when required by the change and available data.

The NetCDF C library must be installed and discoverable (typically through `nc-config`); Python uses only its standard library.

## Convert high-resolution tiles in an external package (`t03`)

Use `t03-convert_external_highres.sh` when the source maps live outside this v5 repository. Set `MAP_ROOT`, `MAPS`, `HIRES`, `VARS`, `COMPRESSION_LEVEL`, and `JOBS` at the top of the script. It resolves the shared converter and `variable_table/map_variables.csv` relative to its own location, warns and skips missing map/resolution directories, and stops on conversion errors. It copies each selected `location.txt` to `<MAP_DIR>/<HIRES>_nc/`; existing NetCDF outputs are skipped unless the script is run with `--force`. As with `s03`, changing the compression level does not alter existing files; use `--force` to rebuild them, with the old output preserved if conversion fails. `--force` is the only shell command-line option; configure parallelism with `JOBS`, not a shell argument.

```sh
map/tools/script_bin2nc/t03-convert_external_highres.sh
map/tools/script_bin2nc/t03-convert_external_highres.sh --force
```

The default settings point to the maintainer's v400 data package. Edit `MAP_ROOT` before using the script on another workstation. It writes converted files alongside the external source maps and does not copy map data into this repository.

## Supported formats and dependencies

The workflow supports registered `float32` or `int32` rasters with dimensions `NX,NY` or `NX,NY,NLFP`, including multi-variable direct-access files such as `nextxy.bin` and layered files such as `fldhgt.bin`. Data type, record order, dimensions, missing values, and variable metadata come from the registry and `params.txt`; the Binary inputs are not modified.

Python uses only the standard library. Conversion also requires the NetCDF C shared library to be installed and discoverable, typically through `nc-config`. This workflow validates conversion and stored values; compatibility with model execution is a separate validation step.

The base-map and consolidated-map NetCDF writers use lossless NetCDF-4 deflate level 3 with shuffle. The high-resolution converter is configurable and defaults to level 3. Existing outputs are not recompressed automatically.

## Restore high-resolution Binary working files (`s04`)

**Distribution format: compressed NetCDF**

**Legacy-compatible working format: Binary generated on demand**

High-resolution `<HIRES>_nc/` tiles and their `location.txt` are the authoritative
package inputs. Restore Binary only when a legacy tool requires it. Do not ship
both the compressed NetCDF and restored Binary copies in the distribution
package. This policy concerns high-resolution tiles, not base-model map formats.
The existing [variable registry](../../../variable_table/map_variables.csv)
continues to define storage types, variable names and record order; no parallel
data definition is introduced and workflow-status values are unchanged.

Copy `s04-restore_highres_binary.sh` beside s01–s03 in the target map's
`script_bin2nc/` (already installed in the local global map), then:

```sh
cd map/glb_15min/script_bin2nc
./s04-restore_highres_binary.sh
```

Edit only `HIRES`, `VARS` and `JOBS` near the top. The same current-directory
and `--map-dir PATH` rules as s01–s03 apply. Existing Binary files are skipped;
use `--force` to replace selected files. The wrapper invokes
[`convert_highres_netcdf_to_binary.py`](../code/convert_highres_netcdf_to_binary.py),
which reuses the forward converter's location/registry parsers and NetCDF C
library. No additional Python library is required. Its standalone CLI supports
explicit tile selection:

```sh
python3 map/tools/code/convert_highres_netcdf_to_binary.py \
  --map-dir /path/to/map --hires 1min \
  --variables "catmxy downxy elevtn uparea hand flddif rivwth" --jobs 8
# For a limited operation, add --areas "<carea from location.txt>".
```

Inputs are `<HIRES>_nc/<AREA>.<VAR>.nc`; outputs are
`<HIRES>/<AREA>.<VAR>.bin`. Other resolutions such as `15sec` and `3sec` use
the same registered schema. All selected NetCDF inputs are preflighted against
`<HIRES>_nc/location.txt`: coordinate centers/directions, named dimensions,
variable names, signed storage type and record order must match. Unregistered
extra variables and packing/unsigned/NetCDF quantization attributes are rejected.
Missing values and `_FillValue` remain raw stored bit patterns: no masks,
replacement, scaling, interpolation or quantization are applied. File grouping
and record ordering follow the registry, including both catmxy/downxy records.

The restored layout is little-endian, longitude fastest within each
north-to-south row, followed by the next complete registered record. Reads use
bounded 256 × 256 cell blocks. Each file is staged privately, checked for the
expected byte size and atomically published; failed files do not replace an
existing complete output. `--jobs 1` is sequential; larger values use independent
worker processes per tile/file. Progress and errors identify the input file.
Completed files may remain after another task fails or execution is interrupted;
there is no whole-directory rollback. A skip does not verify an existing Binary.

After successful selected-file restoration, missing `<HIRES>/location.txt` is
copied atomically from the NetCDF directory. An existing geometrically equivalent
file is preserved verbatim. A conflicting geometry file causes an error even
with `--force`; review it separately rather than changing the interpretation of
other Binary files silently. Subset restoration retains the complete source
location table and does not fabricate unselected tiles.

### Exact reproducibility and checks

The goal is **byte-for-byte restoration**, not approximate numerical agreement.
Compare reference and restored files with SHA-256, for example
`shasum -a 256 reference.bin restored.bin`; unequal hashes are a failure.
The focused offline tests are:

```sh
python3 -B -m unittest map.tools.tests.test_highres_nc2bin -v
```

Synthetic int8/int16/int32/float32 tiles, multiple records and a chunk-edge
crossing matched their original SHA-256 after Binary→NetCDF→Binary. Sequential
and parallel restoration, skip/force, metadata conflicts, invalid types/geometry
and mid-chunk failure cleanup were checked. Signed zero, infinities and selected
quiet/signaling NaN payloads also matched in the local library/platform tests.
This is not a universal NaN-payload guarantee: a different upstream writer,
library or previous lossy/NaN-normalizing transformation may already have changed
the original bits. Those bits cannot be recovered from the NetCDF alone; retain
reference hashes at package construction and check them after restoration.
Never accept a hash mismatch merely because values compare numerically close.

The current global `1min_nc/` has one 21600 × 10800 area, not a collection of
small geographic tiles. Validation therefore used only two 17 × 13 cell windows
from its catmxy/elevtn files in a temporary map; all four restored window files
matched the corresponding original Binary bytes. No full global file or complete
map was restored, and original global data were not changed.

Before `s02` converts anything, it validates every selected input and reports
selected-input, existing-output and new-output counts. If existing outputs are
present in a terminal, `Overwrite all … existing selected outputs? [y/N]` asks
once: `y`/`Y` overwrites all selected outputs without further prompts; `n`/Enter
uses individual overwrite prompts. At an individual prompt, `y`/`Y` overwrites
only that file and `n`/Enter preserves it. Unselected outputs are untouched.
Explicit `--force` skips prompts. Noninteractive use without `--force` still
preserves existing outputs. No bulk prompt appears when all outputs are new.
