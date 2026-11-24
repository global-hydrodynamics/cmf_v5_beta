#!/usr/bin/env bash
set -euo pipefail

# Internal path anchors; user paths below are independent of the caller's directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TUTORIAL_DIR="$SCRIPT_DIR"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
_PYTHON_DEFAULT="$REPO_ROOT/.venv/bin/python"
if [[ ! -x "$_PYTHON_DEFAULT" ]]; then _PYTHON_DEFAULT="python3"; fi

# User settings
# ----------------------------------------------------------------------
PYTHON="${PYTHON:-$_PYTHON_DEFAULT}"                                  # Existing PYTHON override; default .venv, otherwise python3 (unchanged fallback).
SOURCE_DIR="$TUTORIAL_DIR/observation/stations_data"                  # Supplied three-station 2021 CSV/NetCDF and station table; source files are read-only.
METADATA_DIR="$TUTORIAL_DIR/metadata"                                 # Step04 inventory/dataset JSON output directory.

# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

"$PYTHON" "$TUTORIAL_DIR/script/s04-inspect_discharge.py"  --tutorial-dir "$TUTORIAL_DIR" --source-dir "$SOURCE_DIR" --metadata-dir "$METADATA_DIR"
