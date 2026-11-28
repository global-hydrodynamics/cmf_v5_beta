# Tutorial01: Get Started with CaMa-Flood v5

This tutorial introduces how to obtain and navigate CaMa-Flood, find the files used by a GOSH script, build and run the model, and locate the outputs. The 40-day sample run demonstrates the workflow; it is not a scientific validation of the model.

## 0. Obtain CaMa-Flood

Use the v5 repository, `global-hydrodynamics/cmf_v5_beta`. Its default/base
branch is `main`. The current v5b01 tutorial and renamed input datasets are on
the approved `feature/package-builder` branch and have not yet been merged into
`main`. To obtain the version described by this manual during beta preparation:

```bash
git clone --branch feature/package-builder https://github.com/global-hydrodynamics/cmf_v5_beta.git
```

This creates `cmf_v5_beta/`. Without Git, select `feature/package-builder` in the
[v5 repository](https://github.com/global-hydrodynamics/cmf_v5_beta) branch selector
before choosing **Code → Download ZIP**. Extract the archive and use its root;
the extracted folder name can differ. Place the checkout in a suitable working
location; no fixed machine-specific path is required.

The maintainer plans to merge the development branch into `main` once the
**v5b01 package is ready**. After that integration, the standard acquisition
command will be:

```bash
git clone https://github.com/global-hydrodynamics/cmf_v5_beta.git
```

Until the merge is published, do not assume that default `main` contains the
renamed input paths used below. Use the tutorial and inputs from the same revision.

Tutorial01's learner starting state does not contain a compiled `src_main/MAIN_cmf` executable or generated run results. You will build the executable in Section 3 and run the experiment later in this tutorial.

### Learning Check

- [ ] I can obtain the matching v5 beta revision and locate its repository root.
- [ ] I know that I will build `MAIN_cmf` as part of this tutorial.

## 1. Find the repository root

Open a terminal and change to the root of the repository you cloned or extracted. Confirm the location and inspect the root directory:

```bash
cd /path/to/cmf_v5_beta
pwd
ls -lF
bash s00-configure_cama_root.sh
```

When `s00-configure_cama_root.sh` asks, confirm adding `CMF_V50_ROOT` to the startup file it identifies. The script prints the exact command to activate that change in the current terminal. Run that command, or open a new terminal, then verify the value:

```bash
printf '%s\n' "$CMF_V50_ROOT"
```

The value should be the CaMa-Flood repository root. `s00` updates your shell startup configuration; it does not change variables in the already-open terminal by itself. In the root listing, `-l` shows detailed file information and `-F` adds markers: directories end in `/`, executable files normally end in `*`, and symbolic links may end in `@`. These markers are display aids, not part of the actual filenames.

### Expected output

This abbreviated excerpt is based on an actual repository-root `ls -lF` on the verified GitHub checkout. The directory was named `gosh_sample/` in that listing and is now named `gosh_test/`; sizes, dates, and owner names vary between computers. `...` marks omitted listing entries.

```text
drwxr-xr-x    7 yamadai  staff   224 Nov  8 10:36 config/
drwxr-xr-x   11 yamadai  staff   352 Nov  5 22:07 gosh_test/
drwxr-xr-x   11 yamadai  staff   352 Nov  4 21:46 inp/
drwxr-xr-x   10 yamadai  staff   320 Nov  5 22:07 map/
drwxr-xr-x  109 yamadai  staff  3488 Nov  8 10:36 src_main/
drwxr-xr-x    9 yamadai  staff   288 Nov  8 18:03 tutorial/
-rwxr-xr-x@   1 yamadai  staff 13533 Nov 26 09:20 s00-configure_cama_root.sh*
-rwxr-xr-x@   1 yamadai  staff 23526 Nov 28 10:34 s01-setup_fortran.sh*
-rwxr-xr-x@   1 yamadai  staff 15554 Nov 27 22:36 s02-python_setup.sh*
-rwxr-xr-x@   1 yamadai  staff  7568 Nov 27 22:35 s03-activate_cmf_pyenv.sh*
```

The `/` suffix distinguishes directories such as `src_main/` and `tutorial/`; the `*` suffix marks the executable setup scripts. The markers are not part of the names. The main directories are `src_main/` (v5 model source), `map/` (river maps and map tools), `inp/` (runoff datasets), `gosh_test/` (maintained run examples), and `tutorial/` (beginner tutorials). The root setup scripts diagnose and prepare local development environments.

### Learning Check

- [ ] I can locate the model source and the bundled map and runoff directories from the root listing.
- [ ] I can identify directories marked with `/` and executable setup scripts marked with `*`; these markers are not part of the filenames.

## 2. Prepare the local environment

Run the Fortran and Python setup scripts from the repository root. `s01-setup_fortran.sh` checks the Fortran build environment and offers to generate a suggested configuration. `s02-python_setup.sh` checks Python and offers a repository-local virtual environment for optional Python packages. Python is not required to run Tutorial01's Fortran simulation.

```bash
cd "${CMF_V50_ROOT}"
pwd
bash s01-setup_fortran.sh
```

### Fortran setup: output and required actions

The script checks tools and capabilities needed for the selected build, including GNU Make, a Fortran compiler, OpenMP, NetCDF-Fortran, MPI, and sample inputs. A successful check is marked `[OK]`. If a required check is unavailable, the script prints guidance for installing or loading that dependency; address the missing requirement and run the diagnostic again.

After the diagnostic, an interactive terminal displays a prompt like this:

```text
Installed components:
  [OK] GNU Make           GNU Make 3.81
  [OK] GNU Fortran        GNU Fortran (Homebrew GCC 14.2.0_1) 14.2.0
  [OK] OpenMP             -fopenmp compile, link, and run passed
  [OK] NetCDF-Fortran     4.6.2
  [OK] MPI Fortran        mpifort compile/link test passed
...
Recommended configuration:
  Compiler: GNU Fortran (OpenMP enabled)
  NetCDF: Enabled (NF90_DOUBLE read/write test passed)
  MPI: Disabled by default
  Precision: SinglePrec_CMF, matching standard GNU templates
...
Generate ./Mkinclude? [Y/n]: y
[SUCCESS] Generated ./Mkinclude
To activate this configuration:
Existing config/Mkinclude was not changed. Back it up before choosing to replace it.
Legacy v4 builds continue to use adm/Mkinclude.
```

The example shows a user choosing `y`. The suggested file is created at the repository root; the setup script does not overwrite the active `config/Mkinclude`. Review the generated configuration before activating it. Since `config/Mkinclude` already exists, back it up before replacing it, and copy the suggested file only if you intend to change the active v5 configuration:

```bash
cp Mkinclude config/Mkinclude
```

The copy replaces an existing `config/Mkinclude`. If you want to keep the current compiler configuration, do not run the copy command; use the configuration already prepared for your environment.

The Python setup is also run from the repository root. If you choose to create the optional local environment, register its `cmfpy` activation alias afterward:

```bash
cd "${CMF_V50_ROOT}"
bash s02-python_setup.sh
bash s03-activate_cmf_pyenv.sh
```

If `.venv` does not exist, the script reports a Python interpreter candidate and asks whether to create or update the repository-local environment. In the captured example, the user answered `n`:

```text
Repository environment:
  [--] not present
Selected interpreter for .venv: python3 (...)
Packages will be installed only inside .venv, never into the system interpreter.
Create/update .venv and install requirements? [Y/n]: n
Python environment was not changed.
```

Answer `y` only if you want the optional packages installed in `.venv/`; they are not installed into the system Python. `s03` registers `cmfpy` in your shell startup file; follow the activation command it prints or restart the terminal before using the alias. In the newly configured terminal, `cmfpy` activates `.venv`, and `deactivate` exits it. Tutorial01's Fortran simulation does not require Python or this environment.

```bash
cmfpy
# Run Python tools in the activated environment when needed.
deactivate
```

### Learning Check

- [ ] I can tell from the setup output whether the required Fortran checks passed and what to do if one failed.
- [ ] I can identify which configuration file the setup instructions ask me to copy, and where Python setup reports its result.

## 3. Build the model

CaMa-Flood is written in Fortran. A compiler translates its source files into an executable program. Build or update the v5 executable with the repository's standard target, `make all`:

```bash
cd "${CMF_V50_ROOT}"
cd src_main
pwd
make all
ls -lhF MAIN_cmf
```

The build may print unused-import warnings from existing source files. In the checked build, `make all` returned zero and the final command showed:

```text
-rwxr-xr-x  1 yamadai  staff   600K Nov  8 10:36 MAIN_cmf*
```

This confirms that the executable was produced in that checkout; its size and listing details can vary. Do not run `MAIN_cmf` directly from this terminal: the experiment script prepares its Namelist and working directory.

### Learning Check

- [ ] I can locate `MAIN_cmf` under `src_main/` after the build.
- [ ] I can run `make all` and find `MAIN_cmf` in `src_main/`.

## 4. Read the experiment plan and script

A GOSH script is a plain-text shell script that records experiment settings and the commands used to run the model. First read the [Tutorial Design Specification](tutorial_design.md), which describes the purpose, computational conditions, input datasets, and expected products for this experiment.

The script uses `CMF_V50_ROOT` for repository files and writes that path into the Fortran NAMELIST field `CMF_BASE`. The NAMELIST name remains part of the model interface; `CMF_V50_ROOT` is the shell environment setting.

```bash
cd "${CMF_V50_ROOT}"
cd tutorial/tutorial01-get_started
pwd
cat tutorial_design.md
cat tutorial01-get_started.sh
```

`cat` prints a file in the terminal. The GOSH script is several screens long, so you do not need to read it all at once. Open it in an ordinary text editor to inspect its settings. `nano` and `vi` or `vim` are terminal editors; Visual Studio Code is a graphical editor that may be installed separately. Other plain-text editors for your operating system are also suitable. A word processor is not suitable because it can add document formatting to the script.

If available, you can inspect without saving using `nano tutorial01-get_started.sh` and exit with Ctrl-X, choosing not to save if asked. In `vi` or `vim`, press Esc, type `:q!`, and press Enter to quit without saving. Editor commands are optional and availability varies by system.

### Experiment settings at a glance

| Category | Tutorial01 setting |
|---|---|
| Project | `PROJ="tutorial01-get_started"` |
| River map | `map/mekong_15min/` |
| Runoff | `inp/repo-mek_1deg_bin/`, daily Binary records grouped by month |
| Runoff-to-map mapping | `diminfo_repo-mek_1deg.nml` and `inpmat_repo-mek_1deg.nc` in the map directory |
| Period | 2000-01-01 00:00 to 2000-02-10 00:00; end time is exclusive (40 days) |
| Time step | Base `DT=3600` seconds; adaptive time stepping enabled |
| Execution | Non-MPI, one OpenMP thread; bifurcation enabled |
| Output | Daily Binary: `outflw`, `storge`, `sfcelv`, `flddph`, `fldfrc` |
| Output directory | `tutorial/tutorial01-get_started/out/${PROJ}/` |

The rest of the tutorial locates the real input files and shows how the GOSH settings select them.

### Learning Check

- [ ] I can find an experiment condition in `tutorial_design.md` and locate the corresponding setting in the script.

## 5. Inspect the river map

A river map describes the model grid, river connectivity, and physical properties used by the simulation. Return to the repository root, enter the Mekong map directory, and list a few representative files:

```bash
cd "${CMF_V50_ROOT}"
cd map/mekong_15min
pwd
ls -lhF params.nml nextxy_noedge.nc ctmare.nc elevtn.nc rivwth_merit.nc bifprm.csv
```

### Expected output

These file names and representative sizes were observed in the bundled checkout. Permissions and timestamps can differ.

```text
-rw-r--r--@ 1 yamadai  staff    68K Nov 28 10:03 bifprm.csv
-rw-r--r--@ 1 yamadai  staff    34K Nov 28 07:09 ctmare.nc
-rw-r--r--@ 1 yamadai  staff    28K Nov 28 07:09 elevtn.nc
-rw-r--r--@ 1 yamadai  staff    23K Nov 28 07:09 nextxy_noedge.nc
-rw-r--r--@ 1 yamadai  staff   438B Nov 28 07:09 params.nml
-rw-r--r--@ 1 yamadai  staff    33K Nov 28 07:10 rivwth_merit.nc
```

`params.nml` describes the map grid and geographic bounds. The `.nc` files are individual NetCDF map variables; `bifprm.csv` stores bifurcation parameters. The high-resolution tile inventory is in `1min/location.csv`. The tutorial script selects connectivity and channel width with these settings:

```sh
MAPDIR="${CMF_V50_ROOT}/map/mekong_15min"
#NEXTXY="${MAPDIR}/nextxy.nc"
NEXTXY="${MAPDIR}/nextxy_noedge.nc"
#RIVWTH="${MAPDIR}/rivwth.nc"
RIVWTH="${MAPDIR}/rivwth_merit.nc"
```

The commented lines show alternative map products; the uncommented assignments select the files used here.

### Learning Check

- [ ] I can find `MAPDIR` and identify the connectivity and width files selected by `NEXTXY` and `RIVWTH`.

## 6. Inspect runoff forcing

Runoff forcing is water input supplied to the model over time. The sample uses daily Binary records grouped into monthly files on a grid coarser than the river map. Inspect the two files covering the 40-day interval:

```bash
cd "${CMF_V50_ROOT}"
cd inp/repo-mek_1deg_bin/runoff
pwd
ls -l Roff____200001.one Roff____200002.one
```

### Expected output

The monthly files contain 31 and 29 daily fields respectively (60 records total).
Their exact sizes are 74,400 and 69,600 bytes. Each daily field is 2,400 bytes;
monthly grouping does not average the values.

The corresponding GOSH settings identify the dataset, file naming rule, frequency, and unit conversion:

```sh
ROFFTAG="repo-mek_1deg_bin"
INPMAT_TAG="repo-mek_1deg"
RUNOFF_DIR="${CMF_V50_ROOT}/inp/${ROFFTAG}/runoff"
IFRQ_INP=24
CROFFREQ="MON"
CROFPRE="Roff____"
CROFSUF=".one"
DROFUNIT=86400000
```

`Roff____` + a month in `YYYYMM` form + `.one` makes a monthly filename containing daily records. `IFRQ_INP=24` means the forcing interval is 24 hours. `DROFUNIT` converts the supplied `mm/day` runoff values to the model's `m/s` units. The 40-day interval ends at February 10 00:00, so February 9 is the final daily input date.

### Learning Check

- [ ] I can locate a monthly file containing daily runoff records in the listed directory.
- [ ] I can find the GOSH settings that select the runoff directory and construct its filename.

## 7. Inspect runoff-to-map mapping

The runoff grid is 20 × 30 cells, while this Mekong river map is 80 × 120 cells. The input-dimension descriptor and mapping matrix tell the model how runoff-grid values correspond to map cells. These files are stored with the map because the mapping is specific to the map and runoff-grid pairing.

```bash
cd "${CMF_V50_ROOT}"
cd map/mekong_15min
pwd
ls -lhF diminfo_repo-mek_1deg.nml inpmat_repo-mek_1deg.nc
cat diminfo_repo-mek_1deg.nml
```

### Expected output

Observed sizes and the descriptor contents:

```text
-rw-r--r--@ 1 yamadai  staff   485B Nov 28 09:01 diminfo_repo-mek_1deg.nml
-rw-r--r--@ 1 yamadai  staff    82K Nov 28 09:01 inpmat_repo-mek_1deg.nc
```

```text
&DIMINFO
  NX    = 80
  NY    = 120
  NLFP  = 10
  WEST  = 90.0
  EAST  = 110.0
  NORTH = 35.0
  SOUTH = 5.0
/

&INPUTDIM
  INPMAT_FILE = 'inpmat_repo-mek_1deg.nc'
  NXIN    = 20
  NYIN    = 30
  INPN    = 4
  WESTIN  = 90.0
  EASTIN  = 110.0
  NORTHIN = 35.0
  SOUTHIN = 5.0
  OLATIN  = 'NtoS'
/
```

The script points to this pair and turns on input-matrix mapping with `LINTERP`:

```sh
DIMINFO="${MAPDIR}/diminfo_${INPMAT_TAG}.nml"
INPMAT="${MAPDIR}/inpmat_${INPMAT_TAG}.nc"
LINTERP=".TRUE."
```

`DIMINFO` is a Fortran Namelist with `&DIMINFO` for the CaMa-Flood model grid and `&INPUTDIM` for the external runoff input grid. `INPMAT` is the NetCDF runoff-to-map mapping data. With `LINTERP` true, runoff is mapped through this matrix. The supplied files already match this sample; Tutorial01 does not regenerate them.

### Learning Check

- [ ] I can locate the two mapping files and match them to `DIMINFO` and `INPMAT`.
- [ ] I can find `LINTERP` in the same GOSH configuration.

## 8. Run the experiment

The script defines the project as `PROJ="tutorial01-get_started"` and constructs `RUNDIR` as the Tutorial01 directory's `out/${PROJ}/`. Keeping each experiment under its own project name makes outputs easier to compare and prevents one experiment from replacing another. Tutorial02 uses the same naming convention for its multiple experiments.

For this tutorial, leave the project name at its default. The script can be rerun: it replaces known products in the selected project's directory, and does not remove the shared `out/` directory, sibling project directories, or unrelated notes in the selected directory.

Run it from the Tutorial01 directory:

```bash
cd "${CMF_V50_ROOT}"
cd tutorial/tutorial01-get_started
pwd
./tutorial01-get_started.sh
```

### Expected output

This abbreviated excerpt was captured from a 40-day run using the current workflow. The temporary validation output path is shortened; in your checkout `RUNDIR` is under the Tutorial01 directory.

```text
PROJ = tutorial01-get_started
RUNDIR = .../tutorial/tutorial01-get_started/out/tutorial01-get_started
Overwriting previous sample results in: .../out/tutorial01-get_started
...
[STEP 3/5] Generate planned binary-output CTLs
Expected output records: 40 (00Z02jan2000 to 00Z10feb2000)
...
[STEP 4/5] Run CaMa-Flood v5 from 2000 to 2000-2-10
Exit status: 0
...
[STEP 5/5] Generate GrADS CTLs for Binary Restart files
...
[SUCCESS] tutorial01-get_started.sh
Results: .../tutorial/tutorial01-get_started/out/tutorial01-get_started
```

The script first writes the experiment Namelist and planned GrADS CTL files, then runs the model and prepares a Restart CTL. Shell messages go to the terminal; detailed model progress is in `log_CaMa.txt`. Exit status zero and the `[SUCCESS]` message mean the workflow completed without a reported command failure.

### Learning Check

- [ ] I can find `PROJ` and the output directory shown in the script's startup messages.
- [ ] I can run the script from its documented directory and recognize successful completion.

## 9. Inspect the results

The GOSH run directory contains the copied executable, Namelist, model log, timing record, Restart, binary outputs, and CTL metadata. Inspect it from the repository root:

```bash
cd "${CMF_V50_ROOT}"
cd tutorial/tutorial01-get_started
pwd
ls -lhF out/tutorial01-get_started
```

### Expected output

Representative files and sizes from the checked run; this excerpt omits other entries. `*` is the `-F` marker for the executable copy:

```text
-rwxr-xr-x ... MAIN_cmf*                 600K
-rw-r--r-- ... flddph2000.bin            1.5M
-rw-r--r-- ... fldfrc2000.bin            1.5M
-rw-r--r-- ... input_cmf.nam             4.6K
-rw-r--r-- ... log_CaMa.txt              1.6M
-rw-r--r-- ... outflw2000.bin            1.5M
-rw------- ... outflw2000.ctl            293B
-rw-r--r-- ... restart2000021000.bin     450K
-rw-r--r-- ... sfcelv2000.bin            1.5M
-rw-r--r-- ... storge2000.bin            1.5M
```

All five daily output variables contain 40 records. The `outflw2000.ctl` file reports `TDEF 40 LINEAR 00Z02jan2000 1dy`; the model's output timestamps follow its output convention, while the simulation end time is exclusive. The model log ends with `CMF::===== CALCULATION END =====`. The generated Restart is accompanied by a GrADS CTL. These are workflow checks, not evidence that simulated values are scientifically correct.

### Learning Check

- [ ] I can locate the discharge output file `outflw2000.bin` and the model log `log_CaMa.txt`.
- [ ] I can recognize the model's normal-completion message in `log_CaMa.txt`.
