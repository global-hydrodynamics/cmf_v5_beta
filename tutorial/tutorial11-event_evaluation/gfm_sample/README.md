# Rhine 2021: small GFM inundation sample

Six unchanged harmonised GeoTIFFs, **30,474 bytes in total**, retained for
initial data inspection. This is a daily satellite-derived composite, not a
CaMa-Flood simulation, an instantaneous flood-peak map or native 20 m data.

## Provenance and grid

- Source: Copernicus Global Flood Monitoring (GFM), Sentinel-1 SAR; public
  [EODC STAC](https://stac.eodc.eu/api/v1) collection `GFM` and its COG assets.
- Observation date: **2021-07-15 UTC**, combining 14 tile products at 10 exact
  timestamps. This does not mean 10 independent orbital passes.
- Product metadata: GFM v3.1.0 / archive software V02, reprocessed in 2024.
- Tool: [opageo/atlantis](https://github.com/opageo/atlantis), commit
  `9371dc4fc421949caf9a2a8eb03e5fb962872820`
  (`0.1.0rc3.dev2+g9371dc4fc`), acquired on 2026-11-20.
- Event identifier: `Rhine_2021_test`; original native sampling approximately
  20 m, default coarsening factor four, then 1-arcmin harmonisation.
- Grid: **264 columns × 204 rows**, EPSG:4326, 1/60-degree spacing; bounds
  **5.6–10.0°E, 49.5–52.9°N**. Rows run north to south.
- All six files: single-band uint8, LZW GeoTIFF, **nodata = 255**.

The complete procedure, timestamp list, processing definitions, measured load
and limitations are in [the acquisition inventory](../gfm_data_inventory.md).

## Files

All names start with `Rhine_2021_test_2021-07-15_gfm`.

| Filename suffix | Meaning | Actual valid values in this sample |
| --- | --- | --- |
| `_harmonised.tif` | Main flood fraction, integer percent | 0–45 |
| `_water_fraction_harmonised.tif` | Water fraction, integer percent | 0–100 |
| `_reference_water_harmonised.tif` | Reference-water codes | 0, 1 |
| `_exclusion_mask_harmonised.tif` | Stored exclusion-mask codes | 0, 1 |
| `_advisory_flags_harmonised.tif` | Stored advisory bitmask | 0, 2 |
| `_ensemble_likelihood_harmonised.tif` | Ensemble likelihood, not flood fraction | 0–46 |

Reference codes in the pinned implementation are 0: none, 1: permanent,
2: seasonal; code 2 is absent from this harmonised sample. Quality codes are
stored as produced by Atlantis. Their nearest-neighbour representation does
not give the excluded fraction of a target cell. Interpret bit meanings using
version-specific provider documentation.

## Missing observations and interpretation

The main fraction has 23,721 cells with some valid classified input, 30,135
nodata cells and 294 positive-fraction cells. **Never turn 255 into zero.**
A 0% value can include a small positive fraction rounded to zero and does not
prove every native pixel was dry. Support in the processed derivation uses
validity of either the flood or water band; a populated reference-water or
quality layer is not proof of a valid flood observation. Layer masks differ.

Harmonisation spatially resamples the processed fractions; it cannot restore
unobserved areas or narrow features. Daily grouping combines acquisition times.
This small sample alone is insufficient for evaluating event-wide peak extent.
No additional interpolation or smoothing was applied when copying these files.

The three `*_count_harmonised.tif` diagnostics are deliberately excluded:
rounding in this Atlantis version loses fractional counts, including an all-zero
harmonised flood-count layer despite positive main flood fractions. The full
processed diagnostics and native data are not supplied here. The external full
inspection script needs the larger processed-data/log bundle; this sample is
for ordinary GeoTIFF readers, not a standalone complete processing environment.

## Integrity and data rights

`SHA256SUMS` records source/copy checksums. From this directory, verify with:

```bash
shasum -a 256 -c SHA256SUMS
```

The maintainer requested inclusion of these six small files. No new data
licence is assigned here. GFM-specific reuse, attribution and redistribution
conditions have not been independently established in this work; consult the
[provider documentation](https://extwiki.eodc.eu/GFM/PUM/Products). The Atlantis
software Apache-2.0 licence is not a satellite-data licence.
