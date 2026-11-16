"""Measure browser space and fit the actual geographic frame without cropping."""

import math

import panel as pn
import param


def frame_size(extent, bounds):
    """Fit geographic equirectangular aspect within measured outer plot space."""
    west, east, south, north = extent
    ratio = (east - west) * max(0.05, math.cos(math.radians((south + north) / 2))) / (north - south)
    # Leave room for axes, toolbar and physical colorbar, never change ranges.
    width, height = max(1, bounds[0] - 150), max(1, bounds[1] - 85)
    # Quantize height first, then derive width: avoid independent-rounding distortion.
    height = max(1, math.floor(min(height, width / ratio)))
    return max(1, round(height * ratio)), height


class MapViewport(pn.reactive.ReactiveHTML):
    plot = param.ClassSelector(class_=pn.viewable.Viewable)
    bounds = param.List(default=[900, 600])
    _template = '<div id="measure" style="width:100%;min-width:0;display:flex;justify-content:center">${plot}</div>'
    _scripts = {
        "render": """
            state.fit = () => {
                const rect = measure.getBoundingClientRect();
                const width = Math.max(1, Math.floor(rect.width));
                const height = Math.max(140, Math.floor(Math.min(window.innerHeight * .75,
                    window.innerHeight - Math.max(0,rect.top) - 65)));
                if (data.bounds[0] !== width || data.bounds[1] !== height)
                    data.bounds = [width,height];
            };
            state.observer = new ResizeObserver(state.fit);
            state.observer.observe(measure);
            window.addEventListener('resize',state.fit);
            state.fit();
        """,
        "remove": """
            state.observer?.disconnect();
            if (state.fit) window.removeEventListener('resize',state.fit);
        """,
    }
