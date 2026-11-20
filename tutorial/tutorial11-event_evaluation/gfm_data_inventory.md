# Rhine 2021 GFM: one-day acquisition test

Execution date: 2026-11-20 (JST). Satellite acquisition timestamps are UTC.

## Scope and change of strategy

The initial 13–20 July 2021 run was interrupted after approximately 30 minutes
without completed GeoTIFF outputs. It was a long-running processing attempt,
not an established authentication failure. Its log did not expose item-level
progress because the default CLI disables the Atlantis library logger.
The catalogue search itself succeeded: 125 tiled products at 73 distinct exact
timestamps across the eight dates. These are not independent orbital-pass counts.

The maintainer changed the initial test to **2021-07-15 only**, retaining the
original **5.6–10.0°E, 49.5–52.9°N** box. The eight-day acquisition was not
restarted. No Atlantis source modification, large optimisation or model
comparison is part of this task.

All external source, Pixi installation/environment/cache, downloaded data,
intermediates, run logs and inspection scripts are managed in:

```text
/Users/yamadai/work/Atlantis/
  source/                       # pinned external Atlantis checkout and .pixi env
  pixi/                         # standalone Pixi executable and cache
  scripts/                      # acquisition, resource monitor and inspection
  archive/eight_day_attempt/    # preserved first-attempt logs/catalogue/draft
  data/Rhine_2021_test/         # one-day outputs, metadata, logs and caches
  figure/                       # local inspection figures
```

On this workstation the requested path resolves to
`/Volumes/work06_P32_84T/work_06/Atlantis/`; these are two paths to the same
directory, not independent copies. Tutorial 11 retains documentation,
reproduction instructions and selected small figures only. Raw/intermediate
data and installed dependencies are not added to Git. Original discharge
observations remain unchanged.

## Version, installation and exact invocation

The current official repository is [opageo/atlantis](https://github.com/opageo/atlantis),
not the historical ECMWFCode4Earth URL. Inspected commit:
**9371dc4fc421949caf9a2a8eb03e5fb962872820**, installed version
**0.1.0rc3.dev2+g9371dc4fc**.

The pinned [README](https://github.com/opageo/atlantis/blob/9371dc4fc421949caf9a2a8eb03e5fb962872820/README.md),
[CLI](https://github.com/opageo/atlantis/blob/9371dc4fc421949caf9a2a8eb03e5fb962872820/docs/cli.md),
[GFM overview](https://github.com/opageo/atlantis/blob/9371dc4fc421949caf9a2a8eb03e5fb962872820/docs/gfm/overview.md),
[GFM pipeline](https://github.com/opageo/atlantis/blob/9371dc4fc421949caf9a2a8eb03e5fb962872820/docs/gfm/pipeline.md)
and [Pixi setup](https://github.com/opageo/atlantis/blob/9371dc4fc421949caf9a2a8eb03e5fb962872820/docs/pixi-setup.md)
were reviewed against implementation. The recommended locked Pixi environment
keeps the GDAL/HDF4 stack separate from CaMa-Flood. No shared Python or existing
tutorial environment was changed. Generic multi-source credential setup was not
run. This GFM backend uses anonymous public EODC STAC/COG HTTP access; an actual
COG Range request returned HTTP 206.

| Component | Tested version |
| --- | --- |
| Pixi | 0.84.2 |
| Python | 3.14.8, conda-forge |
| Host | macOS 13.7.8, arm64 |
| Rasterio / GDAL | 1.5.2 / 3.13.3 |
| NumPy / xarray | 2.5.4 / 2026.9.0 |

The README badge is not the installation constraint: the pinned pyproject
specifies Python >=3.12,<3.15. The lock SHA-256 is
`93f45edf29077f85dfba596ba2036765eaa41c816a1f7c183249648d3fb43ef3`.

To reproduce the dedicated workspace after installing standalone Pixi there:

```bash
cd /Users/yamadai/work/Atlantis
git clone https://github.com/opageo/atlantis source
git -C source checkout 9371dc4fc421949caf9a2a8eb03e5fb962872820
export PIXI_HOME="$PWD/pixi"
export PIXI_CACHE_DIR="$PWD/pixi/cache"
export PIXI_NO_TELEMETRY=1
./pixi/bin/pixi install --manifest-path source/pixi.toml --locked -e default --no-config
export ATLANTIS_CACHE_DIR="$PWD/data/Rhine_2021_test/cache"
export MPLCONFIGDIR="$ATLANTIS_CACHE_DIR/matplotlib"
./pixi/bin/pixi run --manifest-path source/pixi.toml --locked --no-config \
  atlantis --verbose fetch \
  --event Rhine_2021_test --source gfm --bbox "5.6 49.5 10.0 52.9" \
  --start-date 2021-07-15 --end-date 2021-07-15 \
  --strategy all --harmonise --plot --gfm-persist-diagnostics \
  --output "$PWD/data/Rhine_2021_test"
```

Do not clone over the existing checkout. The local
`scripts/run_gfm_20210715.sh` additionally saves the exact backend catalogue and
runs the same command through a standard-library resource monitor. CURL verbose
headers instrument the COG transfer; no range/cache tuning is applied. The
existing eight-day scripts are historical and must not be executed for this test.
`--verbose` is a global option **before** `fetch`. `--harmonise` selects the
canonical 1/60-degree grid at this commit; no extra resolution option is needed.

## Catalogue and observation times

The full original search contains **14 tiled products on 2021-07-15**, at these
**10 exact UTC timestamps**:

| UTC time | Tile products | Catalogue bbox clipped to request (W/S/E/N, degrees) |
| --- | ---: | --- |
| 05:49:37 | 2 | 5.6000, 51.3288, 10.0000, 52.9000 |
| 05:50:02 | 2 | 5.6000, 51.3288, 10.0000, 52.9000 |
| 05:50:27 | 2 | 5.6000, 49.5000, 9.5905, 52.9000 |
| 05:50:52 | 1 | 5.6000, 49.5000, 9.5905, 51.8223 |
| 05:51:17 | 1 | 5.6000, 49.5000, 9.5905, 51.8223 |
| 16:59:44 | 1 | 8.8458, 49.5000, 10.0000, 51.9522 |
| 17:00:09 | 1 | 8.8458, 49.5000, 10.0000, 51.9522 |
| 17:00:34 | 2 | 8.4465, 49.5000, 10.0000, 52.9000 |
| 17:00:59 | 1 | 8.4465, 51.8223, 10.0000, 52.9000 |
| 17:01:24 | 1 | 8.4465, 51.8223, 10.0000, 52.9000 |

The fresh one-day query independently confirmed these counts. The backend
item cap was not reached. The local complete catalogue, rather than a truncated
first-page response, is the source of this inventory.

Adjacent tiled products can share timestamps. These counts do not establish
10 independent overpasses. Monthly/reference-water asset filenames can include
historical reference intervals; those are not additional event acquisition
dates. The timestamp list uses the item datetime metadata.
Catalogue tile footprints indicate potential
intersection, not valid SAR pixels. Exact item IDs and footprint intersections
are preserved locally in `stac_items.json` and `acquisition_footprints.csv`.
`strategy all` produces a **daily composite**, combining multiple timestamps,
not separate rasters for every time. Its flood distribution is not a snapshot
of the flood peak at one instant.

## Data definitions and spatial resolution

The selected metadata describe **20 m** native sampling on 15,000 × 15,000
**Equi7 Europe Azimuthal Equidistant** tiles, GFM v3.1.0 / archive software V02,
processed in 2024. This is reprocessed historical imagery, not evidence of what
was available in real time in 2021.

The catalogue has ensemble and individual DLR/LIST/TUW flood/likelihood layers,
reference water, exclusion mask, advisory flags, thumbnail and tilejson.
The default run uses six bands: ensemble flood extent, ensemble water extent,
reference water mask, exclusion mask, ensemble likelihood and advisory flags.
Individual-algorithm outputs are not requested.

| Native layer | Meaning in the inspected implementation |
| --- | --- |
| Ensemble flood extent | 0: not classified flooded; 1: flood; 255: nodata |
| Ensemble water extent | 0: not water; 1: water; 255: nodata |
| Reference water mask | 0: none; 1: permanent; 2: seasonal; 255: nodata |
| Exclusion / advisory / likelihood | Companion quality information; not a dry-land classification |

Reference-water codes above follow the pinned [layer definitions](https://github.com/opageo/atlantis/blob/9371dc4fc421949caf9a2a8eb03e5fb962872820/src/atlantis/fetchers/gfm/layers.py);
a summary table in upstream documentation has the two water codes reversed.
The [provider layer guide](https://extwiki.eodc.eu/GFM/PUM/Products) and
[recommendations](https://extwiki.eodc.eu/GFM/PUM/Recommendations) explain why
exclusions and advisory flags require separate consideration. Current provider
documentation is context, not a replacement for versioned item metadata.

Default coarsening is factor four (nominal 80 m), followed by geographic-grid
processing and **1-arcmin EPSG:4326** harmonisation. Atlantis accumulates flood
and water support and valid support, defining a native contribution as valid
when **either flood or water is not 255**. Reference water alone does not prove
SAR observation. Flood fraction is flood support / valid support; it is not
flooded area divided by the whole geographical target-cell area. Water-only
valid support can enter this denominator. No additional quality threshold is
imposed in this initial test.

Fraction files store integer **0–100 percent**, **nodata 255**. A 0% result can
include a small positive fraction rounded to zero, so it does not prove that
all contributing native pixels were dry. Diagnostics store floating support
counts (nodata -9999), not numbers of whole independent observations or a
physical valid-area fraction. No missing observation is interpolated or changed
to zero in the inspection plots.

## Measured run and output inspection

**PASS: the unchanged full box completed successfully (exit 0).**
Run interval: **2026-11-20 18:14:20–18:30:15 JST**. Wall time was
**955.06 s (15 min 55 s)**, including CLI startup, GFM processing, plots and
harmonisation; environment preparation and the separate catalogue query are
not included. The final checklist records all 14 items processed and one date
plotted/harmonised. No HTTP 4xx/5xx response was recorded.

| Measurement | Observed result |
| --- | --- |
| Distinct native COG URLs opened | 74 (84 HEAD opens, including repeated references) |
| Successful COG byte-range GET responses | 10,882 |
| Compressed COG response payload | **440,598,472 bytes (420.19 MiB)** |
| Sum of unique complete source-file sizes | 292,159,649 bytes (278.63 MiB) |
| OS waited-child `ru_maxrss` | **12,915,277,824 bytes (12.03 GiB)** |
| One-second sampled peak process-tree RSS sum | 11,815,632 KiB (11.27 GiB) |

COG payload is summed from successful HTTP 206 **Content-Range lengths** and
matches requested byte ranges. It includes repeated reads but excludes HEAD
body lengths, TLS/HTTP headers and catalogue traffic; it is not a NIC byte
counter or an uncompressed-array size. HTTP/2 requests interleave, so pairing
responses with the most recent outgoing request would undercount transfer;
the final inspection instead totals all successful single-range responses.
The larger-than-unique-file transfer reflects repeated range access. Native
COGs were streamed by range, not saved as 74 complete original TIFF files.

RSS is not unique physical memory. The sampled sum may double-count shared
pages and miss sub-second peaks; the OS counter is reported separately. The
resource record is `logs/run_metrics.json`, and CURL evidence is retained in
`logs/atlantis_fetch.log`. The large RSS occurred with processing/plotting
enabled; no experiment isolating individual stages was run.

### Local output structure and sizes

| Output group | Files | Bytes |
| --- | ---: | ---: |
| `gfm/processed/` | 9 LZW GeoTIFFs | 18,608,416 |
| `gfm/harmonised/` | 9 LZW GeoTIFFs | 49,702 |
| `gfm/plots/processed/derived/` | 9 PNGs | 1,132,397 |
| `gfm/plots/harmonised/derived/` | 9 PNGs | 562,005 |
| **Total GFM outputs** | **36** | **20,352,520** |

Metadata, logs, cache and local inspection figures are additional files outside
these totals. Full per-file metadata/sizes are in the local
`inspection_summary.json`. The catalogue/footprint CSV and run logs are retained
outside Git.

Processed TIFF names use `Rhine_2021_test_20210715_gfm_<layer>.tif`.
Harmonised names use `Rhine_2021_test_2021-07-15_gfm_<layer>_harmonised.tif`,
except the main flood-fraction file, named
`Rhine_2021_test_2021-07-15_gfm_harmonised.tif`. The distinction between
`YYYYMMDD` and `YYYY-MM-DD` was checked against actual output, not inferred.

| Layer | Processed bytes | Harmonised bytes | Stored type / nodata |
| --- | ---: | ---: | --- |
| `flood_fraction` | 893,536 | 2,695 | uint8 / 255 |
| `water_fraction` | 1,187,311 | 6,459 | uint8 / 255 |
| `reference_water` | 749,800 | 1,711 | uint8 / 255 |
| `exclusion_mask` | 1,950,302 | 4,152 | uint8 / 255 |
| `advisory_flags` | 888,300 | 2,345 | uint8 / 255 |
| `ensemble_likelihood` | 6,288,504 | 13,112 | uint8 / 255 |
| `ensemble_flood_extent_count` | 1,318,455 | 4,886 | float32 / -9999 |
| `ensemble_water_extent_count` | 2,501,468 | 5,027 | float32 / -9999 |
| `valid_count` | 2,830,740 | 9,315 | float32 / -9999 |

### Grid, signal and missing observations

The processed geographic grid is **6,123 columns × 4,732 rows**, with spacing
about 0.00071864894° and bounds
(5.59971254, 49.49982034, 10.0, 52.90046712). It is the nominal 80 m processing
stage, not a saved native 20 m tile. The harmonised grid is **264 × 204**,
**EPSG:4326**, spacing **1/60°** in both axes, bounds **5.6, 49.5, 10.0, 52.9**.
Its pixel edges align with the canonical global grid. These are angular cells,
not square 1.85 km cells everywhere.

| Main 1-arcmin flood-fraction raster | Cells |
| --- | ---: |
| Total | 53,856 |
| Some valid classified input | **23,721 (44.045%)** |
| Nodata 255 | **30,135 (55.955%)** |
| Valid, rounded fraction 0% | 23,427 |
| Valid, fraction >0% | **294** |

The displayed flood fraction ranges from **0 to 45%**. Positive cells are sparse
within the predominantly western observed swath; the eastern part of the box
is largely unobserved. These classifications are not independent ground-truth
verification of each flooded feature. Grid-cell percentages above are not
physical-area fractions. The green coverage figure means **some contributing
valid input**, not complete observation of every native pixel or quality-cleared
usable area. Validity uses the flood-or-water rule described above.

The processed flood mask exactly matches `valid_count > 0`, and its saved
percentages match the rounded diagnostic support ratio. **437 processed cells**
have positive flood support that rounds to 0%; this demonstrates why white
zero-valued cells cannot be interpreted as proof of no native flood pixels.
Nodata was kept separate throughout inspection and plotting.

Companion masks have different support: the harmonised exclusion/advisory
rasters each have 24,051 non-nodata cells. Exclusion codes are 0 in 10,868 cells
and 1 in 13,183; advisory codes are 0 in 23,749 and 2 in 302. They are displayed
as **stored codes**, not converted to cell-area fractions or silently merged
into the observation mask. Version-specific bit interpretations and an
appropriate quality-screening policy remain for future work.

### Diagnostic-count limitation discovered

**Do not reconstruct harmonised flood fractions or observation masks from the
saved harmonised count TIFFs in this Atlantis version.** The processed
`ensemble_flood_extent_count` has 19,950 positive cells (maximum 1.917366), but
its harmonised counterpart is **zero in all 53,856 cells**, even though the
main harmonised flood-fraction raster has 294 positive cells. Harmonised
`valid_count` is also rounded (only 0/1 here), with 23,878 positive cells rather
than the main fraction's 23,721 non-nodata cells.

Source inspection identifies integer rounding of non-fraction arrays in
[`write_harmonised_raster`](https://github.com/opageo/atlantis/blob/9371dc4fc421949caf9a2a8eb03e5fb962872820/src/atlantis/harmoniser/__init__.py),
even when diagnostics are ultimately written as float32. Thus float32 storage
does not preserve their fractional support. The main fraction is resampled
separately and must not be declared zero from that diagnostic file. The
processed support checks passed; harmonised ratios are not asserted equivalent
to processed diagnostic ratios. No Atlantis source was changed.

For a subsequent task, preserve diagnostic floats through harmonised export
and verify masks/counts before using them quantitatively. Until then, retain
the processed diagnostics for traceability. This is a proposed follow-up,
not an implemented fix.

### Selected visual inspection

Both selected PNGs were opened and inspected. Geographic axes, common map
extent, legible labels/colorbars and separate grey nodata were checked; the
main-map text bounds were checked at the actual export DPI. No temporal
interpolation or image smoothing is applied by the inspection script.

- [Daily flood fraction and valid-input coverage](figure/gfm_2021-07-15_1arcmin.png)
- [Stored exclusion/advisory codes](figure/gfm_2021-07-15_quality_1arcmin.png)

The local inspection can be repeated without any further downloads:

```bash
cd /Users/yamadai/work/Atlantis
export PIXI_HOME="$PWD/pixi" PIXI_CACHE_DIR="$PWD/pixi/cache"
export MPLCONFIGDIR="$PWD/data/Rhine_2021_test/cache/matplotlib"
./pixi/bin/pixi run --manifest-path source/pixi.toml --locked --no-config \
  python scripts/inspect_gfm_day.py
```


## Repository sample

At the maintainer's request, [gfm_sample/](gfm_sample/README.md) now contains
unchanged copies of the six small harmonised science/quality TIFFs (30,474 bytes),
a provenance/interpretation README and SHA-256 manifest. Source/copy hashes and
GeoTIFF grids/masks were checked. Rounded count diagnostics, processed rasters,
raw COGs, logs, caches and environments are excluded from this repository sample.
Provider data rights remain distinct from software licensing; inclusion does
not assign a new data licence. Full processing still needs the external bundle.

## Suitability and unresolved issues

**The one-day acquisition test succeeded and is suitable for initial visual
inspection of observed portions of the domain. It is not yet sufficient for
quantitative evaluation of the event's peak inundation across the Rhine box.**
Over half the target cells lack valid fraction output, the daily composite
combines multiple times, quality screening is unresolved, and the harmonised
count-export limitation above must be handled. Only July 15 pixels were
inspected; catalogue presence on July 14/16 does not establish usable coverage
on those dates.

The acquisition has stopped after this single day. The original box was not
shrunk, the eight-day run was not resumed, no model metrics were implemented,
and no scientific source input or Atlantis source was modified.

This regional box includes Lobith but excludes Maxau and Speyer south of
49.5°N. It is not the whole Rhine basin. SAR geometry, urban/vegetated areas,
exclusions, advisory flags and temporal sampling limit interpretation; aggregation
to 1 arcmin cannot recover unresolved tributary inundation. Model total-water
and observed flood-only definitions need reconciliation before evaluation.
No metrics or evaluation design have been implemented.

**Knowledge-gap review:** Current repository/CLI, native code meanings,
denominator and daily grouping were resolved from source. Per-acquisition
valid-pixel footprints are not retained separately by this daily-composite CLI;
independent pass IDs and event-specific quality screening remain unresolved.
Full-window July 14–16 availability cannot be established from this one-day
pixel inspection. Dataset attribution/redistribution terms should be checked
separately from the software Apache-2.0 licence. Large/raw outputs stay outside
Git. These issues concern subsequent evaluation and do not justify treating
unobserved pixels as dry.
