#!/usr/bin/env bash
# Launch a read-only map browser; the shared Python launcher asks before environment setup.
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
exec "$PYTHON" "$SCRIPT_DIR/launch_desktop.py" "$MAP_DIR" --port 5006 "$@"
