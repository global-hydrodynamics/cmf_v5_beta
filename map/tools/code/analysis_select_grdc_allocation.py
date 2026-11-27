# SPDX-License-Identifier: Apache-2.0
"""Select the valid GRDC allocation with the greatest mapped area."""
import argparse
import csv
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('allocation_csv', type=Path)
    args = parser.parse_args()

    selected = None
    with args.allocation_csv.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        required = {'ID', 'area_CaMa', 'Type', 'ix1', 'iy1'}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f'{args.allocation_csv} lacks required columns: {sorted(required)}')
        for row in reader:
            try:
                candidate = (float(row['area_CaMa']), row['ID'].strip(),
                             int(row['ix1']), int(row['iy1']), row['Type'].strip())
            except (TypeError, ValueError):
                continue
            area, identifier, ix, iy, kind = candidate
            if not identifier or kind == '-9' or area <= 0 or ix <= 0 or iy <= 0:
                continue
            if selected is None or area > selected[0]:
                selected = candidate

    if selected is None:
        raise SystemExit(f'GRDC allocation contains no valid allocated station: {args.allocation_csv}')
    area, identifier, ix, iy, _kind = selected
    print(identifier, ix, iy, f'{area:g}')


if __name__ == '__main__':
    main()
