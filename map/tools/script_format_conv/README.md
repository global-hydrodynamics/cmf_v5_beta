# Map format conversion templates

These shared templates convert registered base-resolution and high-resolution map rasters between Binary and NetCDF, and generate optional numeric COG visualization caches. Copy the scripts into a map-local `script_format_conv/` directory and run there. No map name or `MAP_DIR` setting needs editing. The Mekong sample contains a ready-to-use copy at [`map/mekong_15min/script_format_conv/`](../../mekong_15min/script_format_conv/).

The scripts reuse [`convert_map_binary_to_netcdf.py`](../code/convert_map_binary_to_netcdf.py), [`convert_highres_binary_to_netcdf.py`](../code/convert_highres_binary_to_netcdf.py), and the authoritative [`variable_table/map_variables.csv`](../../../variable_table/map_variables.csv) registry. `s01`/`s02` handle binaries directly in the map root; `s03` handles registered high-resolution tile binaries.

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

   The same scripts work in any map-local `script_format_conv/`, including Mekong and global maps. Candidates are ordered by numeric `category_id` and then registry row order. A file listed in multiple categories appears once under its first category. Only registered files directly in the map root and supported by the converter are listed. Unregistered binaries and registered but unsupported layouts are reported as warnings. The current `NX,NY,INPN` runoff input matrices are not handled as map rasters and are omitted. If a list already exists in the current directory, `s01` asks before replacing it; non-interactive use preserves it.

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

Run both scripts from the same map-local `script_format_conv/` current directory so `s02` reads the list created by `s01`. The target map comes from the current directory; only the shared converters and registry are resolved from `SCRIPT_DIR` in the development repository. They only inspect `.bin` files directly under `MAP_DIR`; high-resolution subdirectories are never searched.

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

The `t01-legacy_netcdf_map.sh` script creates `netcdf/rivclim.nc` with `nextx`, `nexty`, `lon`, `lat`, `ctmare`, `elevtn`, `nxtdst`, `rivlen`, and all `fldhgt` layers. It creates `netcdf/rivpar.nc` with `rivwth`, `rivhgt`, and `rivman`. The defaults match the Mekong simulation examples: `nextxy_noedge.nc` and `rivwth_merit.nc`. Edit `NEXTXY` and `RIVWTH` near the top to choose `nextxy.nc` or `rivwth.nc` instead.

Run the map-local script independently of `s01` and `s02`:

```sh
cd map/mekong_15min/script_format_conv
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

Python preflights **all selected resolutions** before creating any output. It
lists present/missing inputs and existing/new outputs, then asks once in a
terminal: `Overwrite all N existing selected outputs? [y/N]`. `y` overwrites all
selected existing outputs; `n`/Enter asks for each output individually. Missing
Binary inputs never cause unrelated existing NetCDFs to be overwritten. `--force`
skips confirmation; noninteractive runs without it preserve existing outputs.
No bulk prompt appears when all outputs are new. The standard CLI also defaults
to all CSV products and accepts whitespace-separated resolution tags via `--hires`;
`--interactive-overwrite` enables the prompt policy used by s03.

This replaces the older seven/eleven-product defaults. To add missing outputs
while preserving existing ones, run noninteractively without `--force`, or answer
No to Overwrite all and No at the individual prompts. Signed int8 codes, float32
values, record planes and registered missing values/units are unchanged.

For the bundled Mekong example:

```sh
cd map/mekong_15min/script_format_conv
./s03-convert_highres_netcdf.sh
```

For each selected variable, `s03` calls the shared high-resolution converter. It reads each tile's geometry from `<MAP_DIR>/<HIRES>/location.txt`, and registered variable names, signed type, record index/count, missing value, and dimensions from `variable_table/map_variables.csv`. Unregistered files are ignored; absent registered Binary tiles skip. Present tiles with inconsistent metadata or a Binary size that does not match `location.txt` fail explicitly before conversion. A multi-record file such as `catmxy` or `downxy` is written as one NetCDF containing all registered variables in record order.

Outputs are individual tiles at `<MAP_DIR>/<HIRES>_nc/<AREA>.<VAR>.nc`; the wrapper also copies `<MAP_DIR>/<HIRES>/location.txt` to `<MAP_DIR>/<HIRES>_nc/location.txt` as geometry metadata. NetCDF variables use `(lat,lon)` dimensions, cell-center coordinates, and the binary's row/record order; data are copied in bounded chunks and checked by reading each chunk back byte-for-byte. NetCDF4 uses lossless zlib/deflate compression with shuffle and a 256-by-256 maximum chunk shape. `COMPRESSION_LEVEL` defaults to 3; set it to 0–9, where 0 disables deflate. No scaling, offset, precision reduction, or quantization is used. `JOBS` defaults to 8 and controls the maximum number of Python worker processes; use `JOBS=1` for sequential conversion. Python schedules each registered variable/tile pair once, and the shell wrappers do not start background jobs. Existing NetCDF outputs are preserved in noninteractive mode; terminal s03 runs use the bulk/individual confirmation above. Changing compression alone does not authorize replacement; approve overwrite or run with `--force` to rebuild. Forced conversion stages a complete replacement before atomically replacing the previous output, preserving it if conversion fails. The input Binary and source `location.txt` are read-only. A successful conversion verifies stored values and file layout, not scientific correctness or model-reader compatibility.

Focused tests target CaMa-Flood's Binary-to-NetCDF contract: types, records, coordinates, chunk/task assignment, parallel error reporting, and the requested compression settings. They do not re-test the internal lossless algorithms provided by zlib, HDF5, or NetCDF. Broader map-package and model-reader integration is a separate pre-merge check when required by the change and available data.

The NetCDF C library must be installed and discoverable (typically through `nc-config`); Python uses only its standard library.

## Convert high-resolution tiles in an external package (`t03`)

Use `t03-convert_external_highres.sh` when the source maps live outside this v5 repository. Set `MAP_ROOT`, `MAPS`, `HIRES`, `VARS`, `COMPRESSION_LEVEL`, and `JOBS` at the top of the script. It resolves the shared converter and `variable_table/map_variables.csv` relative to its own location, warns and skips missing map/resolution directories, and stops on conversion errors. It copies each selected `location.txt` to `<MAP_DIR>/<HIRES>_nc/`; existing NetCDF outputs are skipped unless the script is run with `--force`. As with `s03`, changing the compression level does not alter existing files; use `--force` to rebuild them, with the old output preserved if conversion fails. `--force` is the only shell command-line option; configure parallelism with `JOBS`, not a shell argument.

```sh
map/tools/script_format_conv/t03-convert_external_highres.sh
map/tools/script_format_conv/t03-convert_external_highres.sh --force
```

The default settings point to the maintainer's v400 data package. Edit `MAP_ROOT` before using the script on another workstation. It writes converted files alongside the external source maps and does not copy map data into this repository.

## Supported formats and dependencies

The workflow supports registered `float32` or `int32` rasters with dimensions `NX,NY` or `NX,NY,NLFP`, including multi-variable direct-access files such as `nextxy.bin` and layered files such as `fldhgt.bin`. Data type, record order, dimensions, missing values, and variable metadata come from the registry and `params.txt`; the Binary inputs are not modified.

For s01–s04, Python uses only the standard library. Conversion also requires the NetCDF C shared library to be installed and discoverable, typically through `nc-config`. This workflow validates conversion and stored values; compatibility with model execution is a separate validation step.

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
`script_format_conv/` (already installed in the local global map), then:

```sh
cd map/glb_15min/script_format_conv
./s04-restore_highres_binary.sh
```

Adjust `VARS` and `JOBS` near the top as needed; leave `HIRES` empty for automatic selection. The same current-directory
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

1. `1min_nc/`
2. `30sec_nc/`
3. `15sec_nc/`

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

No overwrite prompt is needed: existing files always skip without `--force`,
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

### Source/output layout and band contract

- `netcdf/<stem>.nc` → `COG/<stem>.tif`: native **model grid**, never aggregated high-res pixels.
- `<HIRES>_nc/<area>.<stem>.nc` → `COG/<HIRES>/<area>.<stem>.tif`: native high-resolution grid.
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
execution; `--force` controls output overwriting and does not bypass resolution
confirmation. The subsequent overwrite confirmation and conversion algorithms
are unchanged.

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
For example, add `"rivwth_experiment.bin:rivwth.bin"` or
`"nextxy-experiment.bin:nextxy.bin"` only when those Binary inputs exist.

```sh
cd map/mekong_15min/script_format_conv
./s90-sample_netCDF_conversion.sh
# Existing outputs are refused; explicitly allow replacement:
./s90-sample_netCDF_conversion.sh --force
```

The target is the parent of the current map-local `script_format_conv/`, matching
s01–s03. From another working directory, or the shared template directory, supply
`--map-dir /path/to/map`; a shared template is never implicitly treated as a map.
Outputs retain each input stem: `<map>/netcdf/subbsn-sample.nc` contains `subbsn`,
and `<map>/netcdf/subcol-sample.nc` contains `subcol`. Only these two generated
Mekong NetCDF samples are explicitly approved for Git tracking in this task.

The existing converter also exposes the mapping directly:

```sh
python3 map/tools/code/convert_map_binary_to_netcdf.py \
  --map-dir map/mekong_15min \
  --input map/mekong_15min/subcol-sample.bin \
  --output map/mekong_15min/netcdf/subcol-sample.nc \
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
mismatches fail explicitly. Existing outputs are never overwritten without
`--force` (or the editable `FORCE=1` setting). Each file is privately written and
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

Input matrices are intentionally outside this raster converter. A future
`map/tools/code/convert_inpmat_binary_to_netcdf.py` should reuse the same CSV
variable definitions but handle `NX,NY,INPN`, mixed `inpx`/`inpy`/`inpa` block
types, INPN layers and the input-grid metadata in `diminfo_*.txt` separately.
No input-matrix Python converter or Shell wrapper is implemented by this task.
