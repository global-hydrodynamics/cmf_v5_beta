"""Validated, human-readable display settings; no execution on config load."""

import json
import warnings
from pathlib import Path


def save_settings(path, settings):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, allow_nan=False) + "\n")
    return path


def load_settings(content, reader):
    if len(content) > 65536:
        raise ValueError("Settings JSON must be smaller than 64 KiB")
    data = json.loads(content)
    required = {"version", "map_path", "variable", "extent", "scale", "palette", "limits", "network", "network_options"}
    if not isinstance(data, dict) or not required.issubset(data) or data["version"] not in (1, 2):
        raise ValueError("Unsupported settings schema/version")
    notes = []
    unknown = set(data) - required - {"layers", "background_ui", "viewport", "basemap", "point_select"}
    if unknown:
        notes.append("Ignored unknown settings: " + ", ".join(sorted(unknown)))
        for key in unknown:
            data.pop(key)
    if Path(data["map_path"]).expanduser().resolve() != reader.path:
        raise ValueError("Settings refer to another map; use Map Dataset / Load Map first, then load this JSON again")
    if data["variable"] not in reader.sources:
        raise ValueError("Settings variable is not available in this map")
    reader.geometry.validate_extent(data["extent"])
    from view_controls import ASPECTS, geographic_ratio

    view = data.get("viewport", {"aspect": "custom", "frame_ratio": geographic_ratio(data["extent"])})
    if (
        not isinstance(view, dict)
        or set(view) != {"aspect", "frame_ratio"}
        or view["aspect"] not in (*ASPECTS, "custom")
    ):
        raise ValueError("Invalid viewport settings")
    ratio = view["frame_ratio"]
    import math

    if isinstance(ratio, bool) or not isinstance(ratio, (float, int)) or not math.isfinite(ratio) or ratio <= 0:
        raise ValueError("Viewport frame_ratio must be positive and finite")
    if view["aspect"] in ASPECTS and abs(ratio - ASPECTS[view["aspect"]]) > 1e-8:
        raise ValueError("Viewport aspect and frame_ratio disagree")
    data["viewport"] = view
    if data["scale"] not in ("auto", "linear", "log") or data["palette"] not in (
        "gray",
        "gray_r",
        "viridis",
        "terrain",
        "magma",
        "Blues",
        "YlGnBu",
        "basin_pastel",
        "subcol_pastel",
        "subcol_gray",
    ):
        raise ValueError("Unsupported scale/palette")
    if data["network"] == "nextxy_noedge":
        data["network"] = "nextxy" if "nextxy" in reader.network_sources else "off"
        notes.append("Legacy nextxy_noedge display source replaced by " + data["network"]
                     + "; River Map now uses complete nextxy connectivity")
    if data["network"] != "off" and data["network"] not in reader.network_sources:
        raise ValueError("Settings network is not available")
    options = data["network_options"]
    base_options = {"width", "color", "flexible_color", "distinguish", "scale_width", "color_area"}
    if not isinstance(options, dict) or not base_options.issubset(options):
        raise ValueError("Unsupported network options")
    for key in set(options) - base_options - {"classification", "area_palette", "area_limits", "area_color_style"}:
        notes.append("Ignored network option: " + key)
        options.pop(key)
    options.setdefault("classification", "fixed")
    options.setdefault("area_palette", "viridis")
    from map_products import AREA_PALETTES, AREA_COLOR_STYLES, validate_area_limits

    if options["area_palette"] not in AREA_PALETTES:
        raise ValueError("Unsupported network area palette")
    options.setdefault(
        "area_color_style",
        (
            "gallery_quartiles"
            if options["classification"] == "quartiles"
            else (
                "gallery_continuous"
                if options["classification"] == "six_log" and options["area_palette"] == "shade_rainbow"
                else "palette"
            )
        ),
    )
    if options["area_color_style"] not in AREA_COLOR_STYLES:
        raise ValueError("Unsupported network area color style")
    options["area_limits"] = validate_area_limits(options.get("area_limits"))
    if options["classification"] not in ("fixed", "quartiles", "six_log", "continuous"):
        raise ValueError("Unsupported area classification")
    if not isinstance(options["width"], (int, float)) or not 0.2 <= options["width"] <= 4:
        raise ValueError("Line width must be between 0.2 and 4")
    import re

    for name in ("color", "flexible_color"):
        if not isinstance(options[name], str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", options[name]):
            raise ValueError("Colors must have #RRGGBB format")
    for name in ("distinguish", "scale_width", "color_area"):
        if not isinstance(options[name], bool):
            raise ValueError("Network toggles must be boolean")
    limits = data["limits"]
    if limits is not None and (not isinstance(limits, list) or len(limits) != 2):
        raise ValueError("Color limits must contain two numbers")
    if data["version"] == 2:
        from scene import OVERLAY_DEFAULTS
        from hires import discover_tiles
        from map_products import Products

        layers = data.get("layers", {})
        if not isinstance(layers, dict):
            raise ValueError("layers must be an object")
        allowed = {
            "background",
            "tile",
            "terrain_palette",
            "arrows",
            "overlays",
            "representation",
            "background_opacity",
            "highres_style",
            "auto_limits_policy",
            "coarse_palette_range",
            "arrow_size",
            "background_method",
            "network_geometry",
            "network_detail",
            "network_budget",
        }
        for key in set(layers) - allowed:
            notes.append("Ignored layer setting: " + key)
            layers.pop(key)
        layers.setdefault("network_detail", "all")  # Old saved views retain complete networks.
        layers.setdefault("network_budget", 5000)
        if layers["network_detail"] not in ("auto", "all"):
            raise ValueError("Unsupported River detail mode")
        budget = layers["network_budget"]
        if isinstance(budget, bool) or not isinstance(budget, int) or not 1000 <= budget <= 20000:
            raise ValueError("Headwater count threshold must be an integer from 1000 to 20000")
        layers.setdefault("auto_limits_policy", "gallery")
        if layers["auto_limits_policy"] not in ("percentile", "gallery"):
            raise ValueError("Unsupported automatic color-limit reference policy")
        if layers.get("background", "coarse") not in ("none", "coarse", "catchment", "elevtn", "difference", "flddif"):
            raise ValueError("Unsupported background representation")
        if layers.get("terrain_palette", "gray") not in ("gray", "pale_terrain"):
            raise ValueError("Unsupported terrain palette")
        if layers.get("representation", "grid_center") not in ("off", "grid_center", "outlet_vector"):
            raise ValueError("Unsupported network representation")
        if not isinstance(layers.get("arrows", False), bool):
            raise ValueError("arrows must be boolean")
        arrow_size = layers.get("arrow_size", 7 if layers.get("arrows", False) else 0)
        if (
            isinstance(arrow_size, bool)
            or not isinstance(arrow_size, (int, float))
            or not 0 <= arrow_size <= 20
            or int(arrow_size) != arrow_size
        ):
            raise ValueError("Arrow size must be an integer from 0 to 20 px")
        layers["arrow_size"] = int(arrow_size)
        layers["arrows"] = arrow_size > 0
        if layers.get("background_method", "default") not in ("default", "subbasin_context"):
            raise ValueError("Unsupported background method")
        if layers.get("network_geometry", "straight") not in ("straight", "gallery_arcs"):
            raise ValueError("Unsupported network display geometry")
        if layers.get("background_method") == "subbasin_context" and (
            data["variable"] != "subcol" or "bsncol" not in reader.sources
        ):
            raise ValueError("Subbasin context requires subcol and bsncol")
        from map_layers import validate_palette_range

        layers["coarse_palette_range"] = validate_palette_range(layers.get("coarse_palette_range"))
        from background_style import validate_style
        from map_reader import SCHEMA

        if "highres_style" in layers:
            layers["highres_style"] = validate_style(
                layers["highres_style"],
                layers.get("background") == "catchment" and SCHEMA[data["variable"]].logarithmic,
            )
        opacity = layers.get("background_opacity", 1.0)
        import math

        if (
            isinstance(opacity, bool)
            or not isinstance(opacity, (float, int))
            or not math.isfinite(opacity)
            or not 0 <= opacity <= 1
        ):
            raise ValueError("Background opacity must be between 0 and 1")
        tiles = discover_tiles(reader.path, [])
        if layers.get("tile") not in tiles and layers.get("tile") is not None:
            notes.append("High-resolution source missing; using coarse background")
            layers["tile"] = next(iter(tiles), None)
            layers["background"] = "coarse"
            data.pop("background_ui", None)
        if layers.get("representation") == "outlet_vector" and Products(reader).outlet_source is None:
            notes.append("Outlets missing; using grid centers")
            layers["representation"] = "grid_center"
        overlays = layers.get("overlays", {})
        if not isinstance(overlays, dict):
            raise ValueError("overlays must be an object")
        for key in set(overlays) - set(OVERLAY_DEFAULTS):
            notes.append("Ignored overlay: " + key)
            overlays.pop(key)
        for key, value in overlays.items():
            expected = OVERLAY_DEFAULTS[key]
            if isinstance(expected, bool) and not isinstance(value, bool):
                raise ValueError(f"{key} must be boolean")
            if isinstance(expected, str) and (
                not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value)
            ):
                raise ValueError(f"{key} must be #RRGGBB")
            if key == "outlet_size" and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0 <= value <= 20
                or int(value) != value
            ):
                raise ValueError("Outlet Size must be an integer from 0 to 20 px")
            if key == "channel_pixels_opacity":
                if (isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or not 0 <= value <= 1):
                    raise ValueError("Channel Pixels opacity must be between 0 and 1")
            elif isinstance(expected, float) and (not isinstance(value, (int, float)) or not 0.2 <= value <= 5):
                raise ValueError(f"{key} must be between 0.2 and 5")
        data["layers"] = layers
    ui = data.get("background_ui")
    if data["version"] == 1:
        data.pop("background_ui", None)  # v1 always restores its coarse/grid semantics.
    elif ui is not None:
        fields = {"raster_type", "coarse_variable", "highres_variable", "no_background"}
        if not isinstance(ui, dict) or set(ui) != fields:
            raise ValueError("background_ui requires raster_type, coarse_variable, highres_variable and no_background")
        if ui["raster_type"] not in ("coarse", "highres") or not isinstance(ui["no_background"], bool):
            raise ValueError("Invalid background_ui type/toggle")
        if ui["coarse_variable"] not in reader.sources:
            raise ValueError("Saved coarse_variable is unavailable")
        highres = ui["highres_variable"]
        if highres not in (None, "catchment", "elevtn", "flddif", "difference"):
            if (
                not isinstance(highres, str)
                or not highres.startswith("catchment:")
                or highres.split(":", 1)[1] not in reader.sources
            ):
                raise ValueError("Unsupported highres_variable")
        background = data.get("layers", {}).get("background", "coarse")
        expected_background = (
            "none"
            if ui["no_background"]
            else "coarse" if ui["raster_type"] == "coarse" else (highres or "none").split(":", 1)[0]
        )
        if background != expected_background:
            raise ValueError("background_ui disagrees with saved background")
        if background == "coarse" and ui["coarse_variable"] != data["variable"]:
            raise ValueError("coarse_variable disagrees with saved raster variable")
        if background == "catchment":
            inherited = highres.split(":", 1)[1] if ":" in highres else "uparea"
            if inherited != data["variable"]:
                raise ValueError("highres_variable disagrees with inherited catchment field")
    data.setdefault(
        "point_select",
        (
            "grid"
            if data["version"] == 1 or data.get("layers", {}).get("background", "coarse") in ("none", "coarse")
            else "catchment"
        ),
    )
    if data["point_select"] not in ("grid", "catchment"):
        raise ValueError("Point Select must be grid or catchment")
    basemap = data.setdefault("basemap", dict(show=False, opacity=1.0))
    if not isinstance(basemap, dict) or set(basemap) != {"show", "opacity"} or not isinstance(basemap["show"], bool):
        raise ValueError("Invalid basemap settings")
    alpha = basemap["opacity"]
    if (
        isinstance(alpha, bool)
        or not isinstance(alpha, (int, float))
        or not math.isfinite(alpha)
        or not 0 <= alpha <= 1
    ):
        raise ValueError("OSM opacity must be between 0 and 1")
    data["_warnings"] = notes
    if notes:
        warnings.warn("; ".join(notes), UserWarning)
    return data
