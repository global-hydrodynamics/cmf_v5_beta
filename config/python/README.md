# Historical Python dependency profiles

These profiles provide historical **direct-dependency snapshots** for testing the current CaMa-Flood v5 Python code. They do not recreate historical model versions and are not the standard installation requirements. The standard entry point remains the repository-root `requirements.txt`.

| File | Cutoff | Target interpreter | Notes |
|---|---|---|---|
| `requirements_2024.txt` | 2024-12-31 | CPython 3.12 | Includes NumPy 1.26 to avoid the NumPy 2 ABI transition and versions released by the cutoff. Rasterio 1.4.1 published macOS arm64 wheels for supported Python versions. |
| `requirements_2022.txt` | 2022-12-31 | CPython 3.10 | Historical Python stack; current Map Explorer's declared Panel/Bokeh minimums post-date this profile. Rasterio 1.3.4 has no PyPI macOS arm64 wheel, so a native Apple Silicon installation may need an unsupported source build/GDAL and is not considered covered. |

## Reproducibility and use

Create a disposable virtual environment with the target interpreter and install one profile directly, for example:

```bash
python3.12 -m venv /tmp/cmf-python-2024
/tmp/cmf-python-2024/bin/python -m pip install -r config/python/requirements_2024.txt
```

The version pins constrain the direct packages, not every transitive package. They are therefore snapshots, **not complete lock files**; installation may resolve different indirect versions over time. Record the resolved `pip freeze` and platform alongside any experiment. Do not install these profiles into the repository `.venv`.

The 2022 environment can be used to probe core NumPy/NetCDF and batch plotting workflows. It cannot satisfy today's `visualization/map_explorer/requirements.txt` (`panel>=1.5`, `bokeh>=3.5`) without mixing in post-2022 releases. Treat that as an intentional compatibility boundary, not as a successful test of the current Explorer.

## Validation status (2026-11-27)

The 2024 profile was installed in a temporary CPython 3.12.3 environment on macOS arm64; `pip check` passed. Synthetic NetCDF/GeoTIFF round trips, a headless Matplotlib render with the CaMa-Flood `shade_rainbow` palette, Mekong `params.nml` parsing, a Tutorial 11 NetCDF read, and native-pixel-verified conversion of Mekong `uparea.nc` to a temporary COG passed.

The 2022 profile was exercised in a temporary CPython 3.10.8 environment. All pinned packages except Rasterio were installed, and the PyPI `lmoments3` 1.0.4 wheel was installed by its immutable file URL because its filename version (`1.0.4.post1`) disagrees with its internal metadata (`1.0.4`) and index resolution rejects the pin. `pip check` passed for the installed subset. NumPy/NetCDF round trips, metadata parsing, Tutorial 11 xarray reading, a headless palette render, and the Mekong river-point information script passed. The full profile could not install on this Apple Silicon host: PyPI provides no Rasterio 1.3.4 macOS arm64 wheel, and its source build requires build tooling and GDAL not available here. This does not establish 2022 compatibility for COG, Explorer, or other Rasterio workflows.

All temporary environments and outputs were under `/private/tmp/cmf-dependency-audit`; the repository `.venv` was unchanged. Exact commands, versions, successful checks, and limitations are recorded in [`python_dependency_audit.md`](../../docs/python_dependency_audit.md) and [VR-0261](../../research/records/validation_runs/VR-0261.md).
