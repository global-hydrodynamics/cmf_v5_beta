"""Geographic bounds and requested frame shape are separate display concepts."""

import math

ASPECTS = {"square": 1.0, "landscape": 4 / 3, "portrait": 3 / 4}
ASPECT_LABELS = {
    "Square (1:1)": "square",
    "Landscape (4:3)": "landscape",
    "Portrait (3:4)": "portrait",
    "Custom": "custom",
}


def geographic_ratio(extent):
    w, e, s, n = extent
    return (e - w) * max(0.05, math.cos(math.radians((s + n) / 2))) / (n - s)


def aspect_extent(extent, geometry, ratio):
    w, e, s, n = extent
    lon, lat = (w + e) / 2, (s + n) / 2
    cosine = max(0.05, math.cos(math.radians(lat)))
    # Keep center exactly. Shrink scale only if the requested frame would leave domain.
    dy = min(
        n - s,
        2 * min(lat - geometry.south, geometry.north - lat),
        2 * min(lon - geometry.west, geometry.east - lon) * cosine / ratio,
    )
    if dy <= 0:
        raise ValueError("Cannot fit an aspect at this domain boundary")
    dx = dy * ratio / cosine
    return lon - dx / 2, lon + dx / 2, lat - dy / 2, lat + dy / 2


def translated_extent(extent, geometry, lon, lat):
    if not all(math.isfinite(v) for v in (lon, lat)):
        raise ValueError("Map center coordinates must be finite")
    if geometry.periodic:
        lon = geometry.west + (lon - geometry.west) % 360
    if not geometry.west <= lon <= geometry.east or not geometry.south <= lat <= geometry.north:
        raise ValueError("Requested center lies outside the map domain")
    dx, dy = extent[1] - extent[0], extent[3] - extent[2]
    if dx > geometry.east - geometry.west + 1e-8 or dy > geometry.north - geometry.south + 1e-8:
        raise ValueError("Current viewport spans exceed the map domain")
    cx = min(max(lon, geometry.west + dx / 2), geometry.east - dx / 2)
    cy = min(max(lat, geometry.south + dy / 2), geometry.north - dy / 2)
    return cx - dx / 2, cx + dx / 2, cy - dy / 2, cy + dy / 2


def allocated_frame(extent, bounds, ratio):
    height = max(1, math.floor(min(max(1, bounds[1] - 85), max(1, bounds[0] - 150) / ratio)))
    width = max(1, round(height * ratio))
    actual = geographic_ratio(extent)
    if abs(actual - ratio) < 1e-8:
        return (width, height), (width, height)
    # Same degree spans at a new latitude cannot also retain the exact physical
    # ratio. Letterbox geographic data, never stretch axes or silently zoom.
    data_h = max(1, math.floor(min(height, width / actual)))
    return (max(1, round(data_h * actual)), data_h), (width, height)
