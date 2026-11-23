# CaMa-Flood Common Utilities

This directory contains shared standalone utilities: the `igetday` calendar helper and Python tools for describing model outputs. These tools do not rerun the model. `Makefile` and `igetday.F90` were moved here from the root `util/` directory; all utilities live directly under `tools/`.

The standalone Python [flood-depth downscaling package](output_analysis/downscale_flddph/README.md) ports the tributary-aware `flddph` method and includes a reproducible Mekong sample. It is separate from the legacy Fortran tool under `etc/downscale_flddph/` and does not alter model execution.

## Count days in a month with igetday

`igetday.F90` accepts two positional integer arguments, year and month (1–12), and prints the number of days in that month to standard output, with Fortran list-directed whitespace. It uses the Gregorian leap-year rule (divisible by 4, except centuries not divisible by 400), with the existing special case that February in year 0 has 28 days. No input or output data files are used. Supply both arguments and a valid month; the program does not validate the calendar input range.

### Compile and run

From the repository root, first prepare the ignored machine-specific `config/Mkinclude` as described in [the v5 configuration guide](../config/README.md). Then run:

```sh
make -C tools all
./tools/igetday 2000 2
# Prints 29 (with leading whitespace).
make -C tools clean
```

The Makefile uses `FC`, `FFLAGS`, `LFLAGS` (and legacy `LFLAG` if supplied), and `INC` from `config/Mkinclude` or make command-line overrides. It has no dependency on model objects, Fortran modules, or NetCDF libraries; the standard `INC` flags may include NetCDF headers. It never falls back to `adm/Mkinclude` and does not edit either configuration. The build creates the ignored `tools/igetday` executable; `clean` removes it and local compiler intermediates, leaving the Python tools and source files intact. Build from `tools/` or use `make -C tools`, since the configuration path is relative to that directory.

### Use from other programs

Use an explicit executable path after building it. For example, in a shell where `CMF_BASE` is the repository root:

```sh
# Command substitution captures the number printed by igetday.
NDAY=$("${CMF_BASE}/tools/igetday" 2000 2)
```

Python callers can use `int(subprocess.check_output([str(cmf_base / "tools" / "igetday"), "2000", "2"], text=True))`. No PATH modification or exported environment variable is required by `igetday` itself.

The tracked Japan forecast example, `gosh_test/legacy/test3-jpn_fcast.sh`, uses this shared executable for its starting and ending month lengths. Its two calls now use `$BASE/tools/igetday`; build the helper separately before using that example. The v5 `gosh_test/compile.sh` builds only the model and does not build this utility. Scripts under `etc/downscale_flddph/`, `etc/n-year_flood_depth/`, and `etc/runoff_preset/` have independent local `src/igetday` sources/targets; they are not redirected by this consolidation. No shared-helper call or PATH dependency was found in current Tutorial, Visualization, map, or runoff-input workflows.

The tracked `legacy/gosh/` reference copy still contains the original `util` build-directory and `$BASE/util/igetday` references. It is preserved unchanged and is not a v5 build/run entry point; using those historical scripts against the new layout would require a separate adaptation. Historical descriptions in development plans and research records likewise retain the old paths. The historical root `archive_src.sh` now copies `tools/` instead of `util/`; its other v4 package assumptions are unchanged, and this consolidation does not establish a v5 packaging workflow.

## Generate GrADS CTLs for Binary Restart files

`generate_restart_ctl.py` creates one GrADS descriptor for each existing main Binary Restart in a run directory. It reads the active `input_cmf.nam`, the map's `params.txt`, and [`variable_table/restart_variables.csv`](../variable_table/restart_variables.csv). The registry documents the field names, units, internal kinds, order, and optional conditions.

`generate_output_ctl.py` resolves blank descriptive fields in output-alias rows through their `alias_of` canonical row. The requested alias name remains the CTL variable and output filename name.

Run it from the repository root:

```sh
python3 tools/generate_restart_ctl.py --run-dir out/mek02-longterm_mapnc
```

Use `--restart PATH` to target one file, or `--endian little` / `--endian big` if the restart was written on a host with a different byte order. The default is the current host's native byte order. The tool reads the restart filename's `YYYYMMDDHH` stamp for a one-time `TDEF` and checks that the file size matches the selected fields and map dimensions.

The main `.bin` file stores map-sized variables as consecutive direct-access records. The tool selects them in Binary order according to `LSTOONLY`, `LGDWDLY`, `LDAMOUT`, and `LLEVEE`. It excludes the separate `.bin.pth` bifurcation data because those values use `NPTHOUT x NPTHLEV`, not the geographic map grid.

### Float64 visualization copy

GrADS gridded Binary CTLs describe standard 32-bit IEEE float records; they do not describe CaMa-Flood's 64-bit direct-access restart records ([GrADS binary variable format](https://sources.debian.org/src/grads/3%3A2.2.1-5/doc/variableformats.html)). When `LRESTDBL=.TRUE.`, the tool therefore writes a neighboring `*.grads32.bin` visualization copy, converting each record to Float32, and points the CTL at that copy. The original restart is never changed. This is a lossy visualization representation; use the original restart for model restart or scientific calculations. With `LRESTDBL=.FALSE.`, the CTL points directly to the Float32 restart file.

CTL files and any Float32 visualization copies are overwritten on regeneration. The tool does not change model outputs or restart files. NetCDF Restarts (`LRESTCDF=.TRUE.`) are not handled.

## Generate GrADS CTL files for binary output

`generate_output_ctl.py` creates one GrADS descriptor (`.ctl`) per configured, supported `NX x NY` float32 output. It reads:

- `input_cmf.nam` from the run directory (or `--namelist`), including simulation dates, `DT`, `IFRQ_OUT`, `CVARSOUT`, output paths, and binary/vector settings.
- The map's `params.txt`, located by following `CNEXTXY`, `CGRAREA`, or `CDIMINFO` in the namelist.
- [`variable_table/output_variables.csv`](../variable_table/output_variables.csv) for names, metadata, data type, dimensions, and missing value.

Run from any working directory:

```sh
python3 tools/generate_output_ctl.py --run-dir out/mek01-default_run --mode planned
python3 tools/generate_output_ctl.py --run-dir out/mek01-default_run --mode existing
```

The byte order defaults to the Python host's native byte order. When outputs were created on another architecture, set it explicitly with `--endian little` or `--endian big`.

### Modes

- `planned` uses the namelist schedule and creates CTLs before or during a run without requiring output binaries or checking their sizes. A CTL may describe records that have not been written yet.
- `existing` considers only configured binary files that exist, infers record counts from file size, and compares them with the namelist schedule. If a file has fewer complete records than expected, it reports the file as incomplete and writes a CTL for the records present. A partial trailing record or excess records is an error and produces no CTL for that file.

Both modes overwrite matching CTL files. Binary data are never created or changed. CTLs are placed beside their corresponding binaries.

### Time axis and data layout

The tool follows `CMF_DRV_ADVANCE`: ordinary outputs are written at the end of a model time step when the ending clock hour is divisible by `IFRQ_OUT` and the minute is zero. The first record is therefore the first scheduled output timestamp after the simulation start. Averages refer to the interval ending at that timestamp; snapshots refer to the state at that timestamp. If the final model step lands on an output boundary, the model can write a record at the configured end timestamp. The tool counts only timestamps reached by the configured outer `DT` steps and uses the timestamps actually implied by the source schedule.

The map extent in `params.txt` is expressed as cell edges. CTLs use cell-center coordinates, an increasing south-to-north `YDEF`, and `OPTIONS yrev` to match CaMa-Flood's north-to-south map rows. Ordinary binary records are direct-access, four-byte float records with `NX * NY` values and no sequential-record markers.

### Scope and limitations

- NetCDF output (`LOUTCDF=.TRUE.`), vector output (`LOUTVEC=.TRUE.`), non-confirmed registry rows, and non-`NX,NY` arrays such as `pthflw` are skipped with a reason.
- Binary output with `LOUTINI=.TRUE.` is rejected because the current Fortran initial-output path advances the shared record counter but skips binary writes.
- Registry entries missing a required confirmed `long_name`, `units`, `binary_dtype`, `dimensions`, or `missing_value` are not used.
- Binary files do not identify their own byte order. Specify `--endian` when the generation host's native order differs from the model-output host.
- `existing` can verify size and record count, but cannot prove that a same-named binary was produced with the current namelist.
- Long-term template CTLs combining multiple annual files are not implemented. Their filename/year-boundary convention needs a separate specification; the current tool creates independent per-file CTLs only.
