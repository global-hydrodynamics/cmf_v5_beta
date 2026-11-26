#!/bin/sh
set -eu

echo "=================================================="
echo "Example: Calculate the upstream basin of a river cell"
echo "=================================================="
echo "Usage: ./calc_upbasin.sh xy IX IY [OUTPUT.nc]"
echo ""
echo "  IX, IY : One-based CaMa-Flood grid indices"
echo "  Output : NetCDF upstream-basin mask"
echo "           1 = upstream basin"
echo "           0 = other river cells"
echo "       -9999 = outside river network"
echo ""
echo "Use get_river_point_info.sh to confirm the target cell"
echo "before calculating its upstream basin."
echo ""

IX=62
IY=93
OUTPUT="./upbasin-sample.nc"         # Sample output in script_analysis/.
#OUTPUT="../upbasin-${IX}-${IY}.nc"  # Alternative: map root.

echo "Example: Calculate the upstream basin for grid ($IX, $IY)"
echo "Output: $OUTPUT"
echo ""

./calc_upbasin.sh xy "$IX" "$IY" "$OUTPUT"
