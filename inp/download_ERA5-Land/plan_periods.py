#!/usr/bin/env python3
"""Validate dataset destinations and emit inclusive ERA5-Land job periods."""

import argparse
import calendar
from datetime import date, timedelta
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inp-root', type=Path, required=True)
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--start', type=date.fromisoformat, required=True)
    parser.add_argument('--end', type=date.fromisoformat, required=True)
    parser.add_argument('--unit', choices=['daily', 'monthly', 'yearly'], required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', args.dataset):
        parser.error('dataset must be a single directory name containing letters, digits, _ or -')
    root = args.inp_root.resolve()
    target = root / args.dataset
    if target.resolve().parent != root or target.resolve() == (root / 'download_ERA5-Land').resolve():
        parser.error('dataset destination must be directly under inp/, outside the tools')
    for path in (target / 'original', target / 'logs'):
        if path.resolve().parent != target.resolve():
            parser.error(f'output subdirectory escapes the dataset: {path}')
    if args.end < args.start:
        parser.error('end date precedes start date')
    current = args.start
    while current <= args.end:
        if args.unit == 'daily':
            last, tag = current, current.strftime('%Y%m%d')
        elif args.unit == 'monthly':
            last = current.replace(day=calendar.monthrange(current.year, current.month)[1])
            tag = current.strftime('%Y%m')
        else:
            last, tag = date(current.year, 12, 31), current.strftime('%Y')
        last = min(last, args.end)
        print(current.isoformat(), last.isoformat(), tag)
        current = last + timedelta(days=1)


if __name__ == '__main__':
    main()
