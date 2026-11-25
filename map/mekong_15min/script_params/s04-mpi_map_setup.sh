#!/bin/sh
set -eu

# CaMa-Flood general setting (check CMF root, import shell error checker)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
MPIMODE="normal"       # Basin aggregation mode: normal or MaxMPI.
MPI_COUNTS="4 8 16"     # Requested number of MPI regions.
DEFAULT_MPI=16           # Connectivity analysis partition; include it in MPI_COUNTS.
TEMP_BASIN="../bifbsn_mpi.nc"  # NetCDF intermediate removed after partition creation.
# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
cmf_check_init "Prepare MPI map products"

cmf_check_step 1 3 "Aggregate basins for the selected MPI mode"
"$PYTHON_CMD" "$CODE_DIR/param_mpi_set_basin.py" --mode "$MPIMODE" \
    --map-dir ..

STEP_COUNT=2
set -- $MPI_COUNTS
PARTITION_COUNT=$#
TOTAL_STEPS=$((PARTITION_COUNT + 2))
for N in $MPI_COUNTS; do
    cmf_check_step "$STEP_COUNT" "$TOTAL_STEPS" "Assign basins to $N MPI regions"
    "$PYTHON_CMD" "$CODE_DIR/param_mpi_set_region.py" "$N" --map-dir ..
    STEP_COUNT=$((STEP_COUNT + 1))
done

cmf_check_step "$STEP_COUNT" "$TOTAL_STEPS" "Check bifurcation connectivity for the default partition"
"$PYTHON_CMD" "$CODE_DIR/analysis_check_mpi_bifurcation.py" \
    "../mpireg-$DEFAULT_MPI.nc" --map-dir ..
rm -f "$TEMP_BASIN"
cmf_check_success

# Optional Python CLI flags:
# param_mpi_set_basin.py: --check-map, --map-format binary
# param_mpi_set_region.py / analysis_check_mpi_bifurcation.py: --map-format binary
# Add --check-map to the param_mpi_set_basin.py command above to write its diagnostic.
