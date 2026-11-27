# CaMa-Flood v5 Python Dependency Audit

**Date:** 2026-11-27  
**Worktree:** `feature/package-builder` at `c42e99d` (local `origin/feature/package-builder` matched; fetch was blocked by filesystem permission)  
**Scope:** maintained Python imports, current declarations, historical release availability, and the limited checks possible on this macOS arm64 host.

## Summary

The root requirements cover the core numerical, NetCDF and visualization stack. The code directly imports three additional distributions that are not explicitly declared there: `Pillow` (as `PIL`), `requests`, and `param`. Pillow and requests currently arrive transitively in the inspected environments; relying on that is fragile. The Map Explorer has its own requirements file, so its direct `Pillow` and `param` dependencies should be declared there as well. The root requirements are amended to name these packages explicitly.

No lowered minimum is supported by a runtime matrix. Current root lower bounds are therefore retained. The 2024 direct-pin profile installed and passed focused checks on macOS arm64/CPython 3.12.3. The 2022 profile was partially installed and checked on CPython 3.10.8; its Rasterio pin could not be built on this Apple Silicon host, so Rasterio-dependent compatibility remains unverified.

## Dependency survey

`Required` means imported by an active, maintained workflow; `Optional` means a supported, separable feature. “Code minimum” is left unverified where API inspection does not establish a reliable lowest version. The lower bounds are existing project constraints, not proof of the smallest working release.

| Package | Maintained use | Required / optional | Current constraint | Code-based minimum | Evidence/status |
|---|---|---|---|---|---|
| NumPy | `map/tools`, runoff processing, plots, Explorer, tutorials | Required | `>=1.24`; Explorer `>=1.26,<3` | Unverified | Array operations and dtype/shape handling; existing .venv NumPy 1.26.4 passed focused operations. Explorer's combined requirements effectively require >=1.26. |
| netCDF4 | Map I/O, model outputs, tutorials, Explorer | Required | `>=1.6`; Explorer `<2` | Unverified | `Dataset`, variables, attributes and time conversion APIs; installed 1.6.5 passed synthetic roundtrip and a Tutorial 11 file read. |
| f90nml | `map/tools` and metadata parsing | Required | `>=1.4` | Unverified | `read` of current `params.nml` passed with 1.5.0; no older version tested. |
| pandas | tabular discharge, allocations and analysis | Required for relevant workflows | `>=1.5` | Unverified | Direct use in analysis scripts; DataFrame operation passed in existing .venv. |
| xarray | runoff NetCDF and tutorial analysis | Required for relevant workflows | `>=2023.1` | Unverified | Dataset I/O/data-array operations; read a Tutorial 11 monthly output in existing .venv. |
| SciPy | One script under `map/src/src_dam/script` | Optional / scope boundary | `>=1.10` | Unverified | `scipy.signal.argrelmax`; source is outside normal `map/tools` pipeline and was not executed. Retained pending owner confirmation. |
| cftime | NetCDF calendar interoperability | Supporting/optional | `>=1.6` | Unverified | Often used by netCDF4 time conversion; no direct maintained import found. Kept due model-calendar I/O path. |
| Matplotlib | Static maps, graphs, export | Required | `>=3.7`; Explorer `>=3.8,<4` | Unverified | Plotting APIs and bundled CMF Colormaps; PNG creation passed with Matplotlib 3.11.2. |
| Rasterio | COG, high-res rasters, Tutorial 11, Explorer | Optional by component; required for those workflows | `>=1.3`; Explorer `>=1.4,<1.5` | Unverified | Raster read/write/window/warp APIs; GeoTIFF roundtrip passed with 1.4.1. macOS arm wheel constraints are platform/version-specific. |
| tifffile | No active direct import found | Unclear / potentially optional | `>=2023.7` | Unverified | Retained in root because absence from import search alone does not prove no user workflow; no maintained call site found in scoped files. |
| tqdm | No active direct import found | Unclear / potentially optional | `>=4.65` | Unverified | Retained pending workflow-owner review. |
| lmoments3 | No active direct import found in maintained paths; root comment names levee-height workflow | Optional / needs confirmation | `>=1.0` | Unverified | Existing declaration retained; an older levee workflow under `etc/` was not promoted into active v5 scope. |
| PyYAML | No active direct import found in scoped paths | Unclear / potentially optional | `>=6.0` | Unverified | Root comment mentions remapping configuration; no `yaml` import/call located in maintained Python. Retained pending workflow-owner confirmation. |
| cdsapi | ERA5-Land download script (guarded import) | Optional | `>=0.7` | Unverified | Download path gives a clear missing-package diagnostic; credentials/terms are external. |
| Panel | Map Explorer GUI | Optional by component | `>=1.5,<2` | Project boundary: 1.5 | Current requirement is explicit; older Panel 0.14.2 belongs to the 2022 profile and is outside supported current Explorer range. |
| Bokeh | Map Explorer plot/widgets | Optional by component | `>=3.5,<4` | Project boundary: 3.5 | Current requirement is explicit; 2022 Bokeh 2.4.3 is outside supported current Explorer range. |
| Pillow (`PIL`) | River map/output composition, Explorer and Tutorial 11 | Required for those image workflows | Missing from root; indirect in current resolved environments | Unverified | Direct imports found. Explicitly added without inventing a minimum version to avoid relying on Matplotlib/Panel transitive dependencies. |
| requests | Tutorial 11 GFM acquisition | Optional by tutorial feature | Missing from root; currently available transitively | Unverified | Direct `requests` import in `event_gfm_download.py`; explicitly added to root requirements without asserting an unverified minimum. |
| param | Explorer widgets/parameters | Optional by component | Missing from Explorer file; Panel transitive | Unverified | Direct import in Explorer modules; explicitly declared (`>=2.1,<3`) in root and Explorer requirements. |

Python standard-library imports (for example `pathlib`, `csv`, `argparse`, `subprocess`, `json`, `typing`) are not third-party requirements. Local `cmf_colormap` is a repository package installed from `visualization/cmf_colormap/`, not a PyPI dependency.

## Version and platform findings

- NumPy 2.0 was released on 2024-06-16 and changed the C ABI. The 2024 snapshot intentionally uses NumPy 1.26.4 and compatible-era binary packages. [NumPy 2.0 release notes](https://numpy.org/devdocs/release/2.0.0-notes.html)
- Rasterio 1.4.1, released 2024-10-01, published CPython 3.12 macOS arm64 wheels. Rasterio 1.3.4 (the 2022-era selection) has no macOS ARM64 wheel listed on PyPI; source build may require a GDAL development setup. [Rasterio 1.4.1 files](https://pypi.org/project/rasterio/1.4.1/#files), [Rasterio 1.3.4 files](https://pypi.org/project/rasterio/1.3.4/#files)
- The historical 2024 pins are all dated no later than 2024-12-31. Examples: netCDF4 1.7.2 (Oct 22), xarray 2024.11.0 (Nov 22), Bokeh 3.6.2 (Dec 3), Panel 1.5.5 (Dec 18). [netCDF4 1.7.2](https://pypi.org/project/netCDF4/1.7.2/), [xarray 2024.11.0](https://pypi.org/project/xarray/2024.11.0/), [Bokeh 3.6.2](https://pypi.org/project/bokeh/3.6.2/), [Panel 1.5.5](https://pypi.org/project/panel/1.5.5/)
- The 2022 profile uses CPython 3.10 because it was supported by the pinned-era NumPy, Panel and Bokeh releases. Panel 0.14.2 and Bokeh 2.4.3 cannot satisfy today's current Map Explorer constraints; the 2022 profile does not claim current Explorer compatibility. [Panel 0.14.2](https://pypi.org/project/panel/0.14.2/), [Bokeh 2.4.3](https://pypi.org/project/bokeh/2.4.3/)
- Minimum package versions inferred solely from visible API names would be misleading. The profiles demonstrate release-date candidates, not minimums. A proper verified minimum requires installing old candidates and running the same focused workflow checks.

## Compatibility experiment

Network access was enabled for isolated installs. Temporary environments and all test outputs were kept under `/private/tmp/cmf-dependency-audit`; the repository `.venv` and system Python were not modified.

| Test | Existing root `.venv` | 2024 profile: CPython 3.12.3 | 2022 profile: CPython 3.10.8 |
|---|---|---|---|
| Install / resolution | Existing environment only | PASS: all pins installed, with local `visualization/cmf_colormap`; netCDF4 built from sdist, Rasterio used macOS arm64 wheel | PARTIAL: all pins except Rasterio installed. Rasterio 1.3.4 has no macOS arm64 wheel; sdist build failed (first missing `pkg_resources`, retry missing Cython; host has no `gdal-config`). lmoments3 1.0.4 required its official PyPI wheel URL because filename `.post1` conflicts with internal metadata version 1.0.4. |
| `pip check` | PASS | PASS | PASS for installed subset; Rasterio absent |
| Direct imports / versions | PASS on existing environment | PASS for all pinned distributions | PASS for installed pins; excludes Rasterio |
| Synthetic NetCDF read/write | PASS | PASS, exact values | PASS, exact values |
| Synthetic GeoTIFF read/write | PASS | PASS, exact values | NOT RUN: Rasterio unavailable |
| NumPy/pandas/xarray/SciPy | PASS basic operations | PASS via profile imports and downstream checks | PASS via profile imports and downstream checks |
| Matplotlib + CMF `shade_rainbow` | PASS | PASS headless PNG | PASS headless PNG from repository source; local package metadata requires Matplotlib>=3.7 and therefore was not installed as a package in this 3.6.2 profile |
| Map metadata | PASS | PASS on Mekong `params.nml` (80 × 120 × 10) | PASS on same map |
| Tutorial 11 model output | PASS | PASS xarray read: `outflw`, 744 time records | PASS xarray read: `outflw`, 744 time records |
| Representative CaMa map utility | Not part of earlier selected subset | COG converter's registered conversion function passed on Mekong `uparea.nc`; native pixels verified, TIFF written to temp | `analysis_river_point_info.py --map-dir map/mekong_15min xy 19 6` passed with the NetCDF map and reported one-based cell `(19,6)` |
| Current Explorer | Existing focused tests: 15 passed/1 deselected; broader exploratory tests 34 passed/3 existing test/data assumption failures | Not tested as current UI integration | Unsupported by declared current bounds: Panel 0.14.2/Bokeh 2.4.3 vs Panel>=1.5/Bokeh>=3.5 |

A CLI-level COG planner attempt did not resolve the registered source filename; the dependency exercise therefore called the converter's registered `convert` operation directly. This is an existing utility/planner issue outside the audit scope and was not changed. The passing conversion confirms the 2024 NetCDF/Rasterio/GDAL API path for the tested Mekong file, not the CLI planner.

The existing root `.venv` results are modern-environment checks and are not substituted for these historical profile outcomes. The 2022 evidence covers core numerical, metadata, NetCDF and map-analysis paths only; it does not cover COG, high-resolution raster, or current Explorer behavior.

## Recommendations

1. Keep current minimums unchanged pending actual lowest-version tests.
2. Declare `Pillow`, `requests`, and `param` explicitly because maintained code imports them directly. `Pillow` and `param` are added to the Explorer-specific requirements too.
3. Do not remove the currently declared `scipy`, `tifffile`, `tqdm`, `lmoments3`, `PyYAML`, or `cftime` in this audit; scope search did not prove their absence from all user workflows, and root comments identify some as optional/maintained features.
4. Do not add automatic fallback to `requirements_2024.txt` in `s02-python_setup.sh`. A profile whose installation and representative workflow have not been tested is not a validated fallback, and a failed pip run may leave a partially updated environment.
5. Before enabling fallback, perform clean-install tests for current and 2024 profiles on each supported OS/CPU combination and record resolution, `pip check`, runtime, and recovery behavior. A separate GDAL-capable platform is needed to complete the 2022 Rasterio checks.

Historical profiles constrain direct dependencies, not all transitives. The tested 2024 paths have focused evidence on this macOS arm64 host; the partial 2022 results are not full profile certification. Neither profile establishes general cross-platform support.
