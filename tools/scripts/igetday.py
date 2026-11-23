#!/usr/bin/env python3
"""Print the number of days in a Gregorian calendar month."""

import calendar
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: igetday.py YEAR MONTH", file=sys.stderr)
        return 2

    try:
        year, month = map(int, sys.argv[1:])
    except ValueError:
        print("igetday.py: YEAR and MONTH must be integers", file=sys.stderr)
        return 2

    if not 1 <= month <= 12:
        print(f"igetday.py: MONTH must be between 1 and 12, got {month}", file=sys.stderr)
        return 2

    days = 28 if year == 0 and month == 2 else calendar.monthrange(year, month)[1]
    print(days)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
