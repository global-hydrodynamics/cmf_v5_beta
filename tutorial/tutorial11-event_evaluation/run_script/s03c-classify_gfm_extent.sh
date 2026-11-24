#!/usr/bin/env bash
set -euo pipefail

# Internal path anchors; user paths below are independent of the caller's directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TUTORIAL_DIR="$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$TUTORIAL_DIR/../.." && pwd -P)"

# User settings
# ----------------------------------------------------------------------
PYTHON_CMD="${PYTHON_CMD:-python3}"                                   # Python executable; existing PYTHON_CMD override is supported.
SELECTION_JSON="$TUTORIAL_DIR/metadata/03a_selected_passes.json"      # Authoritative pass selection; distinct passes are not merged.
DOMAIN_JSON="$TUTORIAL_DIR/metadata/02_domain_selection.json"         # Authoritative target bbox [west,south,east,north degrees].
ATLANTIS_ROOT="$TUTORIAL_DIR/Atlantis"                                # Existing Step3b manifests and native COG root.
OUTPUT_DIR="$TUTORIAL_DIR/observation/GFM_extent"                     # Classification COG/provenance output directory.
OVERWRITE=1                                                           # 1: replace derived classification; 0: preserve existing outputs.

# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

# The guarded array expansion below also supports an empty list under Bash 3.2 with set -u.
EXTRA_ARGS=()
if [[ "$OVERWRITE" == "1" ]]; then EXTRA_ARGS+=(--force); fi
"$PYTHON_CMD" -B "$TUTORIAL_DIR/script/s03c-mosaic_gfm_extent.py"  \
    --tutorial-root "$TUTORIAL_DIR" \
    --selection-json "$SELECTION_JSON" \
    --domain-json "$DOMAIN_JSON"  \
    --atlantis-root "$ATLANTIS_ROOT" \
    --output-dir "$OUTPUT_DIR" ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}
