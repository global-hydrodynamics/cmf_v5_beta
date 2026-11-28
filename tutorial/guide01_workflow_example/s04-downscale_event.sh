#!/bin/sh
# Derive event flddph and downscale Control and Deep Channel with the Tutorial-local Python package.
set -eu
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"
PYTHON="$CMF_V50_ROOT/.venv/bin/python"
MAPDIR="$CMF_V50_ROOT/map/mekong_15min"
DOWNSCALER="$SCRIPT_DIR/downscale_flddph/script/downscale_flddph.py"

# User-requested Mekong lower-basin extent for Figure 6.
WEST=102
EAST=108
SOUTH=9
NORTH=15
RES=1min
FORCE=0
if [ "$#" -gt 0 ]; then
    [ "$#" -eq 1 ] && [ "$1" = "--force" ] || { echo "Usage: $0 [--force]" >&2; exit 2; }
    FORCE=1
fi

cmf_check_init "Guide01 one-minute event downscaling"

[ -x "$PYTHON" ] || { echo "[ERROR] Python environment missing: $PYTHON" >&2; exit 1; }
[ -f "$DOWNSCALER" ] || { echo "[ERROR] Tutorial-local Python downscaler missing: $DOWNSCALER" >&2; exit 1; }
[ -f "$SCRIPT_DIR/analysis/event_selection.csv" ] || {
    echo "[ERROR] Run a01-analyze_outputs.py first to select the event." >&2; exit 1;
}
for layer in catmxy flddif rivwth downxy; do
    [ -s "$MAPDIR/1min/1min.$layer.nc" ] || { echo "[ERROR] Missing 1min NetCDF layer: $MAPDIR/1min/1min.$layer.nc" >&2; exit 1; }
done
[ -s "$MAPDIR/nextxy.nc" ] && [ -s "$MAPDIR/uparea.nc" ] || {
    echo "[ERROR] Missing NetCDF network maps required by the downscaler." >&2; exit 1;
}
[ -s "$MAPDIR/params.nml" ] && [ -s "$MAPDIR/1min/location.csv" ] || {
    echo "[ERROR] Missing params.nml or 1min/location.csv." >&2; exit 1;
}

STEP=1
for CASE in control deep_channel; do
    INPUT_DIR="$SCRIPT_DIR/out/downscaling/$CASE/input"
    OUTPUT_DIR="$SCRIPT_DIR/out/downscaling/$CASE"
    INPUT="$INPUT_DIR/flddph_event.nc"
    OUTPUT="$OUTPUT_DIR/flddph_1min_provisional.nc"
    mkdir -p "$INPUT_DIR" "$OUTPUT_DIR"
    if [ -e "$OUTPUT" ] && [ "$FORCE" -eq 0 ]; then
        echo "[ERROR] Output exists (use --force to replace): $OUTPUT" >&2; exit 1;
    fi
    [ "$FORCE" -eq 0 ] || rm -f "$OUTPUT"
    cmf_check_step "$STEP" 4 "Prepare the $CASE event flddph NetCDF"
    "$PYTHON" "$SCRIPT_DIR/a02-prepare_downscale_input.py" --case "$CASE" --output "$INPUT"
    STEP=$((STEP + 1))
    cmf_check_step "$STEP" 4 "Downscale $CASE at one-minute resolution in ${WEST}-${EAST}E, ${SOUTH}-${NORTH}N"
    "$PYTHON" "$DOWNSCALER" --input "$INPUT" --map-dir "$MAPDIR" --resolution "$RES" \
        --map-format netcdf --west "$WEST" --east "$EAST" --south "$SOUTH" --north "$NORTH" --output "$OUTPUT"
    [ -s "$OUTPUT" ] || { echo "[ERROR] Downscaler did not create $OUTPUT" >&2; exit 1; }
    "$PYTHON" - "$OUTPUT" "$WEST" "$NORTH" <<'PYTHON_CHECK'
import sys
from pathlib import Path
import netCDF4
import numpy as np
path = Path(sys.argv[1])
west, north = float(sys.argv[2]), float(sys.argv[3])
with netCDF4.Dataset(path) as ds:
    if ds.variables['flddph'].dimensions != ('lat', 'lon'):
        raise SystemExit('[ERROR] Expected flddph(lat,lon)')
    if ds.variables['flddph'].units != 'm':
        raise SystemExit('[ERROR] Expected flddph units=m')
    if getattr(ds.variables['flddph'], '_FillValue', None) != np.float32(-9999.0):
        raise SystemExit('[ERROR] Expected flddph _FillValue=-9999')
    values = np.ma.asarray(ds.variables['flddph'][:], dtype=np.float32)
    lon = np.asarray(ds.variables['lon'][:], dtype=np.float64)
    lat = np.asarray(ds.variables['lat'][:], dtype=np.float64)
expected_lon = west + (np.arange(360) + 0.5) / 60.0
expected_lat = north - (np.arange(360) + 0.5) / 60.0
if not np.allclose(lon, expected_lon, rtol=0, atol=1.0e-5) or not np.allclose(lat, expected_lat, rtol=0, atol=1.0e-5):
    raise SystemExit('[ERROR] Downscaled NetCDF coordinates do not match requested 1-minute grid')
valid = values.compressed()
if values.shape != (360, 360) or not valid.size:
    raise SystemExit(f'[ERROR] Invalid grid or no valid pixels: {values.shape}, {valid.size}')
if np.any(valid < 0):
    raise SystemExit('[ERROR] Negative inundation depth found')
print(f'[CHECK] cells={values.size}; assigned={valid.size}; min={valid.min():.6g} m; max={valid.max():.6g} m; bytes={path.stat().st_size}')
PYTHON_CHECK
    echo "$CASE downscaling output: $OUTPUT"
    STEP=$((STEP + 1))
done
echo "[WARNING] Reference-point, event, and regional-area choices remain provisional pending researcher review."
cmf_check_success
