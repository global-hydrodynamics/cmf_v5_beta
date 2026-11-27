#!/bin/sh
# Convert standard v5 Namelist/CSV metadata to legacy map TXT metadata.
set -eu

if [ "$#" -ne 0 ]; then
    echo "Usage: ./s32-meta2txt.sh" >&2
    exit 2
fi

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

CODE_DIR="$CMF_V50_ROOT/map/tools/code"

cmf_check_init "Convert standard map metadata to legacy TXT formats"

cmf_check_step 1 1 "Validate and convert metadata in the parent map directory"
"$PYTHON_CMD" "$CODE_DIR/convert_map_metadata.py" meta2txt ..

cmf_check_success
