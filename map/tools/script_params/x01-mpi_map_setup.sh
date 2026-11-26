#!/bin/sh
set -eu

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
BASIN_MERGE_MODE="standard"  # Basin merging: standard (6%) or small_basins (3%).
MPI_COUNTS="4 8 16"          # Generate mpireg-4.nc, mpireg-8.nc, mpireg-16.nc.
# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"

cmf_check_init "Prepare MPI map products"

# Temporary aggregated MPI basin map; removed after region assignment or on failure.
TEMP_BASIN="../bifbsn_mpi.nc"
trap 'status=$?; rm -f "$TEMP_BASIN"; cmf_check_on_exit "$status"' 0

# Count MPI partitions and select the largest for the diagnostic.
set -- $MPI_COUNTS
PARTITION_COUNT=$#
[ "$PARTITION_COUNT" -gt 0 ] || { printf 'MPI_COUNTS must not be empty.\n' >&2; exit 2; }
MAX_MPI=$(printf '%s\n' "$@" | sort -n | tail -n 1)
TOTAL_STEPS=$((PARTITION_COUNT + 2))

cmf_check_step 1 "$TOTAL_STEPS" "Aggregate basins using $BASIN_MERGE_MODE threshold"
"$PYTHON_CMD" "$CODE_DIR/param_mpi_set_basin.py" --mode "$BASIN_MERGE_MODE" \
    --map-dir ..

STEP_COUNT=2
for N in $MPI_COUNTS; do

    cmf_check_step "$STEP_COUNT" "$TOTAL_STEPS" "Assign basins to $N MPI regions"
    "$PYTHON_CMD" "$CODE_DIR/param_mpi_set_region.py" "$N" --map-dir ..
    STEP_COUNT=$((STEP_COUNT + 1))
done

# Verification-only diagnostic: report bifurcation pathways dropped by MPI partitioning.
# This check does not modify MPI maps or generate inputs required by simulation.

cmf_check_step "$STEP_COUNT" "$TOTAL_STEPS" "Check dropped bifurcation pathways for the largest requested MPI count ($MAX_MPI)"
# The largest requested count provides one representative diagnostic, not a guaranteed maximum of dropped pathways.
"$PYTHON_CMD" "$CODE_DIR/analysis_mpi_dropped_bifurcation.py" \
    "../mpireg-$MAX_MPI.nc" --map-dir ..

cmf_check_success

# Optional Python CLI flags:
# param_mpi_set_basin.py: --check-map, --map-format binary
# param_mpi_set_region.py / analysis_mpi_dropped_bifurcation.py: --map-format binary
# Add --check-map to the param_mpi_set_basin.py command above to write its diagnostic.
