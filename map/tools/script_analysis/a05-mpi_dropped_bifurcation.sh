#!/bin/sh
# Example: inspect bifurcation pathways dropped from an existing MPI region map.
# The executable reads map inputs from the map root, so this example runs there.
set -eu

# Command substitution stores the resolved path; CDPATH= keeps cd output predictable.
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
PYTHON_CMD="${PYTHON_CMD:-python3}"
if [ -n "${CMF5_ROOT:-}" ]; then
    CODE_DIR="$CMF5_ROOT/map/tools/code"
else
    CODE_DIR="$SCRIPT_DIR/../../tools/code"
fi
if [ ! -d "$CODE_DIR" ]; then
    printf '[ERROR] Shared Python tools not found: %s (set CMF5_ROOT to the repository root)\n' "$CODE_DIR" >&2
    exit 1
fi
MAP_DIR=$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)

# Analysis output directory, relative to script_analysis/.
OUT_DIR="out_analysis"  # Change to ../out_analysis to use the map-root output folder.

# Command-line inputs: an existing region map and optional dropped-path CSV filename.
if [ "$#" -lt 1 ] || [ "$#" -gt 3 ] || [ "$#" -eq 2 ]; then
    printf '\n[ERROR] Usage: %s <region-map.nc> [--csv <dropped.csv> | --map-format binary]\n' "$0" >&2
    exit 2
fi

# The second and third positional arguments are optional; :- supplies an empty default.
# A relative CSV filename is placed in OUT_DIR; an absolute path is used as given.
REGION_MAP=$1
CSV_OPTION=${2:-}
CSV_ARGUMENT=${3:-}
CSV_IN_OUT_DIR=0
MAP_FORMAT=netcdf
if [ "$CSV_OPTION" = "--map-format" ]; then
    [ "$CSV_ARGUMENT" = "binary" ] || { printf '\n[ERROR] --map-format supports only binary as an explicit legacy option.\n' >&2; exit 2; }
    MAP_FORMAT=binary
    CSV_ARGUMENT=""
fi

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------

# The sed expression escapes apostrophes so printed paths can be pasted into a shell.
quote_shell_arg() {
    printf "'"
    printf '%s' "$1" | sed "s/'/'\\\\''/g"
    printf "'"
}

if [ "$#" -eq 3 ] && [ "$CSV_OPTION" != "--csv" ] && [ "$CSV_OPTION" != "--map-format" ]; then
    printf '\n[ERROR] Usage: %s <region-map.nc> [--csv <dropped.csv> | --map-format binary]\n' "$0" >&2
    exit 2
fi

if [ -n "$CSV_ARGUMENT" ]; then
    case "$CSV_ARGUMENT" in
        /*) CSV_FILE=$CSV_ARGUMENT ;;
        *)
            CSV_FILE="$SCRIPT_DIR/$OUT_DIR/$CSV_ARGUMENT"
            CSV_IN_OUT_DIR=1
            ;;
    esac
fi

# Keep absolute paths; resolve relative filenames from the map root.
case "$REGION_MAP" in
    /*) ;;
    *) REGION_MAP="$MAP_DIR/$REGION_MAP" ;;
esac

if [ ! -s "$REGION_MAP" ]; then
    printf '\n[ERROR] Region map not found: %s\n' "$REGION_MAP" >&2
    exit 1
fi

if [ "$CSV_IN_OUT_DIR" -eq 1 ]; then
    mkdir -p "$SCRIPT_DIR/$OUT_DIR"
fi

# This diagnostic reads params.txt and map files relative to the map root.
cd "$MAP_DIR"

printf '\nWorking directory: %s\n' "$PWD"

STEP="Check dropped bifurcation pathways for $REGION_MAP"
printf '\n==================================================\n'
printf '[STEP 1/1] Check dropped bifurcation pathways\n'
printf '==================================================\n\n'

if [ -n "$CSV_ARGUMENT" ]; then
    printf '"$PYTHON_CMD" "$CODE_DIR/analysis_mpi_dropped_bifurcation.py" '
    quote_shell_arg "$REGION_MAP"
    printf ' '
    quote_shell_arg "$CSV_OPTION"
    printf ' '
    quote_shell_arg "$CSV_FILE"
    printf '\n'
    "$PYTHON_CMD" "$CODE_DIR/analysis_mpi_dropped_bifurcation.py" --map-dir "$MAP_DIR" --map-format "$MAP_FORMAT" "$REGION_MAP" --csv "$CSV_FILE"
else
    printf '"$PYTHON_CMD" "$CODE_DIR/analysis_mpi_dropped_bifurcation.py" '
    quote_shell_arg "$REGION_MAP"
    printf '\n'
    "$PYTHON_CMD" "$CODE_DIR/analysis_mpi_dropped_bifurcation.py" --map-dir "$MAP_DIR" --map-format "$MAP_FORMAT" "$REGION_MAP"
fi

printf '\n==================================================\n'
printf '[SUCCESS] Dropped bifurcation pathway check complete.\n'
printf '==================================================\n'
