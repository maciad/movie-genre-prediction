#!/usr/bin/env python3
"""
Scrapes Filmweb search pages and collects movie links into a CSV.

Usage example:
  python scrape.py --count 50 --output links.csv

Notes:
- The script uses Playwright. After installing requirements run:
	python -m playwright install
- The CSS selector used is the one you provided; it's brittle but matches the page structure.
"""
from __future__ import annotations

import argparse
import csv
import random
import time
import os
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


# The selector provided by the user
DEFAULT_SELECTOR = (
	"div > div:nth-child(1) > div:nth-child(2) > div:nth-child(3) >"
	" div:nth-child(1) > div:nth-child(1) > a:nth-child(1)"
)


def scrape_filmweb_links(
	target_count: int = 100,
	start_page: int = 1,
	selector: str = DEFAULT_SELECTOR,
	headless: bool = True,
	output_path: str | None = None,
	retries: int = 3,
	retry_wait: float = 1.0,
) -> List[str]:
	"""Scrape links page-by-page, retrying until at least 10 links are found (or retries exhausted).

	After reading a page the script immediately writes that page's links to a file named
	`page{n}.csv` (saved in the same directory as `output_path` if provided, else current dir).
	Returns the global list of collected (unique) links up to target_count.
	"""

	collected: List[str] = []

	# determine directory where per-page files should be written
	# use a `links/` subfolder next to provided output (or next to script) per user request
	base_dir = os.path.dirname(output_path) if output_path else os.getcwd()
	if not base_dir:
		base_dir = os.getcwd()
	output_dir = os.path.join(base_dir, "links")
	os.makedirs(output_dir, exist_ok=True)

	def save_page_file(page_links: List[str], page_number: int) -> None:
		if not page_links:
			return
		filename = os.path.join(output_dir, f"page{page_number}.csv")
		with open(filename, "w", newline="", encoding="utf-8") as f:
			writer = csv.writer(f)
			writer.writerow(["url"])
			for u in page_links:
				writer.writerow([u])

	with sync_playwright() as p:
		browser = p.chromium.launch(headless=headless)
		context = browser.new_context()
		page = context.new_page()
		page.set_default_timeout(15000)

		page_num = start_page
		while len(collected) < target_count:
			url = f"https://www.filmweb.pl/search#/film?page={page_num}"
			print(f"Visiting {url}")
			attempt = 0
			elements = []
			while attempt <= retries:
				try:
					page.goto(url, wait_until="networkidle")
				except PlaywrightTimeoutError:
					print(f"Timeout loading page {page_num} (attempt {attempt+1}).")
					# try reload and continue to retry
					try:
						page.reload()
					except Exception:
						pass
					attempt += 1
					time.sleep(retry_wait)
					continue

				# scroll to trigger lazy load
				for i in range(1, 6):
					page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {i} / 5)")
					time.sleep(0.2)

				try:
					page.wait_for_selector(selector, timeout=5000)
				except PlaywrightTimeoutError:
					print(f"Selector not found on page {page_num} (attempt {attempt+1}).")
					elements = []
					attempt += 1
					time.sleep(retry_wait)
					continue

				elements = page.query_selector_all(selector)
				if len(elements) >= 10:
					break
				# otherwise retry
				attempt += 1
				print(f"Only {len(elements)} items found on page {page_num} (attempt {attempt}). Retrying...")
				try:
					page.reload()
				except Exception:
					pass
				time.sleep(retry_wait)

			# after retry loop, proceed with whatever was found (may be <10)
			if not elements:
				print(f"No elements found on page {page_num} after {retries} retries. Stopping.")
				break

			# extract urls for this page
			page_links: List[str] = []
			for el in elements[:10]:
				href = el.get_attribute("href")
				if not href:
					continue
				if href.startswith("/"):
					href = "https://www.filmweb.pl" + href
				page_links.append(href)

			# save this page's links immediately
			save_page_file(page_links, page_num)
			print(f"Saved {len(page_links)} links to page{page_num}.csv")

			# add to global collection (unique)
			for u in page_links:
				if u not in collected:
					collected.append(u)
					print(f"Collected: {u}")
					if len(collected) >= target_count:
						break

			print(f"Collected {len(collected)} links so far.")
			page_num += 1
			# polite short sleep
			time.sleep(random.uniform(1.0, 2.0))

		try:
			browser.close()
		except Exception:
			pass

	return collected[:target_count]


def save_to_csv(links: List[str], output_path: str) -> None:
	with open(output_path, "w", newline="", encoding="utf-8") as f:
		writer = csv.writer(f)
		writer.writerow(["url"])
		for l in links:
			writer.writerow([l])


def main() -> None:
	parser = argparse.ArgumentParser(description="Filmweb link scraper using Playwright")
	parser.add_argument("--count", type=int, default=100, help="Number of links to collect")
	parser.add_argument("--start-page", type=int, default=1, help="Start page number (defaults to 1)")
	parser.add_argument("--output", type=str, default="links.csv", help="Output CSV file")
	parser.add_argument("--selector", type=str, default=DEFAULT_SELECTOR, help="CSS selector for links")
	parser.add_argument("--headed", action="store_true", help="Run browser headed (visible)")
	parser.add_argument("--retries", type=int, default=3, help="Number of retries per page if fewer than 10 links are found")
	parser.add_argument("--retry-wait", type=float, default=1.0, help="Seconds to wait between retries")

	args = parser.parse_args()

	headless = not args.headed

	links = scrape_filmweb_links(
		target_count=args.count,
		start_page=args.start_page,
		selector=args.selector,
		headless=headless,
		output_path=args.output,
		retries=args.retries,
		retry_wait=args.retry_wait,
	)

	if not links:
		print("No links collected. Exiting.")
		return

	# Per-page files have already been written into links/ directory. Optionally write a combined file there.
	if args.output:
		base_name = os.path.basename(args.output)
		combined_path = os.path.join(os.path.dirname(args.output) or os.getcwd(), "links", base_name)
		save_to_csv(links, combined_path)
		print(f"Saved combined {len(links)} links to {combined_path}")
	else:
		print(f"Collected {len(links)} links (no combined output requested)")


if __name__ == "__main__":
	main()

