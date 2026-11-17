"""Explicit nextxy connectivity, including flexible links and longitude seams."""
from __future__ import annotations

import numpy as np


def intersects(x0, y0, x1, y1, extent):
    """Vectorized Liang–Barsky clipping; both endpoints may be outside view."""
    w, e, s, n = extent
    dx, dy = x1-x0, y1-y0
    lower = np.zeros(len(x0))
    upper = np.ones(len(x0))
    valid = np.ones(len(x0), dtype=bool)
    for p, q in ((-dx, x0-w), (dx, e-x0), (-dy, y0-s), (dy, n-y0)):
        ratio = np.divide(q, p, out=np.zeros_like(q, dtype=float), where=p != 0)
        valid &= ~((p == 0) & (q < 0))
        lower = np.where(p < 0, np.maximum(lower, ratio), lower)
        upper = np.where(p > 0, np.minimum(upper, ratio), upper)
    return valid & (lower <= upper)


class RiverNetwork:
    def __init__(self, reader, product='nextxy'):
        self.geometry = g = reader.geometry
        self.product = product
        x, y = reader.read_network(product)
        self.nextx, self.nexty = x.filled(-9999), y.filled(-9999)
        positive = (self.nextx > 0) & (self.nexty > 0)
        in_bounds = positive & (self.nextx <= g.nx) & (self.nexty <= g.ny)
        rows, cols = np.where(in_bounds)
        dr, dc = self.nexty[in_bounds]-1, self.nextx[in_bounds]-1
        self_link = (rows == dr) & (cols == dc)
        self.counts = {
            'out_of_map': int(np.count_nonzero(positive & ~in_bounds)),
            'mixed_codes': int(np.count_nonzero((self.nextx > 0) != (self.nexty > 0))),
            'self_links': int(self_link.sum()),
            'terminal_pairs': int(np.count_nonzero((self.nextx <= 0) & (self.nexty <= 0) & (self.nextx != -9999))),
        }
        keep = ~self_link
        self.rows, self.cols = rows[keep], cols[keep]
        self.dest_rows, self.dest_cols = dr[keep], dc[keep]
        delta_x = np.abs(self.dest_cols-self.cols)
        if g.periodic:
            delta_x = np.minimum(delta_x, g.nx-delta_x)
        self.flexible = np.maximum(delta_x, np.abs(self.dest_rows-self.rows)) > 1
        x0, y0 = g.lon[self.cols], g.lat[self.rows]
        x1, y1 = g.lon[self.dest_cols], g.lat[self.dest_rows]
        # A global seam connection is a short periodic link, not a line across
        # all longitudes. Split it for drawing while retaining source indices.
        seam = (np.abs(x1-x0) > 180) if g.periodic else np.zeros(len(x0), dtype=bool)
        indices = np.flatnonzero(seam)
        adjusted = x1[seam] + np.where(x1[seam] < x0[seam], 360, -360)
        edge = np.where(adjusted > x0[seam], g.east, g.west)
        fraction = (edge-x0[seam])/(adjusted-x0[seam])
        crossing_y = y0[seam] + fraction*(y1[seam]-y0[seam])
        other = np.where(edge == g.east, g.west, g.east)
        self.x0 = np.concatenate([x0[~seam], x0[seam], other])
        self.y0 = np.concatenate([y0[~seam], y0[seam], crossing_y])
        self.x1 = np.concatenate([x1[~seam], edge, x1[seam]])
        self.y1 = np.concatenate([y1[~seam], crossing_y, y1[seam]])
        self.link_index = np.concatenate([np.flatnonzero(~seam), indices, indices])

    def visible(self, extent):
        return np.flatnonzero(intersects(self.x0, self.y0, self.x1, self.y1, extent))

    def inspect(self, row, col):
        g = self.geometry
        x, y = int(self.nextx[row, col]), int(self.nexty[row, col])
        info = {'downstream ix (1-based)': x, 'downstream iy (1-based)': y}
        if x == -9999 or y == -9999:
            status = 'missing / unassigned'
        elif x <= 0 or y <= 0:
            status = 'terminal / boundary code (raw codes retained)' if x <= 0 and y <= 0 else 'invalid mixed destination codes'
        elif x > g.nx or y > g.ny:
            status = 'positive destination outside this map'
        elif x == col+1 and y == row+1:
            status = 'self link (not drawn)'
        else:
            dx = abs(x-(col+1))
            if g.periodic:
                dx = min(dx, g.nx-dx)
            status = 'flexible' if max(dx, abs(y-(row+1))) > 1 else 'local'
            info.update({'downstream longitude': float(g.lon[x-1]), 'downstream latitude': float(g.lat[y-1])})
        info['downstream status'] = status
        return info


def automatic_detail(network, reader, visible, budget=5000):
    """Hide small-uparea display links only; scientific topology stays intact.

    Rank unique stored links, so two periodic seam pieces share one decision.
    Equal areas at the cutoff are retained together. Missing/invalid source areas
    cannot support an omission decision and remain visible.
    """
    unique = np.unique(network.link_index[visible])
    if len(unique) <= budget:
        return visible, f"Auto detail: all {len(unique):,} visible links (target {budget:,})."
    if "uparea" not in reader.sources:
        return visible, "Auto detail unavailable: no stored uparea; all visible links retained."
    if not hasattr(network, "_areas"):
        network._areas = reader.read("uparea")[network.rows, network.cols].astype(float).filled(np.nan) * 1e-6
    areas = network._areas
    reference = areas[unique]
    valid = np.isfinite(reference) & (reference > 0)
    if np.count_nonzero(valid) <= budget:
        return visible, "Auto detail: insufficient valid uparea to reduce density; all visible links retained."
    # A physical area cutoff, not arbitrary array striding or random subsampling.
    cutoff = float(np.partition(reference[valid], -budget)[-budget])
    values = areas[network.link_index[visible]]
    keep = ~np.isfinite(values) | (values <= 0) | (values >= cutoff)
    retained = visible[keep]
    count = len(np.unique(network.link_index[retained]))
    return retained, (f"Auto detail: {count:,}/{len(unique):,} visible links; "
                      f"uparea ≥ {cutoff:,.6g} km² (ties/unknown areas retained). "
                      "Zoom in for tributaries or select All links. Display only.")
