#!/bin/bash
# User-facing configuration for the Tutorial 11 Rhine 2021 hourly ERA5-Land runoff product.
# Requests 2021-07-01 through 2021-07-31 over the Rhine map plus a 0.5-degree margin.
# Saves this event's data below the Tutorial directory; shared processing stays under inp/.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
TUTORIAL_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
REPO_ROOT=$(CDPATH= cd -- "$TUTORIAL_DIR/../.." && pwd -P)

# User settings

# Tutorial-local parent directory for originals, converted runoff and logs.
INP_ROOT="$TUTORIAL_DIR/inp"
# Dataset directory name directly under INP_ROOT; do not include path separators.
DATASET="ERA5land-Rhine2021Jul"

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

# ----------------------------------------------------------------------
# User settings end here. Shared downloader paths and workflow follow.
# ----------------------------------------------------------------------

DOWNLOADER_DIR="$REPO_ROOT/inp/download_ERA5-Land"
# Both stages receive the same explicit settings; CLI options take precedence.
SETTINGS=(--inp-root "$INP_ROOT" --dataset "$DATASET" --start-date "$START_DATE" --end-date "$END_DATE"
    --west "$WEST" --east "$EAST" --south "$SOUTH" --north "$NORTH"
    --tstep "$TSTEP" --download-unit "$DOWNLOAD_UNIT" --output-unit "$OUTPUT_UNIT"
    --format "$FORMAT" --ncpus "$NCPUS" --python "$PYTHON_CMD")

for option in "$@"; do
    if [ "$option" = --help ] || [ "$option" = -h ]; then
        bash "$DOWNLOADER_DIR/s01-download.sh" --help
        exit 0
    fi
done

printf '\n[STEP 1/2] Downloading product source data\n'
bash "$DOWNLOADER_DIR/s01-download.sh" "${SETTINGS[@]}" "$@"

printf '\n[STEP 2/2] Converting product to CaMa-Flood NetCDF\n'
bash "$DOWNLOADER_DIR/s02-convert_CMF_nc.sh" "${SETTINGS[@]}" "$@"

printf '\n[SUCCESS] Product generation completed\n'
