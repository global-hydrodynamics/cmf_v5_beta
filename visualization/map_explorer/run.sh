#!/usr/bin/env bash
# Launch an independent, read-only map browser; never install dependencies here.
set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ "$#" -lt 1 ]; then
    printf 'Usage: %s MAP_DIR [--port 5006] [--no-browser]\n' "$0" >&2
    exit 2
fi

MAP_DIR="$1"
shift
if [ ! -d "$MAP_DIR" ] && [ -d "$REPO_ROOT/$MAP_DIR" ]; then
    MAP_DIR="$REPO_ROOT/$MAP_DIR"
fi
if [ ! -d "$MAP_DIR" ]; then
    printf '[ERROR] Map directory not found: %s\n' "$MAP_DIR" >&2
    exit 2
fi
MAP_DIR="$(cd "$MAP_DIR" && pwd)"

if [ -z "${PYTHON:-}" ]; then
    if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
        PYTHON="$VIRTUAL_ENV/bin/python"
    elif [ -x "$REPO_ROOT/.venv/bin/python" ]; then
        PYTHON="$REPO_ROOT/.venv/bin/python"
    elif [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
        PYTHON="$SCRIPT_DIR/.venv/bin/python"
    else
        PYTHON=python3
    fi
fi

if ! "$PYTHON" -c 'import numpy, netCDF4, matplotlib, panel, bokeh' 2>/dev/null; then
    printf '[ERROR] Missing GUI dependencies in %s. See %s/README.md for isolated installation.\n' "$PYTHON" "$SCRIPT_DIR" >&2
    exit 1
fi

export PYTHONDONTWRITEBYTECODE=1
export BOKEH_RESOURCES=server
export MPLBACKEND=Agg
exec "$PYTHON" "$SCRIPT_DIR/app.py" "$MAP_DIR" "$@"
