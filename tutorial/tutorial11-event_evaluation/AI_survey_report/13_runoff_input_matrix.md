# Runoff Input Matrix Preparation — Survey Report

## Purpose and grid relationship

The runoff Input Matrix connects regular ERA5-Land cells to the CaMa-Flood
unit-catchment cells on a particular model map. It stores the input-grid
indices and contributing area weights used by map preprocessing. The matrix is
specific to both the runoff grid geometry/order and the CaMa-Flood map; matching
resolution alone does not make two matrices interchangeable.

This is especially important for this example: the existing `ERA5land_global`
pair is for a 3600 × 1801 global input grid. Step 12 supplies a regional
111 × 91 subset. The regional grid keeps the same 0.1° spacing but has a
different origin and shape, so the global matrix cannot be reused for it.
Step 13 generated a separate `ERA5land_Rhine2021Jul` pair for
`map/Rhine_15min/`.

## Observed grid specifications

The converted NetCDF coordinate arrays were read from the first and final daily
files. Both contain 111 longitude centers from 2.5 to 13.5°E and 91 latitude
centers from 53.5 down to 44.5°N, at 0.1° spacing. The input rows are therefore
north-to-south (`OLAT=NtoS`). The coordinate-derived cell edges are
2.45–13.55°E and 44.45–53.55°N. The request bounds and cell-center coordinates
are not the same as these outer cell edges.

The regional model `params.txt` gives 40 × 32 cells, 0.25° spacing and outer
edges 3–13°E, 45–53°N. The selected 1-minute high-resolution map's
`location.txt` also covers those edges and has 600 × 480 cells. The ERA5-Land
regional grid extends 0.5° beyond the model-map edges, so it covers the model
window.

## Generated `diminfo`

The following is the complete content of the actual generated file
`map/Rhine_15min/diminfo_ERA5land_Rhine2021Jul.txt`:

```text
        40     !! nXX
        32     !! nYY
        10     !! floodplain layer
       111     !! input nXX 
        91     !! input nYY 
        30     !! input num
inpmat_ERA5land_Rhine2021Jul.bin
       3.000     !! west  edge
      13.000     !! east  edge
      53.000     !! north edge
      45.000     !! south edge
```

Line meanings:

1. `40`: CaMa-Flood base-map size in the x/east–west direction (`nXX`).
2. `32`: CaMa-Flood base-map size in the y/north–south direction (`nYY`).
3. `10`: number of floodplain layers in this map.
4. `111`: runoff input-grid size in x/longitude (`input nXX`).
5. `91`: runoff input-grid size in y/latitude (`input nYY`).
6. `30`: maximum number of distinct runoff-grid contributions found for any
   model cell (`input num`); it is not the number of time records.
7. `inpmat_ERA5land_Rhine2021Jul.bin`: matrix filename paired with this descriptor.
8. `3.000`: western outer edge of the CaMa-Flood model grid, in degrees east.
9. `13.000`: eastern outer edge of the CaMa-Flood model grid, in degrees east.
10. `53.000`: northern outer edge of the CaMa-Flood model grid, in degrees north.
11. `45.000`: southern outer edge of the CaMa-Flood model grid, in degrees north.

The descriptor records the dimensions of both grids and the **model map**
outer edges. It does not store the input-grid resolution, input-grid edge
coordinates or latitude order. Those must be read from the generated Shell
settings and verified against the actual NetCDF and Tutorial Registry. For
this run they are 0.1°, `[2.45, 44.45, 13.55, 53.55]` in
west/south/east/north order, and north-to-south respectively.

## Matrix checks and representative cells

The generator completed with exit status 0. The binary is 460,800 bytes, which
matches `3 × 30 × 40 × 32 × 4`: 30 records of x indices, 30 of y indices and 30
of overlap areas, using 32-bit values and x-fastest map records. All 1,245
river-network cells in the regional map have input contributions. The 35 other
model cells have no assigned contribution. Across the mapped cells there are
16,963 positive-area model/input-cell pairs; all one-based input indices fall
within 1–111 and 1–91, and all contributing areas are finite and positive.

| Rhine reference vicinity | Map cell (ix, iy) | Map outlet (lon, lat) | Largest-area input cell (ix, iy) | Input-cell center (lon, lat) |
| --- | ---: | ---: | ---: | ---: |
| Basel | (19, 23) | (7.589°E, 47.589°N) | (52, 62) | (7.600°E, 47.400°N) |
| Mainz | (22, 13) | (8.285°E, 50.000°N) | (62, 37) | (8.600°E, 49.900°N) |
| Cologne | (16, 9) | (6.963°E, 51.000°N) | (46, 27) | (7.000°E, 50.900°N) |
| Lobith | (14, 6) | (6.242°E, 51.828°N) | (41, 20) | (6.500°E, 51.600°N) |

These are representative map network cells near the named Rhine locations.
The matrix is an area-weighted catchment mapping: one model cell can receive
runoff from multiple 0.1° input cells, so its largest-area input center need
not coincide with the model-cell outlet. This is not a nearest-center lookup.
The index and range checks establish structural correspondence; the model's
runtime reading and runoff time semantics still need later validation.

## Step 14 handoff

Step 14 should use this regional pair with the Tutorial-local dataset row and
Step 12 execution metadata. It must select the simulation and spin-up dates,
confirm forcing covers the experiment and intended evaluation window, compare
the forcing information to runtime settings, and create the GOSH script. The
July 1–20 acquisition period is not a simulation-period decision. KG-0019,
including the ERA5-Land 00 UTC accumulation and converter boundary treatment,
remains unresolved.

The machine-readable results are in
[`metadata/13_runoff_input_matrix.json`](../metadata/13_runoff_input_matrix.json).
The map binaries and diminfo remain local/ignored; this Survey Report includes
the actual diminfo text so Tutorial readers can inspect it without the local
map-data installation.
