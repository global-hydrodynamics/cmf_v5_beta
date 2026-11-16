"""Validated, human-readable display settings; no execution on config load."""
import json
import warnings
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
    if not isinstance(data, dict) or not required.issubset(data) or data['version'] not in (1,2):
        raise ValueError('Unsupported settings schema/version')
    notes=[]
    unknown=set(data)-required-{'layers'}
    if unknown:
        notes.append('Ignored unknown settings: '+', '.join(sorted(unknown)))
        for key in unknown:
            data.pop(key)
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
    base_options={'width', 'color', 'flexible_color', 'distinguish', 'scale_width', 'color_area'}
    if not isinstance(options, dict) or not base_options.issubset(options):
        raise ValueError('Unsupported network options')
    for key in set(options)-base_options-{'classification'}:
        notes.append('Ignored network option: '+key)
        options.pop(key)
    options.setdefault('classification','fixed')
    if options['classification'] not in ('fixed','quartiles','six_log','continuous'):
        raise ValueError('Unsupported area classification')
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
    if data['version']==2:
        from scene import OVERLAY_DEFAULTS
        from hires import discover_tiles
        from map_products import Products
        layers=data.get('layers',{})
        if not isinstance(layers,dict):
            raise ValueError('layers must be an object')
        allowed={'background','tile','terrain_palette','arrows','overlays','representation'}
        for key in set(layers)-allowed:
            notes.append('Ignored layer setting: '+key);layers.pop(key)
        if layers.get('background','coarse') not in ('none','coarse','catchment','elevtn','difference','flddif'):
            raise ValueError('Unsupported background representation')
        if layers.get('terrain_palette','gray') not in ('gray','pale_terrain'):
            raise ValueError('Unsupported terrain palette')
        if layers.get('representation','grid_center') not in ('off','grid_center','outlet_vector'):
            raise ValueError('Unsupported network representation')
        if not isinstance(layers.get('arrows',False),bool):
            raise ValueError('arrows must be boolean')
        tiles=discover_tiles(reader.path,[])
        if layers.get('tile') not in tiles and layers.get('tile') is not None:
            notes.append('High-resolution source missing; using coarse background')
            layers['tile']=next(iter(tiles),None);layers['background']='coarse'
        if layers.get('representation')=='outlet_vector' and Products(reader).outlet_source is None:
            notes.append('Outlets missing; using grid centers');layers['representation']='grid_center'
        overlays=layers.get('overlays',{})
        if not isinstance(overlays,dict):
            raise ValueError('overlays must be an object')
        for key in set(overlays)-set(OVERLAY_DEFAULTS):
            notes.append('Ignored overlay: '+key);overlays.pop(key)
        for key,value in overlays.items():
            expected=OVERLAY_DEFAULTS[key]
            if isinstance(expected,bool) and not isinstance(value,bool):
                raise ValueError(f'{key} must be boolean')
            if isinstance(expected,str) and (not isinstance(value,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',value)):
                raise ValueError(f'{key} must be #RRGGBB')
            if isinstance(expected,float) and (not isinstance(value,(int,float)) or not .2<=value<=5):
                raise ValueError(f'{key} must be between 0.2 and 5')
        data['layers']=layers
    data['_warnings']=notes
    if notes:
        warnings.warn('; '.join(notes),UserWarning)
    return data
