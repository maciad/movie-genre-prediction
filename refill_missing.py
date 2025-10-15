#!/usr/bin/env python3
"""
refill_missing.py

Finds data_pageN.csv files in `text-data/` that contain missing fields (title, genres or description empty or marked)
and re-runs `scrape_details.py` for those page numbers to attempt re-scraping.

Usage:
    python refill_missing.py [--script scrape_details.py] [--headed] [--link-retries 5]

Notes:
- This script calls `scrape_details.py --start N --end N` for each page with missing data.
- It runs them sequentially and prints a short summary. You can re-run with --headed to see the browser.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
from typing import Set

BASE_DIR = os.path.dirname(__file__)
OUT_DIR = os.path.join(BASE_DIR, "text-data")
DEFAULT_SCRIPT = os.path.join(BASE_DIR, "scrape_details.py")
MISSING_TITLE = "__MISSING_TITLE__"
MISSING_DESC = "__MISSING_DESCRIPTION__"

PAGE_RE = re.compile(r"data_page(\d+)\.csv$")


def find_pages_with_missing(out_dir: str) -> Set[int]:
    pages = set()
    if not os.path.isdir(out_dir):
        print(f"Output directory not found: {out_dir}")
        return pages

    for name in os.listdir(out_dir):
        m = PAGE_RE.search(name)
        if not m:
            continue
        page_num = int(m.group(1))
        path = os.path.join(out_dir, name)
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
        except Exception as e:
            print(f"Failed reading {path}: {e}")
            pages.add(page_num)
            continue

        if len(rows) < 2:
            pages.add(page_num)
            continue

        header = rows[0]
        # try to find indices for url,title,genres,description
        idx_map = {h.strip().lower(): i for i, h in enumerate(header)}
        ti = idx_map.get("title")
        gi = idx_map.get("genres")
        di = idx_map.get("description")
        if ti is None or gi is None or di is None:
            pages.add(page_num)
            continue

        for r in rows[1:]:
            # guard against short rows
            title = r[ti].strip() if ti < len(r) else ""
            genres = r[gi].strip() if gi < len(r) else ""
            desc = r[di].strip() if di < len(r) else ""
            if (not title) or (not genres) or (not desc) or title == MISSING_TITLE or desc == MISSING_DESC:
                pages.add(page_num)
                break

    return pages


def run_scrape_for_pages(pages: Set[int], script: str, headed: bool, link_retries: int, link_retry_wait: float) -> None:
    if not pages:
        print("No pages with missing data found.")
        return

    pages_sorted = sorted(pages)
    print(f"Will re-run scrape_details for {len(pages_sorted)} pages: {pages_sorted[:10]}{('...' if len(pages_sorted)>10 else '')}")

    for pnum in pages_sorted:
        cmd = [sys.executable, script, "--start", str(pnum), "--end", str(pnum), "--link-retries", str(link_retries), "--link-retry-wait", str(link_retry_wait)]
        if headed:
            cmd.append("--headed")
        print(f"Running: {' '.join(cmd)}")
        try:
            res = subprocess.run(cmd, check=False)
            print(f"Exit code: {res.returncode}")
        except Exception as e:
            print(f"Failed to run scraper for page {pnum}: {e}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", type=str, default=DEFAULT_SCRIPT, help="Path to scrape_details.py")
    parser.add_argument("--out-dir", type=str, default=OUT_DIR, help="Directory with data_pageN.csv files")
    parser.add_argument("--headed", action="store_true", help="Run browser headed")
    parser.add_argument("--link-retries", type=int, default=5)
    parser.add_argument("--link-retry-wait", type=float, default=0.5)
    args = parser.parse_args()

    pages = find_pages_with_missing(args.out_dir)
    print(f"Found {len(pages)} pages with missing data.")
    print(f"Pages: {sorted(pages)}")
    # run_scrape_for_pages(pages, args.script, args.headed, args.link_retries, args.link_retry_wait)


if __name__ == '__main__':
    main()
