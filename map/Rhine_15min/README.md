# Rhine Regional Map — Tutorial 11

This is a local working map for preparing the July 2021 Rhine event experiment.
It is derived from the separately distributed `map/glb_15min/` source with the
map-local regionalization scripts in `script_region/`. The generated map data
are excluded from Git; the copied scripts and their settings are retained as
reproducibility records. The shared implementations remain under `map/tools/`.

## Current map geometry

The map-local source settings are `SOURCE="../../glb_15min/"` and outer bounds
WEST/EAST/SOUTH/NORTH = 3/13/45/53 degrees. `params.nml` records a 40 × 32
grid, 0.25° cell size and the same edge bounds. Base-resolution individual
NetCDF fields are stored directly under `map/Rhine_15min/`; there is no
`netcdf/` subdirectory. The 1-minute `location.csv` records the auxiliary
grid geometry, and `1min/1min.catmxy.nc` stores `catmxx` and `catmyy` as
`(lat, lon)` arrays with one-based model-grid indices. A legacy `params.txt` copy and older Binary products may remain locally, but
`params.nml` and the individual NetCDF products are the maintained v5 interface.
Retained products were not regenerated for this documentation update.

The map includes base-resolution river/network fields and parameter products,
1-minute auxiliary map data, the `test-1deg` ELSE_GPCC climatology mapping,
and a separate `ERA5land_global` simulation runoff mapping. Tutorial 11 also
generates `ERA5land_Rhine2021Jul` for its 111 × 91 regional ERA5-Land subset;
that matrix is distinct from the 3600 × 1801 global grid and the two cannot be
interchanged. Reproduce the regional pair with
the shared Python `map/tools/code/param_inpmat_generate.py`, using the regional
grid settings and command recorded in Tutorial 11 Step 13. The retained NetCDF
matrix and DIMINFO are local and ignored; the former Binary-generation details
in the Step 13 execution record are historical. `GRDC_alloc.csv` is the
standard GRDC allocation product; it does not verify correspondence for the
ECMWF-provided Tutorial 11 gauges.

## Reproduction and data policy

Read the component READMEs before running a workflow. Build shared v5 tools
from the repository root as documented in `map/tools/README.md`. Regional
scripts must be run from `script_region/`; parameter and conversion scripts
have their own documented working-directory behavior. Existing outputs may be
overwritten by these scripts, so review the selected commands and back up any
locally valuable results before regeneration.

The current regional ERA5-Land mapping is the NetCDF pair
`inpmat_ERA5land_Rhine2021Jul.nc` and
`diminfo_ERA5land_Rhine2021Jul.nml`; the original Step 13 Binary generation
record is historical. The regional map is a local/external working dataset and
is not committed or redistributed from this repository. Source map, high-resolution inputs and
runoff climatology have separate package and licensing conditions; consult
`map/README.md` and the supplied data-package terms.
