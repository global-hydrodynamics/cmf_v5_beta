#!/bin/sh
set -eu

echo "=================================================="
echo "Example: Convert custom NetCDF maps to Binary"
echo "=================================================="
echo "Usage: ./conv_nc2bin.sh INPUT.nc REFERENCE"
echo "  INPUT.nc  : NetCDF file in the parent map directory"
echo "  REFERENCE : Standard map definition in map_variables.csv"
echo "Output: ../binary/<input-name>.bin"
echo ""
echo "Converting two sample maps:"
echo "  subbsn-sample.nc -> binary/subbsn-sample.bin (reference: subbsn)"
echo "  subcol-sample.nc -> binary/subcol-sample.bin (reference: subcol)"
echo ""

./conv_nc2bin.sh subbsn-sample.nc subbsn
./conv_nc2bin.sh subcol-sample.nc subcol
