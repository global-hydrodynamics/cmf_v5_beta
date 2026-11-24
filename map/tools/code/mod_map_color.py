# SPDX-License-Identifier: Apache-2.0
# Parallel port of mod_map_color.F90; original Fortran authors and license retained.
"""Legacy size-prioritized four-neighbor display colors, independent of physics.

Large classes (20 or more cells) precede small classes, both in ascending ID.
Choose the first unused color 2..10, saturating at 10; singletons use 1.
Longitude neighbors wrap only for a 360-degree map, as in mod_map_color.F90.
"""
import numpy as np


def color_map(classes, west, east):
    """Return int32 palette indices; nonpositive classes stay -9999."""
    classes = np.asarray(classes)
    highest = int(classes.max())
    result = np.full(classes.shape, -9999, dtype=np.int32)
    if highest < 1:
        return result
    counts = np.bincount(classes[classes > 0], minlength=highest + 1)
    neighbors = [set() for _ in range(highest + 1)]
    pairs = [(classes[:, :-1], classes[:, 1:]), (classes[:-1], classes[1:])]
    if np.float32(east - west) == np.float32(360):
        pairs.append((classes[:, -1:], classes[:, :1]))
    for left, right in pairs:
        valid = (left > 0) & (right > 0) & (left != right)
        # Encode positive int32 IDs in int64; avoids a costly 2-column sort.
        edges = np.unique(left[valid].astype('i8')*(highest+1)+right[valid])
        for edge in edges:
            a, b = divmod(int(edge), highest+1)
            neighbors[a].add(b)
            neighbors[b].add(a)
    palette = np.zeros(highest + 1, dtype=np.int32)
    for large in (True, False):
        for group in range(1, highest + 1):
            if bool(counts[group] >= 20) != large:
                continue
            used = {palette[n] for n in neighbors[group]}
            color = next((c for c in range(2, 10) if c not in used), 10)
            palette[group] = 1 if counts[group] == 1 else color
    valid = classes > 0
    result[valid] = palette[classes[valid]]
    return result
