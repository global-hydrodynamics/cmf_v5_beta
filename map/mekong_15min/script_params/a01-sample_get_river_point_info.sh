#!/bin/sh
set -eu

echo "=================================================="
echo "Example: Get river information at a selected point"
echo "NOTE: This usage example is designed for the mekong_15min map."
echo "      The example coordinates are not intended for other maps."
echo "=================================================="
echo "These example coordinates are for the Mekong sample map, not arbitrary maps."
echo "Usage:"
echo "  ./get_river_point_info.sh xy IX IY"
echo "  ./get_river_point_info.sh latlon LAT LON"
echo ""
echo "  xy     : One-based CaMa-Flood grid indices"
echo "  latlon : Geographic coordinates in degrees (latitude first)"
echo ""
echo "Example 1: Query by grid indices (62, 93)"
echo ""

./get_river_point_info.sh xy 62 93

echo ""
echo "Example 2: Query by geographic coordinates (11.579, 104.946)"
echo ""

./get_river_point_info.sh latlon 11.579 104.946
