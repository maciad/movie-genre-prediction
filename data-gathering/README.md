# Filmweb scraper

This small script uses Playwright to collect links to film pages from Filmweb search results and save them to a CSV.

Quick start (Windows PowerShell):

1. Create and activate a virtualenv (optional but recommended):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Install Playwright browser binaries:

```powershell
python -m playwright install
```

4. Run the scraper (example collecting 50 links):

```powershell
python scrape.py --count 50 --output film_links.csv
```

Notes:
- The scraper uses the CSS selector you provided. Filmweb may change their HTML structure which will break the selector. If that happens, update the `--selector` argument.
- Be polite: avoid very large scrapes and add delays if needed.
