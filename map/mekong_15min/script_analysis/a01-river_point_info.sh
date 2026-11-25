#!/bin/sh
# Example: inspect river-network and unit-catchment information at a selected point.
# Run from script_analysis/; shared Python sources are resolved by this wrapper.
# Inputs: standard river-map files; latlon mode may use 15sec/ or 1min/ catmxy data.
# Output: river-point report in OUT_DIR.
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

# Analysis output directory, relative to script_analysis/.
OUT_DIR="out_analysis"  # Change to ../out_analysis to use the map-root output folder.

# Choose a query mode and location; grid indices are one-based, coordinates are degrees.
QUERY_MODE=xy   # Query type: xy for grid indices or latlon for geographic coordinates.
IX=62           # CaMa-Flood grid column for xy mode.
IY=93           # CaMa-Flood grid row for xy mode.
LAT=11.579      # Latitude for latlon mode (degrees north).
LON=104.946     # Longitude for latlon mode (degrees east).
REPORT_FILE="$OUT_DIR/river_point_info.txt"  # Text report path; overwritten on each run.

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------

# The sed expression escapes apostrophes so printed paths can be pasted into a shell.
quote_shell_arg() {
    printf "'"
    printf '%s' "$1" | sed "s/'/'\\\\''/g"
    printf "'"
}

cd "$SCRIPT_DIR"
if [ -n "$REPORT_FILE" ]; then
    mkdir -p "$OUT_DIR"
fi

printf '\nWorking directory: %s\n' "$PWD"

printf '\n==================================================\n'
printf '[STEP 1/1] Inspect river information using %s coordinates\n' "$QUERY_MODE"
printf '==================================================\n\n'
case "$QUERY_MODE" in
    xy)
        if [ -n "$REPORT_FILE" ]; then
            printf '"$PYTHON_CMD" "$CODE_DIR/analysis_river_point_info.py" xy %s %s > ' "$IX" "$IY"
            quote_shell_arg "$REPORT_FILE"
            printf '\n'
            "$PYTHON_CMD" "$CODE_DIR/analysis_river_point_info.py" xy "$IX" "$IY" > "$REPORT_FILE"
            printf 'River-information report: %s\n' "$REPORT_FILE"
        else
            printf '"$PYTHON_CMD" "$CODE_DIR/analysis_river_point_info.py" xy %s %s\n' "$IX" "$IY"
            "$PYTHON_CMD" "$CODE_DIR/analysis_river_point_info.py" xy "$IX" "$IY"
        fi
        ;;
    latlon)
        if [ -n "$REPORT_FILE" ]; then
            printf '"$PYTHON_CMD" "$CODE_DIR/analysis_river_point_info.py" latlon %s %s > ' "$LAT" "$LON"
            quote_shell_arg "$REPORT_FILE"
            printf '\n'
            "$PYTHON_CMD" "$CODE_DIR/analysis_river_point_info.py" latlon "$LAT" "$LON" > "$REPORT_FILE"
            printf 'River-information report: %s\n' "$REPORT_FILE"
        else
            printf '"$PYTHON_CMD" "$CODE_DIR/analysis_river_point_info.py" latlon %s %s\n' "$LAT" "$LON"
            "$PYTHON_CMD" "$CODE_DIR/analysis_river_point_info.py" latlon "$LAT" "$LON"
        fi
        ;;
    *)
        printf '\n[ERROR] QUERY_MODE must be xy or latlon.\n' >&2
        exit 2
        ;;
esac

printf '\n==================================================\n'
printf '[SUCCESS] River-point inspection complete.\n'
printf '==================================================\n'
