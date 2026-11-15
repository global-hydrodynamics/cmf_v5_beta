# CaMa-Flood v5 build configuration

Historical v4 sources and templates are tracked under [`legacy/`](../legacy/); their original adm/Mkinclude assumptions are preserved as references, not v5 build instructions. The v5 model and map tools use the separate machine-specific `config/Mkinclude`, so a v5 build cannot silently inherit v4 compiler settings.

`config/Mkinclude` is intentionally ignored by Git because compiler paths, libraries, and flags depend on the local machine. The tracked templates are the reusable starting points; the active file is created separately on each workstation or disposable CI checkout. Never add the active file to Git.

## Recommended GNU Fortran setup

The recommended workstation setup uses GNU Fortran with OpenMP, NetCDF-Fortran, and single precision. MPI and Heatlink are disabled by default. On macOS or Linux, install a compatible GNU Fortran toolchain and NetCDF-Fortran so `gfortran` and `nf-config` are available, then run the root setup script:

```sh
./s01-setup_fortran.sh
```

After reviewing the generated staging file, activate it explicitly:

```sh
if [ ! -e config/Mkinclude ]; then
    cp Mkinclude config/Mkinclude
else
    printf '%s\n' 'config/Mkinclude already exists; review it before replacing it.'
fi
```

The setup script never copies the file automatically and never changes `config/Mkinclude` or the legacy configuration. It requires a successful NetCDF-Fortran compile, link, and read/write check before offering to generate the v5 configuration. OpenMP is enabled when its compiler check succeeds. Without an interactive terminal, `s01-setup_fortran.sh` runs diagnostics only; unattended checks must initialize their own disposable configuration.

## Choosing a template manually

On a new machine with no active configuration, copy a suitable tracked template to the ignored path `config/Mkinclude`, then adjust it for the local installation. Check first so this does not overwrite an existing configuration:

```sh
if [ ! -e config/Mkinclude ]; then
    cp config/Mkinclude_gfortran config/Mkinclude
else
    printf '%s\n' 'config/Mkinclude already exists; leaving it unchanged.'
fi
```

- [`Mkinclude_gfortran`](Mkinclude_gfortran): tracked GNU Fortran baseline used by the former Linux workflow and a manual starting point for macOS and Linux.
- [`Mkinclude_gfortran_debug`](Mkinclude_gfortran_debug): GNU Fortran with runtime checks and debug information.
- [`Mkinclude_linux_ifx`](Mkinclude_linux_ifx): Linux Intel oneAPI `ifx`; load the compiler environment and provide a compatible NetCDF-Fortran `nf-config`.

GNU templates obtain Fortran include and link flags from `nf-config --fflags` and `nf-config --flibs`. Where available, `nc-config --libs` supplements the NetCDF-C search path needed by installations such as Homebrew; its duplicate `-lnetcdf` flag is filtered because `nf-config` already supplies it. Set `NF_CONFIG` or `NC_CONFIG` when either tool has a nonstandard name, or override `INC` and `LIB` for a custom installation. A missing `config/Mkinclude` produces a clear Make error; v5 builds do not fall back to `adm/Mkinclude`.

## Build entry points

```sh
make -C src_main all
make -C map/tools/code all
```

The active `config/Mkinclude` is local and machine-specific. It is ignored by Git; the three templates and this guide are tracked. Keep compiler outputs and local configuration out of commits. Optional MPI, Heatlink, ICI, and sediment configurations require additional setup and are not implied to be validated by the standard templates.

## Manual validation while CI is disabled

The former source/map GitHub Actions workflow has been removed from the active workflows directory by maintainer instruction. Automated CI is temporarily disabled pending a small, reproducible v5 regression suite; this does not remove the tests or establish scientific validation. See [the migration audit](../docs/migration_consistency_audit.md#manual-checks-retained-from-the-retired-workflow) for its previous coverage and retained manual commands. Use a reviewed local configuration or an independent disposable checkout, and never overwrite an existing active configuration automatically. The GNU template remains available for macOS/Linux setup; historical optional configurations are not thereby validated.
