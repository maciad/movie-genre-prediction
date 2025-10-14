#!/usr/bin/env python3
"""
scrape_details.py

Iterates CSV files in `links/` (page1.csv, page2.csv, ...). For each link in a page file:
- open the movie page and extract title from selector: ".filmCoverSection__title "
- extract genres from selector: ".filmPosterSection__buttons > div[data-tag-type=\"rankingGenre\"] > a"
- open movie details page by appending "/descs" to the URL and extract description from selector:
  "div.descriptionSection__item[data-is-default='true'] p.descriptionSection__text.descriptionSection__text--full"

Writes per-page results into directory `test data/` as CSV files named `data_pageN.csv` with columns: url,title,genres,description

Usage:
    python scrape_details.py --start 1 --end 1000 --headed

Note: requires Playwright browsers installed (`python -m playwright install`).
"""
from __future__ import annotations

import argparse
import csv
import os
import time
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_DIR = os.path.dirname(__file__)
LINKS_DIR = os.path.join(BASE_DIR, "links")
OUT_DIR = os.path.join(BASE_DIR, "text-data")

TITLE_SELECTOR = ".filmCoverSection__title "
GENRE_SELECTOR = '.filmPosterSection__buttons > div[data-tag-type="rankingGenre"]'
DESC_SELECTOR = "div.descriptionSection__item[data-is-default='true'] p.descriptionSection__text.descriptionSection__text--full"


def ensure_out_dir() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)


def read_links_for_page(page_num: int) -> List[str]:
    path = os.path.join(LINKS_DIR, f"page{page_num}.csv")
    if not os.path.isfile(path):
        return []
    links: List[str] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
        for r in rows[1:]:
            if r:
                links.append(r[0].strip())
    return links


def write_page_results(page_num: int, rows: List[List[str]]) -> None:
    out_path = os.path.join(OUT_DIR, f"data_page{page_num}.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "title", "genres", "description"])
        for r in rows:
            writer.writerow(r)


def extract_text_or_empty(el):
    try:
        return el.inner_text().strip()
    except Exception:
        return ""


def scrape_range(start: int, end: int, headless: bool = True) -> None:
    ensure_out_dir()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(15000)

        for page_num in range(start, end + 1):
            links = read_links_for_page(page_num)
            if not links:
                print(f"No links for page{page_num}. Skipping.")
                continue

            results: List[List[str]] = []
            for url in links:
                try:
                    print(f"Visiting {url}")
                    page.goto(url, wait_until="networkidle")
                except PlaywrightTimeoutError:
                    print(f"Timeout loading {url}. Skipping link.")
                    results.append([url, "", "", ""])
                    continue

                # title
                try:
                    el = page.query_selector(TITLE_SELECTOR)
                    title = extract_text_or_empty(el) if el else ""
                except Exception:
                    title = ""

                # genres (may be multiple)
                try:
                    genre_els = page.query_selector_all(GENRE_SELECTOR)
                    genres = [extract_text_or_empty(g) for g in genre_els]
                    genres_str = ";".join([g for g in genres if g])
                except Exception:
                    genres_str = ""

                # go to /descs for description
                desc_url = url.rstrip("/") + "/descs"
                desc_text = ""
                try:
                    page.goto(desc_url, wait_until="networkidle")
                    # small delay to allow text to render
                    time.sleep(0.3)
                    desc_el = page.query_selector(DESC_SELECTOR)
                    desc_text = extract_text_or_empty(desc_el) if desc_el else ""
                    desc_text = desc_text.replace("\n", " ").replace("\r", " ").strip()
                except PlaywrightTimeoutError:
                    print(f"Timeout loading desc page for {url}")
                except Exception:
                    pass

                results.append([url, title, genres_str, desc_text])
                # polite delay
                time.sleep(0.3)

            write_page_results(page_num, results)
            print(f"Wrote {len(results)} records to data_page{page_num}.csv")

        try:
            browser.close()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=1000)
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    scrape_range(args.start, args.end, headless=not args.headed)


if __name__ == "__main__":
    main()
