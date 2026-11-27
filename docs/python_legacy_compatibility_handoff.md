# Historical Python Compatibility Handoff

**Evidence date:** 2026-11-27  
**Purpose:** Preserve the outcomes and limits of the completed historical
Linux compatibility experiments and document the narrow follow-up adopted in
the local source.

## Compatibility boundary

The oldest official β02 fallback remains the 2024 dependency profile.
Python 2022 and 2020 are experimental, manual-only probes; neither is selected
by `s02-python_setup.sh` or represents supported β02 installation. The
`cmf_colormap` distribution metadata remains `requires-python >=3.9` and
`matplotlib >=3.7`.

One source-level compatibility shim is applied in
`visualization/cmf_colormap/src/cmf_colormap/core.py`: import `files` from
`importlib.resources` when available, otherwise import it from
`importlib_resources`. The Python 3.8 experiment installed
`importlib-resources==4.1.1` separately and loaded the package from source.
This does not make ordinary package installation supported on Python 3.8,
does not change package metadata, and does not add a dependency to the project.

## Completed Cloud experiments

Cloud Codex completed the Docker experiments before this local follow-up. They
were run on a Linux amd64 host using these container environments:

The inspected Cloud source snapshot was commit
`1b500e7ea60e20d3a4ba4e14a626727c5211752d`. The current local worktree was used
for this change; the Cloud checkout was not merged or copied wholesale.

| Profile | Container | Python / OS | Native libraries noted |
|---|---|---|---|
| 2022 | `python:3.10.9-slim-bullseye` | CPython 3.10.9, Debian 11, glibc 2.31 | netCDF-C 4.9.0, HDF5 1.12.2, GDAL 3.5.3 |
| 2020 | `python:3.8.7-slim-buster` | CPython 3.8.7, Debian 10, glibc 2.28 | netCDF-C 4.7.4, HDF5 1.12.0, GDAL 2.4.4 |

Both completed profiles passed `pip check`, core NetCDF and ordinary GeoTIFF
I/O, and selected Mekong map and runoff checks. The Cloud checks also
confirmed the CMF Colormaps source import; Python 3.8 required the backport.
Six sampled palette RGBA arrays and decoded `shade_rainbow` PNG pixels matched
between the two profiles. These checks are software and selected data-I/O
evidence, not hydrological or model-output validation.

The 2020 baseline needed this PyYAML workaround in its isolated environment:

```sh
python -m pip install --no-cache-dir --no-build-isolation \
  --no-binary=pyyaml --global-option=--without-libyaml 'PyYAML==5.3.1'
python -c 'import yaml; assert not yaml.__with_libyaml__'
```

The separately run Python 3.8 colormap source-path probe additionally used:

```sh
python -m pip install 'importlib-resources==4.1.1'
```

It did not add the backport to a standard or historical requirements file.

## Tested direct dependency snapshots

These values identify the tested profile selection, not a complete lock of
transitive dependencies.

| Distribution | 2024 | 2022 | 2020 |
|---|---:|---:|---:|
| NumPy | 1.26.4 | 1.23.5 | 1.19.4 |
| netCDF4 | 1.7.2 | 1.6.2 | 1.5.5.1 |
| f90nml | 1.4.4 | 1.4.3 | 1.2 |
| pandas | 2.2.3 | 1.5.2 | 1.2.0 |
| xarray | 2024.11.0 | 2022.12.0 | 0.16.2 |
| SciPy | 1.14.1 | 1.9.3 | 1.5.4 |
| cftime | 1.6.4 | 1.6.2 | 1.3.0 |
| Matplotlib | 3.9.2 | 3.6.2 | 3.3.3 |
| Rasterio | 1.4.1 | 1.3.4 | 1.1.8 |
| tifffile | 2024.9.20 | 2022.10.10 | 2020.12.8 |
| tqdm | 4.67.1 | 4.64.1 | 4.55.0 |
| lmoments3 | 1.0.8 | 1.0.4* | 1.0.4* |
| PyYAML | 6.0.2 | 6.0 | 5.3.1** |
| cdsapi | 0.7.5 | 0.5.1 | 0.3.1 |
| Panel | 1.5.5 | 0.14.2 | 0.10.2 |
| Bokeh | 3.6.2 | 2.4.3 | 2.2.3 |
| Pillow | 11.0.0 | 9.3.0 | 8.0.1 |
| requests | 2.32.3 | 2.28.1 | 2.25.1 |
| Param | 2.1.1 | 1.12.3 | 1.10.0 |

`*` The same immutable PyPI wheel URL was used for `lmoments3` 1.0.4 in both
profiles because its wheel filename says `1.0.4.post1` while its internal
metadata says `1.0.4`:

```text
https://files.pythonhosted.org/packages/b6/83/6649731d9b30b937d65dc7eee7aa017311aed58bee0628f07304bbe33d8b/lmoments3-1.0.4.post1-py3-none-any.whl#sha256=137194c637bde5c99afe943e25b8f542f871620768f662cadb17dc212113f426
```

`**` PyYAML 5.3.1 was built without its optional LibYAML extension in the
2020 profile. The direct pins for the official 2024 profile and experimental
2022 and 2020 profiles are maintained in `config/python/requirements_2024.txt`,
`config/python/requirements_2022.txt`, and
`config/python/requirements_2020.txt`, respectively. These are tested direct
dependency selections, not complete transitive locks. The 2020 profile also
requires the separate pure-Python PyYAML installation procedure and optional
backport probe documented in [`config/python/README.md`](../config/python/README.md).

## Findings deliberately left out of scope

- The 2020 Matplotlib 3.3.3 release lacks the current `matplotlib.colormaps`
  registry API. Global colormap registration was not adapted.
- Historical Panel/Bokeh do not meet current Map Explorer bounds; Explorer
  compatibility is not established for either historical profile.
- GDAL 2.4.4 in the 2020 Rasterio environment lacks the COG driver.
- The normal installed `cmf_colormap` package remains unavailable below its
  declared Python/Matplotlib minimums, even though the source import path was
  probed under Python 3.8.
- No Fortran rerun, model-output regression, hydrological equivalence,
  calibration, or conservation test was part of these experiments.

These are deferred compatibility questions rather than reasons to expand
β02's official support matrix. See the [dependency audit](python_dependency_audit.md)
for earlier macOS evidence and the distinction between that evidence and the
Cloud Linux results.
