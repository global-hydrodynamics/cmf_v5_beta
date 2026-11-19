#!/bin/bash
# Conversion stage called with arguments from a Product Shell (sample-*.sh).
# Converts downloaded accumulations to timestep runoff using the Python converter.
# Can combine input files into daily/monthly/yearly output; does not contact CDS.
# Can be rerun from retained originals without downloading them again.
set -eu

# Internal argument placeholders, not independent experiment settings.
DATASET=""
START_DATE=""
END_DATE=""
WEST=""
EAST=""
SOUTH=""
NORTH=""
TSTEP=""
DOWNLOAD_UNIT=""
OUTPUT_UNIT=""
FORMAT="netcdf"

# Retain the documented environment interfaces for runtime resources.
# ${VAR:-default} uses the environment value when nonempty.
NCPUS=${NCPUS:-1}
PYTHON_CMD=${PYTHON_CMD:-python3}

# Command substitution resolves this script independently of the caller's directory.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
source "$SCRIPT_DIR/workflow.sh"
era5_main convert "$@"
