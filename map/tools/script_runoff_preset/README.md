# Runoff climatology and grid-only coastal modification

This workflow creates a reusable runoff climatology **on the runoff product's
own grid**. It reads no river map, `diminfo`, Input Matrix or land/sea mask.
Mean runoff [mm/s] is later mapped to each river catchment by
[`s01-channel_params.sh`](../script_params/s01-channel_params.sh), whose mean
discharge drives channel-width/depth estimates. That later stage owns the
map-specific Input Matrix. Nothing here copies results into `map/data/`.

## Current canonical dataset

On 2026-11-16 the maintainer judged the reported differences acceptable and
manually copied the generated `.one` and `.nc` into `map/data/`. These files
are now the canonical ELSE_GPCC 1981–2010 climatology for future development.
Both copies were verified byte-identical to the generated products:

- Binary SHA-256: `7a5876df2934e87cb7db9ffd1ace38bc68d3f9268a7f6c3ba69c21db4108ae6a`
- NetCDF SHA-256: `4e0c5205fee14ec6ed102f239f71a070eb1f6a4beb62d961a7fbdc73ad6f981b`

This settles adoption of the new product; it does not establish independent
physical optimality of minimum-neighbor filling or recover the old provenance.
The workflow still never writes into `map/data/` automatically. Its default
comparison path now refers to this new canonical field. The comparison results
below describe the **former** reference, identified by its historical hash;
preserve those reports or supply an archived reference for that comparison.

## Standard workflow

Edit the `User settings` in [`s01-runoff_climatology.sh`](s01-runoff_climatology.sh).
The standard settings are ELSE_GPCC, `inp/ELSE_GPCC/runoffYYYY.nc`, variable
`runoff`, 1981–2010, units from NetCDF, and daily minimum coastal modification.
With the repository's existing NumPy/netCDF4 environment active:

```sh
sh map/tools/script_runoff_preset/s01-runoff_climatology.sh all
# Independently execute/restart each stage:
sh map/tools/script_runoff_preset/s01-runoff_climatology.sh calculate
sh map/tools/script_runoff_preset/s01-runoff_climatology.sh modify
sh map/tools/script_runoff_preset/s01-runoff_climatology.sh export
```

Existing outputs cause an error rather than silent replacement. Add
`--overwrite` only when intentional. Completed earlier stages can be retained
while rerunning later stages. Each file is staged temporarily then renamed;
a multi-file stage is not an all-or-nothing transaction. Partial stage completion
requires explicit overwrite or a new output prefix on restart.

One Shell is sufficient: it only configures and sequences the independently
callable Python programs. `runoff_calc_climatology.py calculate` owns Step 1,
`runoff_modify_coastal.py` owns Step 2, and
`runoff_calc_climatology.py export` owns Step 3. Their `--help` lists shared
source/period/unit options. No source or historical Fortran files are modified.

## Input contract and other products

The actual ELSE_GPCC files have float32 `runoff(time,latitude,longitude)`,
units `mm day-1`, `missing_value=-999`, latitude centers 89.5..-89.5 and longitude
-179.5..179.5 on a 180 × 360 grid. Gregorian/proleptic-Gregorian time has daily
bounds; noon labels represent each midnight-to-midnight interval. The requested
1981–2010 files are available locally; they are additional data, not a clone-only
requirement satisfied by every checkout.

For another product edit `DATASET`, `INPUT_DIR`, `INPUT_PATTERN`,
`RUNOFF_VARIABLE`, years, `INPUT_UNITS`, `OUTPUT_PREFIX` and, when necessary,
`INTERVAL_HOURS` and `LONGITUDE_BOUNDARY`. Set `REFERENCE=""` when the supplied
ELSE_GPCC historical Binary is not a relevant comparison. Set
`COAST_MODIFICATION="no"` to export the uncorrected mean. Only `minimum` is
implemented; no mean-field-only approximation is presented as equivalent.

- File grouping may be annual, monthly or daily. Patterns accept `YYYY`, `MM`,
  `DD`, `%Y`, `%m`, `%d` or globs. Variable dimensions may be reordered, but must
  be time and two 1-D regular coordinate dimensions named as their coordinates.
  Coordinates require explicit `degrees_east` / `degrees_north` units; their
  values, dtype and increasing/decreasing direction are retained.
- Rates supported: `mm/day` / `mm day-1`, `mm/h` / `mm h-1`, `mm/s` / `mm s-1`,
  `m/s` / `m s-1`. Integrate each record over its interval. Depths `mm` or `m`
  must already represent **one interval**, not a cumulative forecast. They need
  CF time bounds or explicit `--interval-hours`. Cumulative GRIB accumulations
  are rejected; use the existing upstream converter first. Unknown units fail.
- CF bounds take priority. Without bounds, uniform rate-series spacing supplies
  duration; a single record needs an explicit interval. Daily records use their
  named calendar day; subdaily labels are interpreted as interval starts.
  Set an explicit interpretation or preprocess ambiguous timestamps upstream.
- Require consecutive, nonoverlapping, complete years and days. Missing dates
  fail; they are never interpolated. Subdaily intervals must fit within one day
  and cover all 86400 seconds. Support Gregorian/proleptic-Gregorian and noleap
  calendars; reject 360-day calendars and mixed calendar families.
- Masked values, NaN/Inf and negative runoff are invalid. Any invalid subinterval
  makes that cell's day invalid. For each calendar day/cell, average available
  valid years and save `valid_year_count`. No valid years means missing. This
  explicit available-year policy can differ from the legacy numeric-sentinel sum.
  Review counts if a product has incomplete cell data.
- Exclude February 29; average matching month/day across years. The representative
  NetCDF cycle has 365 noleap days with daily bounds (year 2001 is a label axis,
  not the source period). Each value is daily depth / equivalent daily mean rate
  [mm day-1], **not** a subdaily rate sample.
- Annual mean requires all 365 daily climatologies valid. Sum them in calendar
  order and divide by `365 * 86400` to get mm/s. Float32 chronological sums are
  retained deliberately; this is not a float64 numerical upgrade.

Only a 365-day accumulator/count grid and one source interval/day are retained,
not the full multi-year series. Step 2 rereads source days: minimum and averaging
do not commute. Files open read-only. CLI output directories are restricted to
this workflow's `output/` tree; synthetic tests use isolated temporary files.

## Scientific Rationale and Design Decisions

**Maintainer-confirmed intent.** Long-term runoff supplies mean river discharge
for channel width/depth estimation. Zero or missing forcing can deprive small
coastal rivers of a mean-flow estimate. Neighbor filling permits products without
a land/sea mask to be processed. Using the minimum is a conservative choice
against assigning a larger neighbor runoff; its physical optimality has **not**
been independently validated. It need not be appropriate for all dry interiors.

**Verified legacy rules.** `etc/runoff_preset/src/day_clim.F90` averages the same
calendar day across years, excluding February 29. `ave_clim.F90` actually writes
an **annual sum**, despite its name; it does not divide by 365 or 86400.
`mod_runoff.F90` fixes donor/target classes using that long-term field **only at
Input-Matrix-referenced cells**. A nonpositive-mean target gets the minimum of
the surrounding donor **daily** values. Donor eligibility is positive *mean*,
not positive daily runoff: daily zero is allowed. The source does not explicitly
exclude daily missing/negative donors. Longitude wraps unconditionally; latitude
does not. These source facts are more precise than the old README's shorthand
“minimum positive value.” Old sources remain unchanged as historical evidence.

**Approved v5 change.** A runoff climatology must be independent of river maps:
remove the Input-Matrix target/donor restriction and process the runoff grid.
This changes a scientific selection rule, not just programming language. It is
not valid to demand global bitwise identity with the old restricted product or
to dismiss every difference as numerical error. River-map-dependent allocation
is deferred to the downstream channel workflow.

**Algorithm and implementation decisions.** From the original uncorrected mean,
select every finite-nonpositive or missing target and finite-positive donor.
Freeze these classes. For each original source day, take the minimum finite,
nonnegative daily value from eligible eight-neighbor donors, including zero.
With no eligible daily candidate, retain the original target. Apply replacements
simultaneously; filled cells never become new donors. Then calculate the daily
climatology and annual mean again. Excluding invalid daily donors is an explicit
missing-data rule; its broader effect needs review for products unlike ELSE_GPCC.
Only a complete 360-degree regular grid wraps longitude automatically; regional
grids and latitude do not wrap. Users can explicitly retain regional boundaries.

“Coast modification” is a historical name: this algorithm detects **no actual
coastline**. It can fill inland zero-runoff cells and ocean-adjacent cells unused
by any river map. No water balance or land/sea-area constraint is imposed. Keep
the uncorrected daily climatology and annual mean so this change's spatial effect
can be audited independently. Preserve the 365-day product for legacy seasonality
and reproducible comparisons, not because leap-day runoff is physically absent.
The new annual normalization is explicit mm/s, matching the current channel
reader's contract; the legacy annual-sum output alone has different units.

**Open questions.** The complete generation history and original target mask of
`map/data/ELSE_GPCC_clm-1981-2010.one` are unavailable here. Its main differences
are consistent with the changed selection domain, but that is not a recovered
provenance trace. Small arithmetic/source-history differences remain possible.
Physical validity of minimum filling, its effect on inland dryness and water
balance, and the available-year policy for other products require scientific
review. This workflow does not resolve ERA5-Land time attribution (KG-0019).

## Outputs and their purposes

Everything is saved under ignored `output/`; with the default prefix/period:

| File suffix after `ELSE_GPCC_clm-1981-2010` | Purpose |
| --- | --- |
| `.daily_before.nc` | Original 365-day climatology and valid-year counts, mm day-1 |
| `.mean_before.nc` | Original long-term mean, mm s-1; fixes donors/targets and permits independent auditing |
| `.daily_coastmod.nc` | Recomputed corrected daily climatology and valid-year counts |
| `.mean_coastmod.nc` | Corrected long-term mean before final export |
| `.nc`, `.one` | Final long-term mean [mm s-1], same float32 numbers and missing sentinel |
| `.comparison.json` | Size/grid/missing/zero counts, exact matches, difference statistics and hashes |
| `.difference.nc` | Spatial difference field: generated minus historical reference, mm s-1 |

NetCDF is NetCDF-4, lossless deflate 3 + shuffle, fill/missing value `-999`.
Binary is one little-endian float32 record, original latitude order, longitude/x
fastest. NetCDF field order is `(latitude,longitude)` using original coordinate
names; daily files prepend `time`. No final daily timestamps are shifted.
The comparison Binary's matching grid/order must be established by the user;
Binary cannot supply its own coordinates or units.

## Validation and observed ELSE_GPCC comparison

```sh
python3 -B -m unittest map.tools.tests.test_runoff_preset -v
```

Twelve small tests cover calendar averaging/leap exclusion, year counts and missing
values, annual normalization, rate/depth units, subdaily time weighting and gaps,
minimum-before-average, global/regional boundaries, no iterative propagation,
zero/no-candidate behavior, encoding identity, overwrite refusal, noleap dates
and the three-stage source/output contract. A tiny
Fortran comparison is byte-identical when both algorithms have the same mapped
mask; a deliberately restricted mask demonstrates the approved selection change.

The actual 1981–2010 calculation completed on 2026-11-16. Grid: 360 × 180,
float32. Before/after zero counts: **51,829 / 48,002**; missing: **0 / 0**.
4,266 targets had a candidate on at least one day; 3,827 mean values became
positive (daily zero candidates explain why not all filled targets change).
All valid-year counts are 30 for every day/cell, so missing-year exclusion does
not explain this run's differences. Against the existing Binary: **49,789 / 64,800 exact matches (76.8349%)**;
max absolute difference **9.4081559e-5 mm/s**, RMSE **2.2713322e-6 mm/s**,
mean signed difference **1.4840026e-7 mm/s**. The largest difference is at
**74.5°W, 54.5°S**, where the reference is zero and the new grid-only result is
positive. 807 reference-zero cells become positive. On originally positive
runoff cells, the maximum discrepancy is only **9.4587449e-11 mm/s**; rounding
or unrecovered source/history differences cannot be uniquely distinguished.
The `.difference.nc` retains the complete spatial distribution. Difference
statistics weight jointly valid grid cells equally; they are not area-weighted
water-balance diagnostics. Memory scales with 365 times the runoff grid size
(sums, counts and climatology plus backend caches), not the source period length.
Very high-resolution products may need large RAM; tiled/disk-backed accumulation
is a future extension, not claimed here.

The former reference at the time of the original comparison had SHA-256
`87369394baa9ec715647740771c51a1ffc5eb77513885022d7e6350be50b580c`.
The generated Binary SHA-256 is
`7a5876df2934e87cb7db9ffd1ace38bc68d3f9268a7f6c3ba69c21db4108ae6a`.
This is reproducibility/contract evidence, **not** proof of physical correctness.
The maintainer subsequently adopted the generated field as recorded above.
The original implementation did not replace the reference; the maintainer
performed the copy, and future regeneration still requires explicit adoption.
