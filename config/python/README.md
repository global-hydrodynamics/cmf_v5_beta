# Historical Python dependency profiles

These files record historical **direct-dependency profiles** for compatibility experiments with current CaMa-Flood v5 Python code. They do not recreate historical model versions, and they are not the standard installation requirements. The standard entry point remains the repository-root `requirements.txt`.

The root `s02-python_setup.sh` tries standard requirements first and uses the
2024 profile as one automatic compatibility fallback after installation or
validation failure. The fallback is installed into a clean `.venv`; the
previous environment is restored if the new profile does not validate. This
2024 profile is the only historical profile selected automatically by setup.
Both 2022 and 2020 are experimental and must be installed manually into
disposable environments; neither adds to the official β02 support matrix.

| File | Cutoff | Target interpreter | Notes |
|---|---|---|---|
| `requirements_2024.txt` | 2024-12-31 | CPython 3.12 | **Official β02 fallback profile.** Includes NumPy 1.26 and versions released by the cutoff. Tested on macOS arm64; not a guarantee for every OS/CPU. |
| `requirements_2022.txt` | 2022-12-31 | CPython 3.10 | **Experimental.** Exact direct pins passed the scoped Cloud Docker checks on Debian 11 / Linux amd64. Rasterio 1.3.4 has no PyPI macOS arm64 wheel, so the profile is not verified for Apple Silicon. Historical Panel/Bokeh do not meet current Explorer bounds. |
| `requirements_2020.txt` | 2020-12-31 | CPython 3.8 | **Experimental.** Exact direct pins passed scoped Cloud Docker checks on Debian 10 / Linux amd64, with the PyYAML procedure below. The profile does not support the current Explorer or COG creation. |

## Reproducibility and use

Create a disposable virtual environment with the target interpreter and install one profile directly, for example:

```bash
python3.12 -m venv /tmp/cmf-python-2024
/tmp/cmf-python-2024/bin/python -m pip install -r config/python/requirements_2024.txt
```

The pins constrain direct dependencies, not every transitive package; these
files are **not lock files** and may resolve different indirect versions over
time. Cloud's exact tested environment snapshots and limitations are recorded
in [`python_legacy_compatibility_handoff.md`](../../docs/python_legacy_compatibility_handoff.md)
and [`python_dependency_audit.md`](../../docs/python_dependency_audit.md). Do
not install historical profiles into the repository `.venv`.

The 2022 and 2020 experiments verified selected core I/O, map/runoff paths,
dependency consistency, and static CMF palette behavior only. They do not
establish current Map Explorer compatibility. In particular, the historical
Panel/Bokeh APIs are below current project bounds. Python 3.8 source import of
CMF Colormaps required a separately installed backport, while the package
metadata still requires Python >=3.9 and Matplotlib >=3.7. The 2020 GDAL
build lacks the COG driver.

### Python 3.8 experiment setup details

The verified Debian 10 / CPython 3.8.7 environment needed PyYAML 5.3.1 built
without its optional LibYAML extension. In the disposable target venv, install
it with the tested command before installing the profile:

```bash
python -m pip install --no-cache-dir --no-build-isolation \
  --no-binary=pyyaml --global-option=--without-libyaml 'PyYAML==5.3.1'
python -c 'import yaml; assert not yaml.__with_libyaml__'
python -m pip install -r config/python/requirements_2020.txt
```

For the separate Python 3.8 **source-path** probe of CMF Colormaps only, the
backport was installed explicitly:

```bash
python -m pip install 'importlib-resources==4.1.1'
```

This backport is not in either historical requirements file. It does not make
normal `cmf_colormap` package installation supported on Python 3.8. Neither
historical profile is selected by `s02-python_setup.sh`; the automatic
fallback remains 2024.

## Validation status (2026-11-27)

The 2024 profile was installed in a temporary CPython 3.12.3 environment on macOS arm64; `pip check` passed. Synthetic NetCDF/GeoTIFF round trips, a headless Matplotlib render with the CaMa-Flood `shade_rainbow` palette, Mekong `params.nml` parsing, a Tutorial 11 NetCDF read, and native-pixel-verified conversion of Mekong `uparea.nc` to a temporary COG passed. These checks support a compatibility fallback attempt, not a guarantee for all operating systems.

The 2022 profile was exercised in a temporary CPython 3.10.8 environment. All pinned packages except Rasterio were installed, and the PyPI `lmoments3` 1.0.4 wheel was installed by its immutable file URL because its filename version (`1.0.4.post1`) disagrees with its internal metadata (`1.0.4`) and index resolution rejects the pin. `pip check` passed for the installed subset. NumPy/NetCDF round trips, metadata parsing, Tutorial 11 xarray reading, a headless palette render, and the Mekong river-point information script passed. The full profile could not install on this Apple Silicon host: PyPI provides no Rasterio 1.3.4 macOS arm64 wheel, and its source build requires build tooling and GDAL not available here. This does not establish 2022 compatibility for COG, Explorer, or other Rasterio workflows.

All temporary environments and outputs were under `/private/tmp/cmf-dependency-audit`; the repository `.venv` was unchanged. Exact commands, versions, successful checks, and limitations are recorded in [`python_dependency_audit.md`](../../docs/python_dependency_audit.md) and [VR-0261](../../research/records/validation_runs/VR-0261.md).

The later isolated Linux 2022/2020 compatibility experiments and the Python 3.8 CMF Colormaps source-import follow-up are summarized in [`python_legacy_compatibility_handoff.md`](../../docs/python_legacy_compatibility_handoff.md). They were completed outside the local workstation and are not repeated by the checks in this repository.
