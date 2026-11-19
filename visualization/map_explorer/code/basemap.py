"""Visible browser XYZ tiles resampled into the unchanged geographic map axes.

Scientific layers remain lon/lat. Each output pixel row uses exact spherical
Mercator Y; stretching a complete tile affinely in latitude would be incorrect.
No server downloads, prefetch, offline archive, or online tiles in PNG exports.
"""

from __future__ import annotations

import base64
from io import BytesIO
from html import escape
import json
import math
import os
from urllib.parse import urlparse

import numpy as np
import panel as pn
import param
from PIL import Image

MERCATOR_LIMIT = 85.0511287798066
DEFAULT_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"


def world_pixel(lon, lat, zoom):
    size = 256 * 2**zoom
    return (lon + 180) / 360 * size, (
        1 - np.arcsinh(np.tan(np.deg2rad(np.clip(lat, -MERCATOR_LIMIT, MERCATOR_LIMIT)))) / np.pi
    ) / 2 * size


def tile_plan(extent, size, url=DEFAULT_URL):
    parsed = urlparse(url)
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost")):
        raise ValueError("Tile provider must use HTTPS (loopback HTTP allowed for local test/self-hosted tiles)")
    if not all("{" + key + "}" in url for key in ("z", "x", "y")):
        raise ValueError("Tile URL needs {z}, {x} and {y}")
    w, e, s, n = map(float, extent)
    width, height = [max(1, min(1400, int(v))) for v in size]
    if not np.isfinite([w, e, s, n]).all() or not w < e or not s < n:
        raise ValueError("Invalid geographic basemap extent")
    z = max(0, min(18, int(math.floor(math.log2(width * 360 / (256 * (e - w)))))))
    while True:
        x0, y0 = world_pixel(w, n, z)
        x1, y1 = world_pixel(e, s, z)
        c0, c1 = math.floor(x0 / 256), math.ceil(x1 / 256) - 1
        r0, r1 = max(0, math.floor(y0 / 256)), min(2**z - 1, math.ceil(y1 / 256) - 1)
        if (c1 - c0 + 1) * (r1 - r0 + 1) <= 32 or z == 0:
            break
        z -= 1
    lat = n - (np.arange(height) + 0.5) * (n - s) / height
    _, yy = world_pixel(w, lat, z)
    rows = [float(v - r0 * 256) if abs(a) <= MERCATOR_LIMIT else None for a, v in zip(lat, yy)]
    tiles = [
        dict(
            url=url.replace("{z}", str(z)).replace("{x}", str(c % 2**z)).replace("{y}", str(r)),
            x=(c - c0) * 256,
            y=(r - r0) * 256,
        )
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
    ]
    key = json.dumps([list(extent), width, height, url], separators=(",", ":"))
    return dict(
        key=key,
        extent=list(extent),
        width=width,
        height=height,
        zoom=z,
        tiles=tiles,
        mosaic_width=(c1 - c0 + 1) * 256,
        mosaic_height=max(1, (r1 - r0 + 1) * 256),
        source_x=float(x0 - c0 * 256),
        source_width=float(x1 - x0),
        rows=rows,
    )


class TileBrowser(pn.reactive.ReactiveHTML):
    request = param.Dict(default={})
    enabled = param.Boolean(default=False)
    png = param.String(default="")
    status = param.String(default="OpenStreetMap off")
    _template = '<div id="driver" style="height:0;overflow:hidden"></div>'
    _scripts = {
        "render": """
            state.serial=0;
            state.draw=()=>{
                clearTimeout(state.timer);state.abort?.abort();const serial=++state.serial;
                if(!data.enabled){data.status='OpenStreetMap off';data.png='';return;}
                state.timer=setTimeout(async()=>{
                    const p=data.request;if(!p.tiles)return;
                    state.abort=new AbortController();data.status='Loading visible online tiles…';
                    const mosaic=document.createElement('canvas');mosaic.width=p.mosaic_width;mosaic.height=p.mosaic_height;
                    const ctx=mosaic.getContext('2d');let failures=0;
                    await Promise.all(p.tiles.map(async tile=>{
                        try{
                            const response=await fetch(tile.url,{cache:'default',referrerPolicy:'strict-origin-when-cross-origin',signal:state.abort.signal});
                            if(!response.ok)throw new Error('unavailable');
                            const bitmap=await createImageBitmap(await response.blob());
                            ctx.drawImage(bitmap,tile.x,tile.y,256,256);bitmap.close();
                        }catch(error){if(error.name!=='AbortError')failures++;}
                    }));
                    if(serial!==state.serial||!data.enabled)return;
                    const out=document.createElement('canvas');out.width=p.width;out.height=p.height;
                    const target=out.getContext('2d');target.imageSmoothingEnabled=true;
                    // Python supplies exact Mercator coordinates at geographic
                    // row centers. Each row is resampled separately, never affine
                    // latitude stretching of an entire Mercator tile.
                    for(let row=0;row<p.height;row++)if(p.rows[row]!==null)
                        target.drawImage(mosaic,p.source_x,p.rows[row]-.5,p.source_width,1,0,row,p.width,1);
                    data.png=JSON.stringify({key:p.key,extent:p.extent,image:out.toDataURL('image/png').split(',')[1]});
                    data.status=failures?'Some online tiles unavailable; scientific layers remain usable.':
                        'OpenStreetMap online · geographic reprojection · excluded from PNG';
                },250);
            };state.draw();
        """,
        "request": "state.draw?.();",
        "enabled": "state.draw?.();",
        "remove": "clearTimeout(state.timer);state.abort?.abort();state.serial++;",
    }


class GeographicBasemap:
    def __init__(self):
        self.url = os.environ.get("CMF_EXPLORER_TILE_URL", DEFAULT_URL)
        self.credit = os.environ.get("CMF_EXPLORER_TILE_ATTRIBUTION", "© OpenStreetMap contributors")
        self.driver = TileBrowser(height=0, margin=0)
        self.attribution = pn.pane.HTML(
            "<small>"
            + escape(self.credit)
            + ' · <a href="https://www.openstreetmap.org/copyright" target="_blank">licence</a> · online basemap excluded from PNG</small>',
            visible=False,
            sizing_mode="stretch_width",
        )
        self.notice = pn.pane.Markdown("", sizing_mode="stretch_width", margin=(0, 0))
        self.driver.param.watch(lambda event: setattr(self.notice, "object", event.new), "status")

    def update(self, extent, size, enabled, opacity):
        active = bool(enabled and opacity > 0)
        self.attribution.visible = active
        if active:
            plan = tile_plan(extent, size, self.url)
            if plan != self.driver.request:
                self.driver.request = plan
        if self.driver.enabled != active:
            self.driver.enabled = active

    def decode(self):
        if not self.driver.png or not self.driver.enabled:
            return None
        payload = json.loads(self.driver.png)
        if payload["key"] != self.driver.request.get("key"):
            return None
        with Image.open(BytesIO(base64.b64decode(payload["image"]))) as image:
            rgba = np.asarray(image.convert("RGBA"), dtype="u1")
        return np.ascontiguousarray(rgba[::-1]).view("<u4").reshape(rgba.shape[:2]), payload["extent"]
