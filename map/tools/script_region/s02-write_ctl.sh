#!/bin/sh
# Generate GrADS CTLs for the base map and available high-resolution products.
# Run from this map's script_region/ directory after reviewing regional outputs.
set -eu

# CaMa-Flood general setting (check CMF root, import shell error checker)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
DRY_RUN=0        # Set to 1 to validate and list planned CTLs without writing.
OVERWRITE=1      # Set to 0 to preserve existing CTLs.
for OPTION in "$@"; do
    case "$OPTION" in
        --dry-run) DRY_RUN=1 ;;
        --overwrite) OVERWRITE=1 ;;
        --no-overwrite) OVERWRITE=0 ;;
        -h|--help)
            printf 'Usage: ./%s [--dry-run] [--no-overwrite]\n' "${0##*/}"
            exit 0 ;;
        *) printf 'Unknown option: %s\n' "$OPTION" >&2; exit 2 ;;
    esac
done

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
cmf_check_init "Generate Binary GrADS CTL files"

set --
[ "$DRY_RUN" -eq 0 ] || set -- "$@" --dry-run
[ "$OVERWRITE" -eq 1 ] || set -- "$@" --no-overwrite

cmf_check_step 1 1 "Generate CTLs for the base and available high-resolution maps"
"$PYTHON_CMD" "$CODE_DIR/generate_ctl.py" --map-dir ../binary "$@"
for LOCATION in ../binary/*/location.txt; do
    [ -f "$LOCATION" ] || continue
    printf 'Generating CTLs for %s\n' "${LOCATION%/location.txt}"
    "$PYTHON_CMD" "$CODE_DIR/generate_ctl.py" --map-dir "${LOCATION%/location.txt}" "$@"
done
cmf_check_success

# Optional generator flags: --dry-run, --no-overwrite, --overwrite. Default replaces outputs.
