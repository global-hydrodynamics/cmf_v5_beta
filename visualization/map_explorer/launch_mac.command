#!/bin/bash
# Double-click in Finder or run in Terminal. Missing dependencies trigger a [y/N] setup prompt.
set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -z "${PYTHON:-}" ]; then
    if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
        PYTHON="$VIRTUAL_ENV/bin/python"
    fi
fi
if [ -z "${PYTHON:-}" ]; then
    for candidate in "$SCRIPT_DIR/.venv/bin/python" \
        "$REPO_ROOT/.venv/bin/python" /opt/homebrew/bin/python3 /usr/local/bin/python3; do
        if [ -x "$candidate" ]; then
            PYTHON="$candidate"
            break
        fi
    done
fi
PYTHON="${PYTHON:-python3}"
export PYTHONDONTWRITEBYTECODE=1
export BOKEH_RESOURCES=server
export MPLBACKEND=Agg
export MPLCONFIGDIR="${MPLCONFIGDIR:-$SCRIPT_DIR/output/.matplotlib}"

if "$PYTHON" "$SCRIPT_DIR/code/launch_desktop.py" "$@"; then
    exit 0
else
    launch_status=$?
    printf '\n[ERROR] Launch failed. See the message above and README.md.\n'
    read -r -p "Press Enter to close this window..." _reply || true
    exit "$launch_status"
fi
