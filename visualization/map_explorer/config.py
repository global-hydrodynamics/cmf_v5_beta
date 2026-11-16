"""Validated, human-readable display settings; no execution on config load."""
import json
from pathlib import Path


def save_settings(path, settings):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, allow_nan=False) + '\n')
    return path


def load_settings(content, reader):
    if len(content) > 65536:
        raise ValueError('Settings JSON must be smaller than 64 KiB')
    data = json.loads(content)
    required = {'version', 'map_path', 'variable', 'extent', 'scale', 'palette', 'limits', 'network', 'network_options'}
    if not isinstance(data, dict) or set(data) != required or data['version'] != 1:
        raise ValueError('Unsupported settings schema/version')
    if Path(data['map_path']).expanduser().resolve() != reader.path:
        raise ValueError('Settings refer to another map; launch that map separately')
    if data['variable'] not in reader.sources:
        raise ValueError('Settings variable is not available in this map')
    reader.geometry.validate_extent(data['extent'])
    if data['scale'] not in ('auto', 'linear', 'log') or data['palette'] not in ('viridis', 'terrain', 'magma', 'Blues'):
        raise ValueError('Unsupported scale/palette')
    if data['network'] != 'off' and data['network'] not in reader.network_sources:
        raise ValueError('Settings network is not available')
    options = data['network_options']
    if not isinstance(options, dict) or set(options) != {'width', 'color', 'flexible_color', 'distinguish', 'scale_width', 'color_area'}:
        raise ValueError('Unsupported network options')
    if not isinstance(options['width'], (int, float)) or not .2 <= options['width'] <= 4:
        raise ValueError('Line width must be between 0.2 and 4')
    import re
    for name in ('color', 'flexible_color'):
        if not isinstance(options[name], str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', options[name]):
            raise ValueError('Colors must have #RRGGBB format')
    for name in ('distinguish', 'scale_width', 'color_area'):
        if not isinstance(options[name], bool):
            raise ValueError('Network toggles must be boolean')
    limits = data['limits']
    if limits is not None and (not isinstance(limits, list) or len(limits) != 2):
        raise ValueError('Color limits must contain two numbers')
    return data
