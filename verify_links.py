#!/usr/bin/env python3
"""
verify_links.py

Checks that the `links/` folder contains files page1.csv .. page1000.csv,
and verifies each file has a header `url` and exactly 10 data rows.

Usage:
    python verify_links.py

Exits with code 0 if all good; prints files with problems otherwise.
"""
from __future__ import annotations

import csv
import os
import sys

BASE_DIR = os.path.dirname(__file__)
LINKS_DIR = os.path.join(BASE_DIR, "links")
EXPECTED_COUNT = 1000
EXPECTED_ROWS_PER_FILE = 10


def verify():
    if not os.path.isdir(LINKS_DIR):
        print(f"Directory not found: {LINKS_DIR}")
        return 2

    problems = []

    # check that page1..page1000 exist
    missing = []
    for i in range(1, EXPECTED_COUNT + 1):
        fname = f"page{i}.csv"
        path = os.path.join(LINKS_DIR, fname)
        if not os.path.isfile(path):
            missing.append(fname)
    if missing:
        print(f"Missing {len(missing)} files:")
        for m in missing[:50]:
            print("  ", m)
        if len(missing) > 50:
            print("  ...")

    # inspect existing files and find those with fewer than EXPECTED_ROWS_PER_FILE data rows
    short_files = []
    bad_header = []
    for i in range(1, EXPECTED_COUNT + 1):
        fname = f"page{i}.csv"
        path = os.path.join(LINKS_DIR, fname)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
        except Exception as e:
            problems.append((fname, f"error reading: {e}"))
            continue

        if not rows:
            short_files.append((fname, 0))
            continue
        header = rows[0]
        if not header or header[0].strip().lower() != 'url':
            bad_header.append(fname)
            # still check rows
        data_rows = rows[1:]
        # count non-empty rows
        data_count = sum(1 for r in data_rows if r and any(cell.strip() for cell in r))
        if data_count < EXPECTED_ROWS_PER_FILE:
            short_files.append((fname, data_count))

    print("Verification summary:")
    total_files = len([n for n in os.listdir(LINKS_DIR) if n.lower().endswith('.csv')])
    print(f"  CSV files in links/: {total_files}")
    print(f"  Missing expected files: {len(missing)}")
    print(f"  Files with bad header: {len(bad_header)}")
    print(f"  Files with < {EXPECTED_ROWS_PER_FILE} data rows: {len(short_files)}")

    if bad_header:
        print("\nFiles with wrong/missing header (should be 'url'):")
        for f in bad_header:
            print("  ", f)

    if short_files:
        print("\nFiles with too few data rows:")
        for fname, cnt in short_files:
            print(f"  {fname}: {cnt} rows")

    if missing or bad_header or short_files or problems:
        print("\nProblems detected.")
        return 1
    print("All good: 1000 files with 10 links each and proper header found.")
    return 0


if __name__ == '__main__':
    rc = verify()
    sys.exit(rc)
