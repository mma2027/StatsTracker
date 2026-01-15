#!/usr/bin/env python3
"""
Fetch Jory Lee's PRs and save HTML for debugging.
"""

import sys
sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')  # noqa: E402
import time  # noqa: E402

from src.website_fetcher.tfrr_fetcher import TFRRFetcher  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

# First, let's get the roster and find Jory Lee's athlete ID
fetcher = TFRRFetcher()
fetcher._init_selenium_driver()

# Go directly to Jory Lee's page
athlete_url = "https://www.tfrrs.org/athletes/8317912/Haverford/Jory_Lee.html"
print(f"Fetching: {athlete_url}")
fetcher.driver.set_page_load_timeout(30)
fetcher.driver.get(athlete_url)
time.sleep(3)

# Save HTML
with open("jory_lee_page.html", "w") as f:
    f.write(fetcher.driver.page_source)
print("Saved page HTML to jory_lee_page.html")

soup = BeautifulSoup(fetcher.driver.page_source, "html.parser")

# Look for all tables
print("\nAll tables found on page:")
tables = soup.find_all("table")
print(f"Found {len(tables)} tables")

for i, table in enumerate(tables):
    print(f"\n--- Table {i+1} ---")
    # Get first row to see headers
    first_row = table.find("tr")
    if first_row:
        headers = [th.get_text(strip=True) for th in first_row.find_all(["th", "td"])]
        print(f"Headers: {headers[:5]}")  # First 5 headers

    # Get row count
    rows = table.find_all("tr")
    print(f"Rows: {len(rows)}")

    # Show first data row
    if len(rows) > 1:
        first_data = rows[1].find_all(["td", "th"])
        print(f"First row data: {[td.get_text(strip=True) for td in first_data[:3]]}")

# Look for sections with "Best" or "PR" or "Personal"
print("\n\nLooking for PR sections:")
for h in soup.find_all(["h1", "h2", "h3", "h4"]):
    text = h.get_text(strip=True).lower()
    if any(keyword in text for keyword in ["best", "personal", "pr", "record"]):
        print(f"Found: {h.get_text(strip=True)}")

fetcher._close_driver()
