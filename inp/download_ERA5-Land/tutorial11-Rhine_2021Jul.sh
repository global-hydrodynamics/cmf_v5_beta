#!/bin/bash
# User-facing configuration for the Tutorial 11 Rhine 2021 hourly ERA5-Land runoff product.
# Requests 2021-07-01 through 2021-07-31 over the Rhine map plus a 0.5-degree margin.
# Passes settings to s01-download.sh and s02-convert_CMF_nc.sh, in that order.
# Normally edit only the User settings below; Python performs the data processing.
set -eu

# User settings

# Output dataset name under inp/; a single directory name, never a path.
DATASET="tutorial11-ERA5land-Rhine2021Jul"

# Inclusive period and geographic edges [degrees east/north].
# Requested CDS area is not a substitute for the downloaded grid-center metadata.
START_DATE="2021-07-01"
END_DATE="2021-07-31"
WEST=2.5
EAST=13.5
SOUTH=44.5
NORTH=53.5

# Temporal resolution [hours], file grouping and parallel requests.
TSTEP=1
DOWNLOAD_UNIT="daily"
OUTPUT_UNIT="daily"
FORMAT="netcdf"                 # NetCDF is the only supported output format.
NCPUS=2
PYTHON_CMD="python3"

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
