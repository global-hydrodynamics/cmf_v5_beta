# Map format conversion templates

These shared templates convert registered base-resolution and high-resolution map rasters between Binary and NetCDF, and generate optional numeric COG visualization caches. The standard layout keeps NetCDF at the map root or resolution directory and optional Binary under `binary/`. Copy the scripts into a map-local `script_format_conv/` directory and run there. No map name or `MAP_DIR` setting needs editing. The Mekong sample contains a ready-to-use copy at [`map/mekong_15min/script_format_conv/`](../../mekong_15min/script_format_conv/).

The scripts reuse [`convert_map_binary_to_netcdf.py`](../code/convert_map_binary_to_netcdf.py), [`convert_highres_binary_to_netcdf.py`](../code/convert_highres_binary_to_netcdf.py), and the authoritative [`variable_table/map_variables.csv`](../../../variable_table/map_variables.csv) registry. `s01`/`s02` handle Binary products under `<map>/binary/`; `s03` handles registered high-resolution tiles under `<map>/binary/<RES>/`. Existing products owned by the converter are overwritten by default; `--no-overwrite` preserves them where supported. Inputs and unrelated files are never removed. The user-editable `bin2nc_list.txt` remains an interactive selection-list output.

**Rerun policy:** maintained Python converters and their Shell wrappers replace their own output products by default. Use `--no-overwrite` where available to preserve existing files. Inputs, unselected products, and unrelated files are not removed. The editable `bin2nc_list.txt` remains a user-reviewed selection list and its creation may ask before replacing an existing list.

## Select files and convert

1. Copy the templates to the target map. The parent of the current `script_format_conv/` directory becomes the target automatically:

   ```sh
   mkdir -p map/your_map/script_format_conv
   cp map/tools/script_format_conv/s01-list_binary.sh map/your_map/script_format_conv/
   cp map/tools/script_format_conv/s02-convert_netcdf.sh map/your_map/script_format_conv/
   cp map/tools/script_format_conv/s03-convert_highres_netcdf.sh map/your_map/script_format_conv/
   ```

2. Change to the map-local script directory, then generate the candidate list. The list is written to the current directory as `bin2nc_list.txt`:

   ```sh
   cd map/your_map/script_format_conv
   ./s01-list_binary.sh
   ```

   The same scripts work in any map-local `script_format_conv/`, including Mekong and global maps. Candidates are ordered by numeric `category_id` and then registry row order. A file listed in multiple categories appears once under its first category. Only registered files directly under `<map>/binary/` and supported by the converter are listed. Unregistered binaries and registered but unsupported layouts are reported as warnings. The current `NX,NY,INPN` runoff input matrices are not handled as map rasters and are omitted. If a list already exists in the current directory, `s01` asks before replacing it; non-interactive use preserves it.

3. Review `bin2nc_list.txt` and comment out every file that should not be converted by placing `#` at the beginning of its line. The generated list starts with all supported candidates selected.

4. Convert the remaining entries in list order:

   ```sh
   ./s02-convert_netcdf.sh
   ```

   Files are written to `<map>/<binary-stem>.nc`. For example, `binary/nextxy.bin` becomes `nextxy.nc` with `nextx` and `nexty`; `binary/fldhgt.bin` becomes `fldhgt.nc` with all registered floodplain layers. The converter checks registry metadata, map dimensions, record sizes, and reads each written variable/layer back for exact value comparison.

5. Review the conversion log and NetCDF files in the map root. Selected output files are replaced by default. Use `--no-overwrite` to preserve an existing output:

   ```sh
   ./s02-convert_netcdf.sh --no-overwrite
   ```

Run both scripts from the same map-local `script_format_conv/` current directory so `s02` reads the list created by `s01`. The target map comes from the current directory; only the shared converters and registry are resolved from `SCRIPT_DIR` in the development repository. They inspect base Binary files under `<MAP_DIR>/binary/`; high-resolution subdirectories are handled by `s03`.

## Explicit target, including external package maps

Normal use is argument-free from the map-local directory:

```sh
cd map/glb_15min/script_format_conv
./s01-list_binary.sh
# Review bin2nc_list.txt, then:
./s02-convert_netcdf.sh
./s03-convert_highres_netcdf.sh
```

All three scripts use **Current Directory First, Explicit Override**. Without
`--map-dir`, the physical current directory must be named `script_format_conv` and
its parent must contain `params.txt`. Calling a script by path does not change
this rule. The shared `map/tools/script_format_conv/` directory is not a map and is
rejected as an implicit target.

To process an external map without copying scripts outside the repository,
use the repository's shared scripts with an explicit target. For example, from
the repository root (replace `/path/to/work` with your workspace):

```sh
./map/tools/script_format_conv/s01-list_binary.sh --map-dir /path/to/work/cmf_v5_package_data/map/glb_15min
# Review ./bin2nc_list.txt; keep the same working directory for s02.
./map/tools/script_format_conv/s02-convert_netcdf.sh --map-dir /path/to/work/cmf_v5_package_data/map/glb_15min
./map/tools/script_format_conv/s03-convert_highres_netcdf.sh --map-dir /path/to/work/cmf_v5_package_data/map/glb_15min
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

The `t01-legacy_netcdf_map.sh` script creates consolidated `rivclim.nc` with `nextx`, `nexty`, `lon`, `lat`, `ctmare`, `elevtn`, `nxtdst`, `rivlen`, and all `fldhgt` layers. It creates consolidated `rivpar.nc` with `rivwth`, `rivhgt`, and `rivman`. Both files are placed at the map root, separately from individual `*.nc` rasters; their reader remains selected only by `LMAPCDF=.TRUE.`. Defaults match the Mekong simulation examples: `nextxy_noedge.nc` and `rivwth_merit.nc`. Edit `NEXTXY` and `RIVWTH` near the top to choose `nextxy.nc` or `rivwth.nc` instead.

Run the map-local script independently of `s01` and `s02`:

```sh
cd map/mekong_15min/script_format_conv
./t01-legacy_netcdf_map.sh
```

Existing consolidated outputs are replaced by default. Pass `--no-overwrite` to preserve them. The Python program stages both outputs, reads them back, checks variable values, then replaces the targets.

The current legacy reader additionally uses `gdwdly` from `rivpar.nc` when `LGDWDLY` is enabled (the reader sets it to zero if absent), `elevslope` for `LSLOPEMOUTH`, and `mask_slope` for `LSLPMIX`; the latter two must exist in `rivpar.nc` when their options are enabled. `LMEANSL` reads `meansl` from the separately configured `CMEANSLNC`, and MPI legacy mode reads `mpireg` from `CMPIREGNC`. This generator does not synthesize these optional variables. The basic Mekong containers omit them; do not enable the corresponding option unless its required input is supplied.

Example model settings for the consolidated path:

```fortran
&NMAP
LMAPCDF   = .TRUE.
CRIVCLINC = ".../rivclim.nc"
CRIVPARNC = ".../rivpar.nc"
CPTHOUT   = ".../bifprm.txt"
/
```

This is only the Map namelist fragment. If bifurcation is used, enable `LPTHOUT=.TRUE.` in `&NRUNVER`; the model also requires its normal dimension, time, and other run settings.

The NetCDF C library and Python standard library are sufficient. Validation here checks source/output variable values and layout; it does not replace a model run. Execution through the legacy consolidated reader remains a separate validation step.

## Convert high-resolution tiles (`s03`)

Copy `s03-convert_highres_netcdf.sh` to the map-local `script_format_conv/` directory, set `HIRES`, `VARS`, `COMPRESSION_LEVEL` and `JOBS` near the top, then run from that map-local directory. No `MAP_DIR` edit is needed; use `--map-dir PATH` when running elsewhere. The commented `HIRES` and `VARS` examples show the available choices; select existing resolution directories; absent registered Binary products skip. The standard `VARS="all"` reads every registered high-resolution Binary product
from the canonical CSV, currently these 12 stems (paired records are one file):

```text
catmxy catmz100 catmzz downxy elevtn flddif flwdir grdare hand rivwth uparea visual
```

The full list is printed before conversion. For every area in `location.txt`, an
absent Binary is listed as `SKIP missing Binary`; it is not a conversion error.
Existing files must still pass registered type/record/size validation. Unregistered
files are not converted. A subset can be selected by replacing `all` with stems;
missing registered inputs also skip in subset mode, while unregistered names fail.
Leave `HIRES` empty to propose the coarsest available Binary resolution (Japan: `15sec`, Mekong: `1min`) and confirm it at the prompt; set `HIRES` explicitly when a particular resolution or list is required.

Python preflights **all selected resolutions** before creating outputs. It
lists present/missing inputs and existing/new outputs. Existing outputs are
replaced by default; pass `--no-overwrite` to preserve existing files. Missing
Binary inputs never cause unrelated existing NetCDFs to be modified. The standard
CLI defaults to all CSV products and accepts whitespace-separated resolution tags
via `--hires`.

This replaces the older seven/eleven-product defaults. Signed int8 codes, float32
values, record planes and registered missing values/units are unchanged.

For the bundled Mekong example:

```sh
cd map/mekong_15min/script_format_conv
./s03-convert_highres_netcdf.sh
```

For each selected variable, `s03` calls the shared high-resolution converter. It reads each tile's geometry from `<MAP_DIR>/<HIRES>/location.txt`, Binary files from `<MAP_DIR>/binary/<HIRES>/`, and registered variable names, signed type, record index/count, missing value, and dimensions from `variable_table/map_variables.csv`. Unregistered files are ignored; absent registered Binary tiles skip. Present tiles with inconsistent metadata or a Binary size that does not match `location.txt` fail explicitly before conversion. A multi-record file such as `catmxy` or `downxy` is written as one NetCDF containing all registered variables in record order.

Outputs are individual tiles at `<MAP_DIR>/<HIRES>/<AREA>.<VAR>.nc`; the wrapper retains `<MAP_DIR>/<HIRES>/location.txt` as geometry metadata. NetCDF variables use `(lat,lon)` dimensions, cell-center coordinates, and the Binary row/record order; data are copied in bounded chunks and checked by reading each chunk back byte-for-byte. NetCDF4 uses lossless zlib/deflate compression with shuffle and a 256-by-256 maximum chunk shape. `COMPRESSION_LEVEL` defaults to 3; set it to 0–9, where 0 disables deflate. No scaling, offset, precision reduction, or quantization is used. `JOBS` defaults to 8 and controls the maximum number of Python worker processes; use `JOBS=1` for sequential conversion. Python schedules each registered variable/tile pair once, and the shell wrappers do not start background jobs. Existing outputs are replaced by default, after the converters stage and validate replacements. Use `--no-overwrite` to preserve outputs. Binary under `binary/<HIRES>/` and the source `location.txt` are read-only. A successful conversion verifies stored values and file layout, not scientific correctness or model-reader compatibility.

Focused tests target CaMa-Flood's Binary-to-NetCDF contract: types, records, coordinates, chunk/task assignment, parallel error reporting, and the requested compression settings. They do not re-test the internal lossless algorithms provided by zlib, HDF5, or NetCDF. Broader map-package and model-reader integration is a separate pre-merge check when required by the change and available data.

The NetCDF C library must be installed and discoverable (typically through `nc-config`); Python uses only its standard library.

## Convert high-resolution tiles in an external package (`t03`)

Use `t03-convert_external_highres.sh` when the source maps live outside this v5 repository. Set `MAP_ROOT`, `MAPS`, `HIRES`, `VARS`, `COMPRESSION_LEVEL`, and `JOBS` at the top of the script. It resolves the shared converter and `variable_table/map_variables.csv` relative to its own location, warns and skips missing map/resolution directories, and stops on conversion errors. It retains each `location.txt` at `<MAP_DIR>/<HIRES>/`; existing NetCDF outputs are replaced by default after validation. Use `--no-overwrite` to preserve them. Configure parallelism with `JOBS`, not a shell argument.

```sh
map/tools/script_format_conv/t03-convert_external_highres.sh
map/tools/script_format_conv/t03-convert_external_highres.sh --force
```

The default settings point to the maintainer's v400 data package. Edit `MAP_ROOT` before using the script on another workstation. It writes converted files alongside the external source maps and does not copy map data into this repository. Standard NetCDF output is `<MAP_DIR>/<HIRES>/`; optional Binary source products belong under `<MAP_DIR>/binary/<HIRES>/`.

## Supported formats and dependencies

The workflow supports registered `float32` or `int32` rasters with dimensions `NX,NY` or `NX,NY,NLFP`, including multi-variable direct-access files such as `nextxy.bin` and layered files such as `fldhgt.bin`. Data type, record order, dimensions, missing values, and variable metadata come from the registry and `params.txt`; the Binary inputs are not modified.

For s01–s04, Python uses only the standard library. Conversion also requires the NetCDF C shared library to be installed and discoverable, typically through `nc-config`. This workflow validates conversion and stored values; compatibility with model execution is a separate validation step.

The base-map and consolidated-map NetCDF writers use lossless NetCDF-4 deflate level 3 with shuffle. The high-resolution converter is configurable and defaults to level 3. Existing outputs are not recompressed automatically.

## Restore high-resolution Binary working files (`s04`)

**Distribution format: compressed NetCDF**

**Legacy-compatible working format: Binary generated on demand**

High-resolution `<HIRES>/` tiles and their `location.txt` are the authoritative
package inputs. Restore Binary only when a legacy tool requires it. Do not ship
both the compressed NetCDF and restored Binary copies in the distribution
package. This policy concerns high-resolution tiles, not base-model map formats.
The existing [variable registry](../../../variable_table/map_variables.csv)
continues to define storage types, variable names and record order; no parallel
data definition is introduced and workflow-status values are unchanged.

Copy `s04-restore_highres_binary.sh` beside s01–s03 in the target map's
`script_format_conv/` (already installed in the local global map), then:

```sh
cd map/glb_15min/script_format_conv
./s04-restore_highres_binary.sh
```

Adjust `VARS` and `JOBS` near the top as needed; leave `HIRES` empty for automatic selection. The same current-directory
and `--map-dir PATH` rules as s01–s03 apply. Existing Binary files are replaced by default;
use `--no-overwrite` to preserve selected files. The wrapper invokes
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

With `HIRES=""`, s04 searches `1min/`, `30sec/`, `15sec/`,
`5sec/`, `3sec/`, `1sec/` in coarsest-first order. It shows the
selected NetCDF resolution and asks `[Y/n]`; Enter means Yes. No lists the
available tags (for example, `1min` or `15sec`) and asks which one to restore.
Only NetCDF source directories are candidates, regardless of existing Binary
directories. A Japan map with only `15sec/` therefore selects `15sec`.
An explicit nonempty `HIRES` list remains the initial proposal. No available
source, or EOF at confirmation, stops before conversion. `--force` still only
controls overwriting; it does not bypass resolution confirmation. Existing
Binary and `location.txt` handling is unchanged.

Inputs are `<HIRES>/<AREA>.<VAR>.nc`; outputs are
`binary/<HIRES>/<AREA>.<VAR>.bin`. Other resolutions such as `15sec` and `3sec` use
the same registered schema. All selected NetCDF inputs are preflighted against
`<HIRES>/location.txt`: coordinate centers/directions, named dimensions,
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

The global `1min/` source has one 21600 × 10800 area, not a collection of
small geographic tiles. Validation therefore used only two 17 × 13 cell windows
from its catmxy/elevtn files in a temporary map; all four restored window files
matched the corresponding original Binary bytes. No full global file or complete
map was restored, and original global data were not changed.

Before `s02` converts anything, it validates each selected input and reports
selected-input, existing-output and new-output counts. Existing selected outputs
are replaced by default without prompts. Unselected outputs are untouched. The
Python converter stages and validates replacements before publishing them.


## Numeric NetCDF-to-COG caches (`s05`)

Binary is the legacy/model working format; compressed NetCDF is the authoritative
high-resolution distribution/input format. COG is an optional numeric visualization
cache, not a replacement for scientific inputs, new RGB image or model format.
**Explorer COG reading and automatic Overview selection are not implemented.**
Package Additional Data registration/assembly is unchanged; do not register or
import generated COGs without a separate size/usefulness review.

The maintained directories are now `script_format_conv/` (formerly
`script_bin2nc/`). Copy templates to a map-local directory. Git-untracked map
workflows are not moved automatically; review/copy them manually. Internal
Binary/NetCDF Python converter names and algorithms remain unchanged. A local
untracked script left in an old directory is not the updated maintained template.

### Dependencies and invocation

`s01`–`s04` retain their existing standard-library/NetCDF-C requirements. Only
`s05` additionally needs NumPy, netCDF4-Python and Rasterio with GDAL's COG driver
(GDAL >=3.7 for native signed Int8). Use an isolated Python environment on PATH.
One tested Python3.12 installation is:

```sh
python3 -m venv /path/to/cog-env
. /path/to/cog-env/bin/activate
python3 -m pip install 'numpy>=1.24,<2' 'netCDF4>=1.6,<1.7' 'rasterio>=1.4,<1.5'
# Optional independent structural validation:
python3 -m pip install rio-cogeo
```

Other compatible versions may work; test their native read-back and COG validation.
Source-building Rasterio requires a matching GDAL installation; a platform wheel
or a consistent conda-forge environment avoids that build requirement. The local
validated combination is Rasterio1.4.1/GDAL3.9.2, netCDF4 1.6.5, NumPy1.26.4.
There is no change to the Explorer's installed environment/dependencies.

For TE-Japan, copy the maintained template without moving its data/workflows:

```sh
mkdir -p map/TE-Japan_01min/script_format_conv
cp map/tools/script_format_conv/s05-convert_netcdf_to_cog.sh map/TE-Japan_01min/script_format_conv/
cd map/TE-Japan_01min/script_format_conv
./s05-convert_netcdf_to_cog.sh
```

The shared template and maintained Mekong copy default to `RESOLUTIONS="auto"`,
`VARS="all"`, tile edge512px (allowed128–4096, divisible by16), lossless DEFLATE,
Overview factors2/4/8/16/32 and4worker processes. Copy the template without changing
resolution settings: Python selects the model grid plus the **first existing**
high-res NetCDF directory in this coarse-to-fine order:

1. `1min/`
2. `30sec/`
3. `15sec/`

For example, both1min and15sec present selects only1min; both30sec and15sec
present selects only30sec. No map-name/source-family inference or ambiguity error
is needed. If none exists, Auto selects base only and prints that selection.
`location.txt` still defines actual tile geometry; this search only selects inputs.

MERIT Hydro-derived distributed maps normally have1min data (original3sec is not
distributed here); Japan's J-FlwDir-derived maps normally have15sec (original1sec
is not distributed here). Original-resolution data are not automatic candidates;
use explicit `--resolutions` to select them or any other supported resolution.
Missing products keep the existing skips. CLI options at the end override the
shell's settings, and the direct Python CLI has the same Auto default. For an
existing local copy with fixed `base 15sec`/`base 1min`, change only
`RESOLUTIONS="auto"` or recopy the template while preserving other custom settings.
`s03` and other conversions retain their existing explicit resolution settings.

```sh
map/tools/script_format_conv/s05-convert_netcdf_to_cog.sh \
  --map-dir /path/to/map --resolutions 'base 1min' --variables 'elevtn catmxy visual' --jobs 1
# Rebuild selected caches only after review:
map/tools/script_format_conv/s05-convert_netcdf_to_cog.sh --map-dir /path/to/map --force
```

Existing files are overwritten by default;
including noninteractive runs. Skipping does not validate an existing cache.
A forced replacement is written privately, verified fully and atomically replaced.
Failure preserves the previous cache and removes temporary files. Independent
successful files remain if another file fails; no directory-wide rollback occurs.
The command summarizes PASS/SKIP/UNSUPPORTED/FAIL. Known non-target files
`bifprm.nc` (bifurcation table), `rivclim.nc` and `rivpar.nc` (legacy consolidated
containers) are explicitly configured as reasoned SKIPs, including with --force.
They are not converted or opened and do not make the command fail. Missing
registered inputs/directories also skip. Unsupported or failed **conversion-target**
inputs still return nonzero; unknown files are not silently accepted.

### Consolidated CSV definitions and variant NetCDF names

Numbered `mpireg-N.nc` files reuse the CSV `mpireg.bin` definition and retain
numbered COG stems. The positive-integer rule is shared with Binary-to-NetCDF;
`--variables mpireg` selects the existing numbered family, while explicit stems
such as `--variables 'mpireg-4 mpireg-8'` select individual files. Invalid/zero
MPI counts gain no automatic mapping.

For a nonstandard single-variable filename (for example `subbsn-sample.nc`,
`subcol-sample.nc` or `width-experiment.nc`), COG discovery reads only NetCDF
metadata and looks for exactly one raster variable whose name matches the
canonical same-name CSV file/variable definition. It does not guess scientific
identity from a filename suffix. The CSV remains the definition of type,
dimensions and meaning; existing storage, geometry, NoData and full native-byte
checks still apply before publication. No duplicate sample rows are needed.
`--variables` accepts these resolved variant file stems as well as registered
stems. `all` includes them automatically.

Ambiguous/multivariable unknown names remain unsupported rather than guessed;
known registered pairs/layers and high-resolution products retain their existing
handling. Known table/legacy-container exclusions remain reasoned SKIPs. Missing
optional registered inputs remain SKIPs; this does not indicate a malformed CSV.

### Source/output layout and band contract

- `<stem>.nc` → `COG/<stem>.tif`: native **model grid**, never aggregated high-res pixels.
- `<HIRES>/<area>.<stem>.nc` → `COG/<HIRES>/<area>.<stem>.tif`: native high-resolution grid.
- Overviews are internal to each file; no separate pyramid directory is generated.
- Generated `COG/` trees are normally ignored by Git. The complete repository
  sample `map/mekong_15min/`, including `COG/`, is explicitly included for Git
  tracking. `package_data.csv` is unchanged.

The canonical `variable_table/map_variables.csv` controls product selection,
registered types, names, meanings and record order. `all` considers all registered
model-grid raster stems/patterns and all12 high-resolution products. Absent products
are not invented. Native raster families include core Float32 fields, layered
`fldhgt`, paired Int32 `nextxy`/`downxy`, categorical maps, and signed Int8/Int16
high-res products including `visual`, `catmz100`, `catmzz`, `flwdir`, `catmxy`,
`downxy`, plus continuous `elevtn/flddif/hand/rivwth/uparea/grdare`.

Each registered variable is assigned consecutive bands in native record order;
extra record/layer dimensions expand in their native index order. `fldhgt` layers
stay ordered, and `catmxx/catmyy` (or existing `catmx/catmy` aliases) remain paired.
Band descriptions/tags retain source variable, registry name, dtype, units,
scientific description, original1-based Binary record and extra dimension indices.
A source-file tag identifies the NetCDF. No unrelated spatial variable is silently
dropped. `nextxy_noedge.nc` may use the existing `nextx/nexty` variable names.

EPSG:4326 is explicit. Regular geographic coordinate centers are checked against
params.txt or the selected NetCDF directory's location.txt, accepting ascending
or descending axes and lat/lon or lon/lat dimension order. The GeoTIFF affine
transform is derived from source centers, preserving their pixel edges, including
minor rounding in printed metadata. Native values are only transposed/flipped,
never resampled, scaled, cast, quantized or colorized. Every full-resolution band
is read back in chunks and checked byte-for-byte, including fill patterns and
NoData mask agreement. Nonmissing special codes are preserved; no new catmxy
assignment-validity mask is imposed on continuous source fields.

### Display Overview semantics, memory and limits

Floating continuous bands use GDAL **average**, excluding the declared NoData.
Integer codes/indices use **nearest**; all paired bands choose the same source
pixel, rather than independently aggregating x/y. Layers are handled independently.
Integer-valued continuous fields, if introduced, conservatively use nearest to
avoid inventing fractional native integer codes. Overview values are display-only
representatives and must not replace native model/Inspector measurements. Mean
rivwth/uparea can make fine river features less prominent; max/mode are future work.
Small rasters omit unusable reduction factors; odd dimensions have rounded sizes
and GDAL-reported effective factors. No resampling occurs at full resolution.

NetCDF and GeoTIFF blocks are read/written one band at a time; no full native raster
is materialized. GDAL block cache is16MiB per worker, overview work chunks are2MiB and staged
overview tiles128px; NetCDF caches are bounded separately.
JOBS controls concurrent independent files, not inner compression threads. Allow
additional memory for libraries/bands and disk for a staged TIFF, internal overviews
and final COG. Choose JOBS=1 on constrained machines. Large files use BigTIFF when
needed. Compression choices are lossless DEFLATE/LZW/ZSTD/NONE only.

Both NetCDF-4 and regular NetCDF classic rasters are accepted.
Known non-target tables/containers skip as above. Unsupported conversion-target
inputs are reported explicitly: runoff input matrices with INPN/mixed dtype, unregistered spatial content,
packed/unsigned-reinterpreted/quantized NetCDF, inconsistent geometry, differing
band types or missing codes that cannot share one exact TIFF NoData. Current
registered raster storage is signed Int8/Int16/Int32/Float32; the writer also
accepts faithfully registered UInt8/16/32 and Float64. Int64/UInt64 and complex
storage are intentionally not implemented. No arbitrary conversion is attempted.
NaN payload preservation is verified for the actual library/platform; data already
changed by an upstream writer cannot be recovered by this converter.

See the [GDAL COG driver](https://gdal.org/en/stable/drivers/raster/cog.html) for
internal tiling, CreateCopy and existing-Overview semantics. Independent validation:

```sh
rio cogeo validate --strict map/your_map/COG/elevtn.tif
python3 -B -m pytest -q -p no:cacheprovider map/tools/tests/test_netcdf_to_cog.py
```

This task validates synthetic data and small read-only Japan windows only. Full
TE-Japan/all-variable COG generation, global performance, Explorer integration and
additional-data inclusion remain separate developer tasks.


### Validation in this implementation

The focused offline suite covers full raw Float32/Int8/Int16/Int32 bytes,
multivariable and layered maps, extra record dimensions, axis flips/transposes,
EPSG:4326 bounds, NoData and special float bits, average/nearest overviews,
standard rio-cogeo validation, skip/force and mid-write/verification failure safety.
It also runs the previous Binary↔NetCDF and shell-workflow regression cases.
A512MiB native artificial plane (16384×8192 Float32) converted and verified under
an externally monitored320MiB process RSS budget; observed peak162.5MiB locally.
This demonstrates bounded processing for that case, not a universal process-memory
ceiling for arbitrary band counts/libraries. JOBS multiplies per-worker costs.

Read-only TE-Japan checks extracted96×128 windows into a temporary map: model-grid
elevtn plus15sec elevtn/catmxy/visual produced four valid COGs (five bands total).
All native bytes matched, internal overviews and EPSG:4326 were verified, strict
rio-cogeo checks passed and hashes of all four original files were unchanged.
No full TE-Japan or global product was converted.

Metadata-only inspection of installed TE-Japan accepts35 model-grid plus11
high-resolution raster files; `flwdir` is absent and `bifprm.nc` is a nonraster
table excluded with a reasoned SKIP. That inspection does not generate full-size COGs.

For `s03-convert_highres_netcdf.sh`, an empty `HIRES` proposes the coarsest
installed Binary directory in `1min`, `30sec`, `15sec`, `5sec`, `3sec`, `1sec`
order. The selected path is shown before `[Y/n]` confirmation (Enter = Yes).
No lists the available resolution tags and asks which one to use. Explicit
nonempty `HIRES` lists remain supported as the initial proposal. EOF stops
execution. Existing selected outputs are replaced by default without overwrite
prompts; the resolution-selection question is separate from output handling.


## Standard numbered MPI-region maps

The CSV contains one standard `mpireg.bin` / `mpireg` definition: one Int32
`NX,NY` record, missing value -9999 (outside an assigned MPI region). Actual
`mpireg-N.bin` files are standard MPI partition products, not experimental
variants. The supplied Mekong files correspond to 4, 8 and 16 processes:

| Binary | Process count | NetCDF / variable |
| --- | ---: | --- |
| binary/mpireg-4.bin | 4 | mpireg-4.nc / mpireg |
| binary/mpireg-8.bin | 8 | mpireg-8.nc / mpireg |
| binary/mpireg-16.bin | 16 | mpireg-16.nc / mpireg |

They are generated by `param_mpi_set_region.F90` through
`script_params/s04-mpi_map_setup.sh`, and selected for runtime through
`src_main/cmf_ctrl_maps_mod.F90` CMPIREG initialization. No unnumbered Binary
alias is generated; `mpireg.bin` is the standard metadata key, not a new dataset.
Partition count does not imply grid shape or change stored IDs. Shapes come only
from `params.txt`, and values are copied exactly without reassigning MPI regions.

`s01` delegates candidate discovery to the shared Python converter. It finds only
existing map-root files matching `mpireg-<positive ASCII integer>.bin` and places
them under the standard row's category/order (24 / MPI), once per filename.
Future counts such as 32 need no extra CSV row. Leading zeros are accepted for
positive counts (`mpireg-004.bin`); zero/all-zero, negative, decimal, empty and
nonnumeric suffixes are excluded. Nested files and nonexistent counts are not
invented. This naming rule applies only to mpireg; `rivwth-4.bin` gains no automatic
interpretation. Existing literal registered files keep their normal handling.

Use the standard flow, preserving list editing. `s02` replaces selected outputs
by default; pass `--no-overwrite` to keep existing outputs:

```sh
cd map/mekong_15min/script_format_conv
./s01-list_binary.sh
# Review/comment bin2nc_list.txt, then:
./s02-convert_netcdf.sh
```

`s02` passes `--reference-binary mpireg.bin` explicitly for positive numbered MPI
files, keeping each numbered output stem. Existing selected outputs are replaced by default; explicit reference selection
continues to preserve the complete registered file definition. The Python converter also
recognizes these standard filenames directly. `--reference-binary` selects the
exact complete file definition; `--variables mpireg` selects output variables and
retains the legacy name fallback for custom input names. Both work here, but the
standard Shell path uses explicit reference selection rather than guessing rows.

`s90` remains for sample/experimental variants and has no MPI entries. The future
inpmat converter remains separate and unimplemented, as documented below.
CTL generation also resolves numbered MPI files to mpireg.bin; s99 supports
explicit variant references and Shell-owned sample/station mappings. See the
[CTL reference interface](../script_params/README.md#standard-definitions-for-ctl-variants).

## Variant Binary conversion (`s90`)

**CSV defines standard variables; Shell manages concrete experimental/derived
filenames.** A variant is an existing Binary with a standard layout under a
nonstandard filename, not a new scientific variable definition. The sample names
`subbsn-sample.bin` and `subcol-sample.bin` are therefore not registry rows and
are not candidates for `s01`/`s02` or automatic CTL generation. Other existing
sample/derived registry entries are unchanged.

Copy `s90-sample_netCDF_conversion.sh` into `<map>/script_format_conv/` and run
it there with Bash (or execute its Bash shebang). Its `VARIANTS` array contains
`"input.bin:reference.bin"` pairs; the defaults convert the two Mekong samples.
Existing selected outputs are replaced by default, without an overwrite prompt.
For example, add `"rivwth_experiment.bin:rivwth.bin"` or
`"nextxy-experiment.bin:nextxy.bin"` only when those Binary inputs exist.

```sh
cd map/mekong_15min/script_format_conv
./s90-sample_netCDF_conversion.sh
# The default run also replaces existing selected outputs.
./s90-sample_netCDF_conversion.sh
```

The target is the parent of the current map-local `script_format_conv/`, matching
s01–s03. From another working directory, or the shared template directory, supply
`--map-dir /path/to/map`; a shared template is never implicitly treated as a map.
Before conversion, s90 prints selected/existing/new output counts. Existing
selected outputs are replaced by default without prompts; unselected outputs are
untouched. Converted/skipped totals appear at completion.

Outputs retain each input stem at the map root: `<map>/subbsn-sample.nc` contains `subbsn`,
and `<map>/subcol-sample.nc` contains `subcol`. Only these two generated
Mekong NetCDF samples are explicitly approved for Git tracking in this task.

The existing converter also exposes the mapping directly:

```sh
python3 map/tools/code/convert_map_binary_to_netcdf.py \
  --map-dir map/mekong_15min \
  --input map/mekong_15min/binary/subcol-sample.bin \
  --output map/mekong_15min/subcol-sample.nc \
  --reference-binary subcol.bin
```

`--reference-binary` matches a literal registered base filename exactly; it never
falls back to `--variables` or guesses by input stem. All definition rows are
validated before output-variable selection: supported dimensions are `NX,NY`
and one-variable `NX,NY,NLFP`, storage is Int32/Float32, ordinary record indices
must cover `1..record_count` once each, and output names must be unique. Each
record uses its declared type and offset. For `nextxy.bin`, all records produce
`nextx`/`nexty` even if the input is named `experiment.bin`. Existing
`nextxy_noedge` output aliases remain `nextx`/`nexty` for compatibility.
`--variables nexty` may write only that variable, but still requires the complete
Binary size and valid complete reference definition; it reads record 2.

Without the option, existing filename inference and `--variables` fallback remain.
`--generate-list` cannot be combined with `--reference-binary`. Coordinate centers,
missing/special values, layer order, raw integers and zlib/shuffle level 3 are
unchanged. Missing inputs, unregistered references, inconsistent records and size
mismatches fail explicitly. Existing outputs are overwritten by default; use `--no-overwrite` where supported to retain them. Each file is privately written and
read-back verified, closed, then published; a failed write preserves any previous
output and removes its temporary file. Earlier successful variants remain if a
later conversion fails. Binary inputs are never modified.

Mekong samples were generated by `script_params/s06-subbasin.sh` using example
thresholds 30,000 / 5,000 km². Stage 2 preserves Stage 1 IDs/boundaries and adds
IDs only in previously unassigned network regions; neither threshold guarantees
a minimum segment area. `subbsn` positive values are segment IDs; `subcol` positive
values are display categories, not IDs. Zero remains unassigned modeled network,
and -9999 remains outside-network/missing.

### Future input-matrix converter

Input matrices are handled separately from ordinary map rasters because they
have dimensions `NX,NY,INPN` and mixed `inpx`/`inpy`/`inpa` block types. The
dedicated [`convert_inpmat.py`](../code/convert_inpmat.py) preserves their
Fortran-compatible storage and `diminfo_*.txt` metadata; it supports explicit
`binary-to-netcdf` and `netcdf-to-binary` conversion.

## Default high-resolution Binary restoration

By default, `s04-restore_highres_binary.sh` restores all registered high-resolution
variables available in the selected NetCDF map (`VARS="all"`). Missing optional
NetCDF products are skipped. Existing Binary files are replaced by default unless `--no-overwrite`
is specified. Set `VARS` to explicit registered stems to restore a subset; an
explicitly requested missing input remains an error.
