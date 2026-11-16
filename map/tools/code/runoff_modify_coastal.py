#!/usr/bin/env python3
"""Grid-only legacy-style daily neighbor minimum; no coastline, land mask or Input Matrix."""
from __future__ import annotations

import sys
import numpy as np
from runoff_calc_climatology import (parser, product_paths, read_product, require_new, climatology,
                                     same_grid, annual_mean, save_netcdf, metadata)


def neighbor_plan(mean_mm_s, grid, boundary='auto'):
    """Targets: mean <=0 or missing; donors: finite mean >0 in the original eight neighbors.

    Preserve latitude edges, and wrap longitude only for a full 360-degree regular
    grid. The map-independent mask is an approved change from mod_runoff.F90's
    Input-Matrix-limited selection; no actual coastal classification is claimed.
    """
    dx = abs(float(grid.longitude[-1])-float(grid.longitude[0]))/(grid.shape[1]-1)
    global_grid = np.isclose(dx*grid.shape[1], 360., rtol=0, atol=1e-4)
    if boundary == 'periodic' and not global_grid:
        raise ValueError('Periodic longitude requires a complete 360-degree grid')
    periodic = global_grid and boundary != 'regional'
    eligible = np.isfinite(mean_mm_s) & (mean_mm_s > 0)
    rows, cols = np.where(~eligible)
    donors = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == dy == 0:
                continue
            y, x = rows+dy, cols+dx
            valid = (y >= 0) & (y < grid.shape[0])
            if not periodic:
                valid &= (x >= 0) & (x < grid.shape[1])
            x = x % grid.shape[1]
            y = np.clip(y, 0, grid.shape[0]-1)
            valid &= eligible[y, x]
            donors.append((y, x, valid))
    return rows, cols, donors, periodic


def modify_day(daily_mm, plan):
    """Daily interval depth [mm] -> adjusted depth [mm], original row order and float32.

    The long-term mean fixes donors/targets. Use the minimum of their *daily*
    values, including valid zero: min(mean) is not mean(min). This retains the
    legacy conservative choice, whose physical optimality is unverified.
    Missing/negative daily donors are excluded explicitly; absent candidates leave
    the original value untouched. All replacements are simultaneous, no propagation.
    """
    rows, cols, donors, _ = plan
    minimum = np.full(len(rows), np.inf, dtype='f4')
    for y, x, valid in donors:
        values = daily_mm[y, x]
        candidates = valid & np.isfinite(values) & (values >= 0)
        minimum = np.minimum(minimum, np.where(candidates, values, np.float32(np.inf)))
    filled = np.isfinite(minimum)
    result = daily_mm.copy()
    result[rows[filled], cols[filled]] = minimum[filled]
    return result, (rows[filled], cols[filled])


def modify(args):
    paths = product_paths(args)
    require_new([paths['daily_after'], paths['mean_after']], args.overwrite)
    grid, before, original = read_product(paths['mean_before'])
    if (original['start_year'], original['end_year'], original['dataset']) != (args.start_year, args.end_year, args.dataset):
        raise ValueError('Uncorrected mean belongs to another period/dataset')
    expected = metadata(args)
    for key in ('source_pattern', 'source_variable', 'input_units_override', 'interval_hours_override'):
        if original.get(key) != expected[key]:
            raise ValueError(f'Uncorrected mean/source settings differ for {key}; rerun calculate')
    # No land mask is required: fill nonpositive/missing means so coastal small
    # rivers can receive a runoff estimate even for products without such a mask.
    # This intentionally can affect inland zeros and cells never used by a river map.
    plan = neighbor_plan(before, grid, args.longitude_boundary)
    filled_any = np.zeros(grid.shape, dtype=bool)

    def adjust(daily_mm):
        adjusted, filled = modify_day(daily_mm, plan)
        filled_any[filled] = True
        return adjusted

    # Correct each source day BEFORE averaging across years. Minimum and averaging
    # do not commute; correcting an already averaged field would change the method.
    actual_grid, daily, counts = climatology(args, modifier=adjust, expected_grid=grid)
    if not same_grid(grid, actual_grid):
        raise ValueError('Raw runoff grid differs from uncorrected mean')
    mean = annual_mean(daily)
    attrs = metadata(args)
    attrs.update(coastal_method='minimum of daily values from original-mean-positive eight neighbors; grid-only targets',
                 longitude_boundary='periodic' if plan[3] else 'regional',
                 target_cells=len(plan[0]), filled_target_cells=int(filled_any.sum()),
                 source_mean=paths['mean_before'].name)
    save_netcdf(paths['daily_after'], grid, daily, 'mm day-1', attrs, counts, args.overwrite)
    save_netcdf(paths['mean_after'], grid, mean, 'mm s-1', attrs, overwrite=args.overwrite)
    print(f'[SUCCESS] Filled {filled_any.sum()} target cells; saved {paths["mean_after"]}', flush=True)


if __name__ == '__main__':
    # Share source/unit/period arguments; this executable always owns stage 2.
    p = parser(include_stage=False)
    p.description = __doc__
    p.add_argument('--method', choices=['minimum'], default='minimum')
    p.add_argument('--longitude-boundary', choices=['auto','periodic','regional'], default='auto')
    try:
        modify(p.parse_args())
    except (ValueError, OSError, KeyError) as error:
        print(f'[ERROR] {error}', file=sys.stderr)
        sys.exit(1)
