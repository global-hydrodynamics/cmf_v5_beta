#!/bin/bash
# User-facing configuration for one global ERA5-Land runoff product.
# Passes settings to s01-download.sh and s02-convert_CMF_nc.sh, in that order.
# Normally edit only the User settings below; Python performs the data processing.
set -eu

# User settings

# Output dataset name under inp/; a single directory name, never a path.
DATASET="ERA5land-glb_2day"

# Inclusive period and geographic edges [degrees east/north].
START_DATE="2000-01-01"
END_DATE="2000-01-02"
WEST=-180
EAST=180
SOUTH=-90
NORTH=90

# Temporal resolution [hours], file grouping and parallel requests.
TSTEP=24
DOWNLOAD_UNIT="monthly"
OUTPUT_UNIT="monthly"
FORMAT="netcdf"                 # NetCDF is the only supported output format.
# Intentional environment interfaces for job resources and Python environment.
# ${VAR:-default} uses the supplied nonempty value, otherwise the shown default.
NCPUS=${NCPUS:-1}
PYTHON_CMD=${PYTHON_CMD:-python3}

# ================================================================
# User settings end here
# ================================================================

# Command substitution resolves this script's directory independently of the caller.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
# Both stages receive the same explicit settings; CLI options take precedence.
SETTINGS=(--dataset "$DATASET" --start-date "$START_DATE" --end-date "$END_DATE"
    --west "$WEST" --east "$EAST" --south "$SOUTH" --north "$NORTH"
    --tstep "$TSTEP" --download-unit "$DOWNLOAD_UNIT" --output-unit "$OUTPUT_UNIT"
    --format "$FORMAT" --ncpus "$NCPUS" --python "$PYTHON_CMD")

for option in "$@"; do
    if [ "$option" = --help ] || [ "$option" = -h ]; then
        bash "$SCRIPT_DIR/s01-download.sh" --help
        exit 0
    fi
done

printf '\n[STEP 1/2] Downloading product source data\n'
bash "$SCRIPT_DIR/s01-download.sh" "${SETTINGS[@]}" "$@"

printf '\n[STEP 2/2] Converting product to CaMa-Flood NetCDF\n'
bash "$SCRIPT_DIR/s02-convert_CMF_nc.sh" "${SETTINGS[@]}" "$@"

printf '\n[SUCCESS] Product generation completed\n'
