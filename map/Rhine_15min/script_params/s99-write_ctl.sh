#!/bin/sh

# Generate GrADS CTL files for existing registered binaries in the base map
# and immediate high-resolution directories. Copy into a map-local
# script_params/ directory before running; data paths are relative to its
# parent map directory.

# Input Binary pattern : exact standard Binary definition (optional products).
VARIANTS="subbsn-sample.bin:subbsn.bin
subcol-sample.bin:subcol.bin
upbasin-*.bin:upbasin.bin"

usage() {
  cat <<'EOF'
Usage: ./s99-write_ctl.sh [--dry-run] [--no-overwrite | --overwrite]
       ./s99-write_ctl.sh --input FILE.bin [--variables NAMES | --reference-binary FILE.bin]

  --input FILE    Generate only this base-map Binary CTL.
  --variables NAMES  Comma-separated registry variable names (requires --input).
  --reference-binary FILE  Exact registered layout (requires --input).
  --dry-run       Validate inputs and list planned CTLs without writing files.
  --overwrite     Replace existing CTLs (the default).
  --no-overwrite  Preserve existing CTLs instead of replacing them.
EOF
}

# These internal flags are set by the command-line options in usage().
PYTHON_CMD="${PYTHON_CMD:-python3}"
DRY_RUN=0    # Set to 1 by --dry-run.
OVERWRITE=1  # Set to 0 by --no-overwrite; existing CTLs are replaced by default.
INPUT=""
VARIABLES=""
REFERENCE=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --overwrite) OVERWRITE=1; shift ;;
    --no-overwrite) OVERWRITE=0; shift ;;
    --input|--variables|--reference-binary)
      [ "$#" -ge 2 ] && [ -n "$2" ] || { usage >&2; exit 2; }
      case "$1" in
        --input) INPUT=$2 ;;
        --variables) VARIABLES=$2 ;;
        --reference-binary) REFERENCE=$2 ;;
      esac
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done
if [ -z "$INPUT" ] && { [ -n "$VARIABLES" ] || [ -n "$REFERENCE" ]; }; then
  printf 'ERROR: --variables and --reference-binary require --input.\n' >&2
  exit 2
fi

# ----------------------------------------------------------------------
# User settings end here. Program paths and processing steps follow.
# ----------------------------------------------------------------------

# Keep this map-local script directory as the working directory, as in the
# reusable script_region CTL wrapper.
# Command substitution stores the resolved path; CDPATH= keeps cd output predictable.
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd) || exit 1
cd "$SCRIPT_DIR" || exit 1

GENERATOR="../../tools/code/generate_ctl.py"
if [ ! -f "$GENERATOR" ]; then
  printf '\n[ERROR] Missing shared CTL generator: %s\n' "$GENERATOR" >&2
  exit 1
fi

# Prefer the standard compatibility tree while retaining the former root layout
# for existing maps that have not yet been migrated.
DATA_DIR=../binary
if [ ! -d "$DATA_DIR" ]; then
  if [ -n "$INPUT" ] || { [ -f ../nextxy.bin ] && [ ! -f ../nextxy.nc ]; }; then
    # Explicit legacy inputs may still use the pre-binary/ map-root layout.
    DATA_DIR=..
  else
    printf '[SKIP] No ../binary directory; NetCDF maps do not require GrADS CTL files.\n'
    exit 0
  fi
fi

STATUS=0
# set -- rebuilds the argument list passed to each generator invocation.
set --
[ "$DRY_RUN" -eq 0 ] || set -- "$@" --dry-run
[ "$OVERWRITE" -eq 1 ] || set -- "$@" --no-overwrite

# Explicit single-file mode does not scan unrelated base/high-resolution data.
if [ -n "$INPUT" ]; then
  [ -z "$VARIABLES" ] || set -- "$@" --variables "$VARIABLES"
  [ -z "$REFERENCE" ] || set -- "$@" --reference-binary "$REFERENCE"
  exec "$PYTHON_CMD" "$GENERATOR" --map-dir "$DATA_DIR" --input "$INPUT" "$@"
fi

# The generator examines only .bin files that already exist in each directory.
printf '\n==================================================\n'
printf '[STEP 1/2] Generate CTLs for the base map\n'
printf '==================================================\n\n'
"$PYTHON_CMD" "$GENERATOR" --map-dir "$DATA_DIR" "$@" || STATUS=1
printf '\n'

# High-resolution grids provide their geometry in location.txt.
for LOCATION in "$DATA_DIR"/*/location.txt
do
  [ -f "$LOCATION" ] || continue
  # Remove the /location.txt suffix to get the high-resolution map directory.
  MAP_DIR=${LOCATION%/location.txt}
  printf '\n==================================================\n'
  printf '[STEP 2/2] Generate CTLs for high-resolution map %s\n' "$MAP_DIR"
  printf '==================================================\n\n'
  "$PYTHON_CMD" "$GENERATOR" --map-dir "$MAP_DIR" "$@" || STATUS=1
  printf '\n'
done

# Variants reuse standard CSV definitions; concrete names remain Shell settings.
for ENTRY in $VARIANTS; do
  PATTERN=${ENTRY%%:*}
  REFERENCE=${ENTRY#*:}
  # Intentional glob expansion: process existing map-root matches only.
  for BINARY in "$DATA_DIR"/$PATTERN; do
    [ -f "$BINARY" ] || continue
    printf '\nGenerate variant CTL: %s (reference %s)\n' "${BINARY##*/}" "$REFERENCE"
    "$PYTHON_CMD" "$GENERATOR" --map-dir "$DATA_DIR" --input "${BINARY##*/}" --reference-binary "$REFERENCE" "$@" || STATUS=1
  done
done

if [ "$STATUS" -eq 0 ]; then
  printf '\n==================================================\n'
  # ${0##*/} prints only this script's filename in the success message.
  printf '[SUCCESS] %s\n' "${0##*/}"
  printf '==================================================\n'
fi

exit "$STATUS"
