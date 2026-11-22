# Regional Map Preparation — Survey Report

## Purpose and decision context

Step 11 prepares the spatial map inputs for a future Rhine 2021 CaMa-Flood
experiment. Step 2 records the current **candidate** simulation window as
WGS84 outer cell-boundary edges `[3.0, 45.0, 13.0, 53.0]` (west, south, east,
north), using `glb_15min` at 0.25°. This map-preparation check used those
bounds. It does not promote the Step 2 candidate to an approved scientific
simulation configuration.

## Existing regional map found

The local `map/Rhine_15min/` contains a regional map consistent with the
requested source `../../glb_15min/` and exact bounds WEST=3.0, EAST=13.0,
SOUTH=45.0, NORTH=53.0. Its `params.txt` records 40 columns × 32 rows at
0.25° and the same outer edges. The 1-minute auxiliary `location.txt` records
600 × 480 cells over the same extent at 1/60°. These dimensions are consistent
with the requested geographic window and grid spacings.

The map contains the expected network fields (`nextxy`, `basin`, `uparea`,
`ctmare`, `rivseq`, elevation/floodplain fields), channel parameter files,
bifurcation products, permanent-water area, subbasin sample products, runoff
mappings, and derived NetCDF/COG files. Representative COGs use EPSG:4326 and
have 40 × 32 cells, 0.25° pixels and bounds 3–13°E, 45–53°N. The sampled
high-resolution COG uses 600 × 480 cells at 1 arc-minute over the same bounds.
NetCDF examples have `lon=40`, `lat=32`, `layer=10`; `bifprm.nc` has 20 paths
and 5 layers. This inspection establishes metadata and file availability, not
hydrologic validity or value-by-value equivalence to the global source.

No map generator, parameter calculator, converter, model executable, or data
acquisition was run for this Step. The map and format products were already
present as retained local outputs. Their complete generation history cannot
be established from the files alone.

## Parameter and forcing mappings

Two separate runoff-grid mappings are present and must retain their distinct
meaning:

- `inpmat_test-1deg.bin` with `diminfo_test-1deg.txt` is the 1° global
  ELSE_GPCC mapping used with the annual runoff climatology
  `map/data/ELSE_GPCC_clm-1981-2010.one` for channel climatology/parameters.
- `inpmat_ERA5land_global.bin` with `diminfo_ERA5land_global.txt` maps the
  global ERA5-Land runoff grid for a simulation configured to use that forcing.

The matching dimension files are present. The channel script retains
`test-1deg` and the ELSE_GPCC climatology input; the bifurcation workflow also
uses `test-1deg` for the standard runoff-linked parameter generation. The
ERA5-Land matrix is a separate product; its presence alone does not establish
that event forcing files or a complete simulation configuration are available.

Channel parameter settings retained in the local script include
`HC=0.1`, `HP=0.50`, `HO=0`, `HMIN=1 m`, `WC=2.50`, `WP=0.60`, `WO=0`, and
`WMIN=5 m`. The bifurcation script selects five layers. The subbasin example
uses 30,000 and 5,000 km² thresholds. These are inspected workflow settings,
not independently validated Rhine scientific choices.

A 1-minute auxiliary map is present and is used by the permanent-water
workflow. `GRDC_alloc.txt` is also present, produced by the standard GRDC
allocation workflow. It does not establish station-to-model-cell
correspondence for the ECMWF-supplied Tutorial 11 gauges; that check remains a
later observation-matching task.

## Reproducibility and data handling

The regionalization script in `map/Rhine_15min/script_region/` explicitly sets
`SOURCE="../../glb_15min/"`, WEST=3.0, EAST=13.0, SOUTH=45.0, NORTH=53.0.
Its region settings match the retained `params.txt`. The map-local parameter
and format-conversion scripts are preserved as workflow snapshots. Their
shared implementations remain under `map/tools/`.

`map/.gitignore` keeps the regional map data, Binary, NetCDF, high-resolution
and COG outputs out of Git while allowing the map-local scripts and README to
be tracked. The data remain local; this Step does not redistribute them.

## Step 12–14 handoff and simulation limitations

The existing map path is `map/Rhine_15min/`; its base grid is 0.25° (40 × 32)
with the 3–13°E, 45–53°N outer-edge window. Candidate basin IDs 74 and 1299
remain inherited from Step 2 and are not revalidated by this map-product
inspection. Basin IDs are model routing groups, not guaranteed natural
watershed boundaries.

Step 12 prepares the runoff input. Step 13 must validate the runoff Input Matrix against the actual grid. Before
simulation, Step 14 still needs to settle the event period, hydrologic scope
and treatment of neighboring routing groups, active-cell and boundary
behavior, initial conditions, forcing availability, and model configuration. File presence and matching grid metadata do not prove
complete upstream coverage, correct outlet treatment, scientifically suitable
parameter values, or simulation readiness. No Rhine event simulation or
performance evaluation was performed here.
