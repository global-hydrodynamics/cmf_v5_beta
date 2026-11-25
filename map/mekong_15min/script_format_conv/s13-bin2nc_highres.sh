#!/bin/sh
# Convert registered high-resolution Binary map tiles to NetCDF.
# Run from this map's script_format_conv/ directory.
set -eu

# CaMa-Flood general setting (check CMF root, import shell error checker)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
HIRES=""          # Empty selects the coarsest installed Binary resolution.
VARS="all"       # Use all registered products or select space-separated file stems.
COMPRESSION_LEVEL=3
JOBS=8

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
REGISTRY="$CMF_V50_ROOT/variable_table/map_variables.csv"
cmf_check_init "Convert high-resolution Binary map products"
AVAILABLE=""
if [ -z "$HIRES" ]; then
    for tag in 1min 30sec 15sec 5sec 3sec 1sec; do
        if [ -f "../binary/$tag/location.txt" ]; then
            AVAILABLE="${AVAILABLE}${AVAILABLE:+ }$tag"
            [ -n "$HIRES" ] || HIRES=$tag
        fi
    done
fi
[ -n "$HIRES" ] || { printf 'No Binary high-resolution location.txt found in ../binary.\n' >&2; exit 1; }
printf 'Selected Binary high-resolution map: ../binary/%s\n' "$HIRES"
while :; do
    printf 'Use this resolution? [Y/n]: '
    IFS= read -r answer
    case "$answer" in
        ''|y|Y|yes|Yes|YES) break ;;
        n|N|no|No|NO)
            while :; do
                printf 'Available resolutions: %s\nChoose resolution: ' "$AVAILABLE"
                IFS= read -r HIRES
                case " $AVAILABLE " in *" $HIRES "*) break 2 ;; esac
                printf 'Choose one of the listed resolutions.\n'
            done ;;
        *) printf 'Please answer Yes or No (Enter = Yes).\n' ;;
    esac
done
cmf_check_step 1 1 "Convert registered high-resolution products for $HIRES"
"$PYTHON_CMD" "$CODE_DIR/convert_highres_binary_to_netcdf.py" \
    --map-dir .. --hires "$HIRES" --variables "$VARS" \
    --registry "$REGISTRY" --compression-level "$COMPRESSION_LEVEL" --jobs "$JOBS"
cmf_check_success

# Optional converter flags: --no-overwrite, --force. Default replaces NetCDF outputs.
