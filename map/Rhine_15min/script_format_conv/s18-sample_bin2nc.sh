#!/bin/sh
set -eu

echo "=================================================="
echo "Example: Convert custom Binary maps to NetCDF"
echo "=================================================="
echo "Usage: ./conv_bin2nc.sh INPUT.bin REFERENCE"
echo "  INPUT.bin : Binary file in the parent map's binary/ directory"
echo "  REFERENCE : Standard map definition in map_variables.csv"
echo "Output: ../<input-name>.nc"
echo ""
echo "Converting two sample maps:"
echo "  binary/subbsn-sample.bin -> subbsn-sample.nc (reference: subbsn)"
echo "  binary/subcol-sample.bin -> subcol-sample.nc (reference: subcol)"
echo ""

./conv_bin2nc.sh subbsn-sample.bin subbsn
./conv_bin2nc.sh subcol-sample.bin subcol
