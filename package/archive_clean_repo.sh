#!/usr/bin/env bash
# Extract committed beta sources; never overlay additional data or build models.
set -euo pipefail

# ============================================================
# User settings
# ============================================================

VER="v5b01_$(date +%Y%m%d)"  # Local execution date; a fixed version is also allowed.

# Output: package/repo_clean_${VER}/

# ============================================================
# User settings end here
# ============================================================

# CDPATH= keeps directory discovery independent of shell search settings.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO_ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)
HELPER="$SCRIPT_DIR/archive_clean_repo.py"
EXCLUDES="$SCRIPT_DIR/package_source_exclude.txt"
OUTPUT="$SCRIPT_DIR/repo_clean_${VER}"
COMMIT=$(git -C "$REPO_ROOT" rev-parse --verify 'HEAD^{commit}')
BRANCH=$(git -C "$REPO_ROOT" symbolic-ref --quiet --short HEAD || printf '%s' 'HEAD (detached)')
ARCHIVE_DATE=$(date '+%Y-%m-%dT%H:%M:%S%z')

DRY_RUN=false
case "${1:-}" in
    --dry-run) DRY_RUN=true ;;
    '') ;;
    *) printf 'Usage: %s [--dry-run]\n' "$0" >&2; exit 2 ;;
esac
if [ "$#" -gt 1 ]; then
    printf 'Usage: %s [--dry-run]\n' "$0" >&2
    exit 2
fi

python3 "$HELPER" plan "$REPO_ROOT" "$COMMIT" "$EXCLUDES" "$OUTPUT" "$VER" "$BRANCH"
if "$DRY_RUN"; then
    printf '\n[SUCCESS] Dry-run only; no output created.\n'
    exit 0
fi

# Only this invocation's mktemp directory is removed, including on a failed pipe.
TEMP_DIR=$(mktemp -d "$SCRIPT_DIR/.repo_clean_tmp.XXXXXXXX")
cleanup() { rm -rf -- "$TEMP_DIR"; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# End of error handling.

mkdir "$TEMP_DIR/tree"
printf '\n[STEP 1/2] Extract committed source %s\n' "$COMMIT"
git -C "$REPO_ROOT" archive --format=tar "$COMMIT" | tar -xf - -C "$TEMP_DIR/tree"

printf '\n[STEP 2/2] Exclude, verify and publish clean source\n'
python3 "$HELPER" finish "$REPO_ROOT" "$COMMIT" "$EXCLUDES" "$OUTPUT" "$VER" "$BRANCH" "$TEMP_DIR/tree" "$ARCHIVE_DATE"
printf '\n[SUCCESS] Clean Git source: %s\n' "$OUTPUT"
