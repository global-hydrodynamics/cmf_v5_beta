"""Flat Explorer settings referencing the canonical Gallery CSV, not a registry."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from scene import OVERLAY_DEFAULTS
from map_products import AREA_PALETTES, AREA_COLOR_STYLES

VISIBLE_PRESETS = ("p01-f01a", "p01-f01d", "p01-f02a", "p01-f03a", "p01-f03c", "p01-f04b", "p01-f05f")

BOOLEAN_FIELDS = {
    "arrows",
    "channel",
    "overland",
    "outlets",
    "headwater",
    "coarse_grid",
    "catchment_boundaries",
    "channel_pixels",
    "bif_classes",
}
NUMBER_FIELDS = {"background_opacity", "line_width", "bif_width", "west", "east", "south", "north"}
CHOICES = {
    "background_method": {"default", "subbasin_context"},
    "network_geometry": {"straight", "gallery_arcs"},
    "background": {"coarse", "catchment", "elevtn", "difference", "flddif", "none"},
    "representation": {"off", "grid_center", "outlet_vector"},
    "color_mode": {"uniform", "connection_type", "upstream_area"},
    "width_mode": {"uniform", "upstream_area"},
    "classification": {"quartiles", "six_log", "continuous", "fixed"},
    "area_palette": set(AREA_PALETTES),
    "area_color_style": set(AREA_COLOR_STYLES),
    "terrain_palette": {"gray", "pale_terrain"},
}


class PresetLibrary:
    def __init__(self, settings_path=None, catalog_path=None):
        home = Path(__file__).resolve().parent
        self.messages, self.presets = [], {}
        self.catalog_path = Path(catalog_path or home.parent / "visualization_catalog.csv")
        try:
            with self.catalog_path.open(encoding="utf-8-sig", newline="") as stream:
                canonical = {}
                for row in csv.DictReader(stream):
                    identity = row["visualization_id"]
                    if identity in canonical:
                        raise ValueError(f"Duplicate canonical Gallery ID: {identity}")
                    canonical[identity] = row
            with Path(settings_path or home / "presets.csv").open(encoding="utf-8-sig", newline="") as stream:
                for original in csv.DictReader(stream):
                    row = {key: value.strip() for key, value in original.items()}
                    identity = row["gallery_id"]
                    if identity not in canonical or identity in self.presets:
                        raise ValueError(f"Unknown/duplicate Gallery reference: {identity}")
                    row.setdefault("background_method", "default")
                    row.setdefault("network_geometry", "straight")
                    row.setdefault("background_opacity", "1")
                    row.setdefault("flexible_color", "#e67e22")
                    for key in BOOLEAN_FIELDS:
                        if row[key].lower() not in ("true", "false", "1", "0"):
                            raise ValueError(f"{identity}:{key} must be boolean")
                        row[key] = row[key].lower() in ("true", "1")
                    for key in NUMBER_FIELDS:
                        row[key] = float(row[key])
                        if not np.isfinite(row[key]):
                            raise ValueError(f"{identity}:{key} must be finite")
                    row.setdefault(
                        "area_color_style",
                        (
                            "gallery_quartiles"
                            if row["classification"] == "quartiles"
                            else (
                                "gallery_continuous"
                                if row["classification"] == "six_log" and row["area_palette"] == "shade_rainbow"
                                else "palette"
                            )
                        ),
                    )
                    for key, choices in CHOICES.items():
                        if row[key] not in choices:
                            raise ValueError(f"{identity}:{key} unsupported setting")
                    if not 0 <= row["background_opacity"] <= 1:
                        raise ValueError(f"{identity}: invalid opacity")
                    if not (0.2 <= row["line_width"] <= 4 and 0.2 <= row["bif_width"] <= 5):
                        raise ValueError(f"{identity}: invalid line widths")
                    if not (row["west"] < row["east"] and row["south"] < row["north"]):
                        raise ValueError(f"{identity}: invalid suggested extent")
                    self.presets[identity] = (row, canonical[identity])
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.presets.clear()
            self.messages.append(f"Gallery presets unavailable: {exc}")

    def missing_products(self, identity, reader, scene):
        row, _ = self.presets[identity]
        missing = []
        if row.get("background_method") == "subbasin_context" and "bsncol" not in reader.sources:
            missing.append("bsncol")
        if row["variable"] not in reader.sources:
            missing.append(row["variable"])
        if row["network_source"] != "off" and row["network_source"] not in reader.network_sources:
            missing.append(row["network_source"])
        if row["color_mode"] == "upstream_area" or row["width_mode"] == "upstream_area" or row["headwater"]:
            if "uparea" not in reader.sources:
                missing.append("uparea")
        if (
            row["representation"] == "outlet_vector"
            or row["channel"]
            or row["overland"]
            or row["outlets"]
            or row["headwater"]
        ) and scene.products.outlet_source is None:
            missing.append("lonlat (stored outlet coordinates)")
        if (row["channel"] or row["overland"]) and scene.products.bif_path is None:
            missing.append("bifprm.nc")
        required = set()
        if row["background"] == "catchment" or row["catchment_boundaries"] or row["headwater"]:
            required.add("catmxy")
        if row["channel_pixels"]:
            required.update(("catmxy", "visual"))
        if row["background"] in ("elevtn", "difference", "flddif"):
            required.add("elevtn")
        if row["background"] == "flddif":
            required.add("flddif")
        if required and not any(required.issubset(tile.files) for tile in scene.tiles.values()):
            missing.append("one high-resolution tile with " + ", ".join(sorted(required)))
        return list(dict.fromkeys(missing))

    def state(self, identity, app, gallery_extent=False):
        """Validate dependent inputs before changing any visible application state."""
        row, _ = self.presets[identity]
        missing = self.missing_products(identity, app.reader, app.scene)
        if missing:
            raise ValueError("Preset unavailable; missing: " + ", ".join(missing))
        if row["representation"] == "outlet_vector" or row["channel"] or row["overland"]:
            a, b = app.scene.products.outlets
            if not np.any(np.isfinite(a) & np.isfinite(b)):
                raise ValueError("Preset unavailable: no valid stored outlets")
        if row["channel"] or row["overland"]:
            data = app.scene.products.bifurcations
            if row["channel"] and not data["channel"].any():
                raise ValueError("Preset unavailable: no valid channel bifurcations")
            if row["overland"] and data["channel"].all():
                raise ValueError("Preset unavailable: no valid overland bifurcations")
        state = app.settings()
        extent = [row[key] for key in ("west", "east", "south", "north")] if gallery_extent else list(app.extent)
        if gallery_extent:
            app.reader.geometry.validate_extent(extent)
        state.update(
            variable=row["variable"],
            palette=row["palette"],
            scale="auto",
            limits=None,
            network=row["network_source"],
            extent=extent,
        )
        state["network_options"].update(
            width=row["line_width"],
            classification=row["classification"],
            area_palette=row["area_palette"],
            area_color_style=row["area_color_style"],
            area_limits=None,
            color_area=row["color_mode"] == "upstream_area",
            distinguish=row["color_mode"] == "connection_type",
            scale_width=row["width_mode"] == "upstream_area",
            color="#000000",
            flexible_color=row["flexible_color"],
        )
        overlays = {**OVERLAY_DEFAULTS, **{key: row.get(key, default) for key, default in OVERLAY_DEFAULTS.items()}}
        required = set()
        if row["background"] == "catchment" or row["headwater"] or row["catchment_boundaries"]:
            required.add("catmxy")
        if row["channel_pixels"]:
            required.update(("catmxy", "visual"))
        if row["background"] in ("elevtn", "difference", "flddif"):
            required.add("elevtn")
        if row["background"] == "flddif":
            required.add("flddif")
        tile = app.hires_source.value
        if required and (tile not in app.scene.tiles or not required.issubset(app.scene.tiles[tile].files)):
            tile = next(key for key, value in app.scene.tiles.items() if required.issubset(value.files))
        state["basemap"] = dict(show=False, opacity=1.0)
        state["layers"] = dict(
            coarse_palette_range=[0.0, 1.0],
            auto_limits_policy="gallery",
            background=row["background"],
            tile=tile,
            terrain_palette=row["terrain_palette"],
            representation=row["representation"],
            arrows=row["arrows"],
            arrow_size=7 if row["arrows"] else 0,
            overlays=overlays,
            background_opacity=row["background_opacity"],
            background_method=row["background_method"],
            network_geometry=row["network_geometry"],
            network_detail=app.river_ui.detail.value,
            network_budget=app.river_ui.budget.value,
            highres_style=dict(palette="gallery", scale="gallery", limits=None, palette_range=[0.0, 1.0]),
        )
        if gallery_extent:
            from view_controls import geographic_ratio

            state["viewport"] = {"aspect": "custom", "frame_ratio": geographic_ratio(extent)}
        state["background_ui"] = app.background_ui.config_for(row["background"], row["variable"])
        return state
