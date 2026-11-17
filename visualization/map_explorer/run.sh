#!/usr/bin/env bash
# Launch a read-only map browser; the shared Python launcher asks before environment setup.
set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -z "${PYTHON:-}" ]; then
    if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
        PYTHON="$VIRTUAL_ENV/bin/python"
    elif [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
        PYTHON="$SCRIPT_DIR/.venv/bin/python"
    elif [ -x "$REPO_ROOT/.venv/bin/python" ]; then
        PYTHON="$REPO_ROOT/.venv/bin/python"
    else
        PYTHON=python3
    fi
fi

export PYTHONDONTWRITEBYTECODE=1
export BOKEH_RESOURCES=server
export MPLBACKEND=Agg
# Keep the terminal entry point's default port; an explicit --port still takes precedence.
exec "$PYTHON" "$SCRIPT_DIR/launch_desktop.py" --port 5006 "$@"
