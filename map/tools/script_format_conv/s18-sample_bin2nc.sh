#!/bin/bash
# Convert sample Binary maps produced by script_params/s06 to NetCDF.
# Run from this map's script_format_conv/ directory.
set -eu

# CaMa-Flood general setting (check CMF root, import shell error checker)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

# ----------------------------------------------------------------------
# User settings
# ----------------------------------------------------------------------
VARIANTS=(
    "subbsn-sample.bin:subbsn.bin"
    "subcol-sample.bin:subcol.bin"
)
NO_OVERWRITE=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --no-overwrite) NO_OVERWRITE=1; shift ;;
        --help|-h) printf 'Usage: ./%s [--no-overwrite]\n' "${0##*/}"; exit 0 ;;
        *) printf 'Usage: ./%s [--no-overwrite]\n' "${0##*/}" >&2; exit 2 ;;
    esac
done

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------
CODE_DIR="$CMF_V50_ROOT/map/tools/code"
REGISTRY="$CMF_V50_ROOT/variable_table/map_variables.csv"
cmf_check_init "Convert sample Binary maps to NetCDF"
[ -f ../params.txt ] || { printf 'Map-root params.txt is missing.\n' >&2; exit 1; }
for VARIANT in "${VARIANTS[@]}"; do
    INPUT=${VARIANT%%:*}
    [ -f "../binary/$INPUT" ] || { printf 'Sample Binary is missing: ../binary/%s\n' "$INPUT" >&2; exit 1; }
done
cmf_check_step 1 1 "Convert the sample subbasin and color maps"
CONVERTED=0
SKIPPED=0
for VARIANT in "${VARIANTS[@]}"; do
    INPUT=${VARIANT%%:*}
    REFERENCE=${VARIANT#*:}
    SOURCE="../binary/$INPUT"
    OUTPUT="../${INPUT%.bin}.nc"
    if [ -f "$OUTPUT" ] && [ "$NO_OVERWRITE" -eq 1 ]; then
        printf 'Existing output preserved: %s\n' "$OUTPUT"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi
    printf '%s -> %s\n' "$SOURCE" "$OUTPUT"
    "$PYTHON_CMD" "$CODE_DIR/convert_map_binary_to_netcdf.py" --map-dir .. \
        --input "$SOURCE" --output "$OUTPUT" --reference-binary "$REFERENCE" \
        --registry "$REGISTRY"
    CONVERTED=$((CONVERTED + 1))
done
printf 'Converted: %s; skipped: %s\n' "$CONVERTED" "$SKIPPED"
cmf_check_success

# Optional shell flag: --no-overwrite preserves existing NetCDF outputs.
