#!/bin/bash
# Deprecated compatibility entrypoint; use s18-sample_bin2nc.sh directly.
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
ARGS=()
for ARG in "$@"; do
    [ "$ARG" != --force ] || continue
    ARGS+=("$ARG")
done
exec bash "$SCRIPT_DIR/s18-sample_bin2nc.sh" "${ARGS[@]}"
