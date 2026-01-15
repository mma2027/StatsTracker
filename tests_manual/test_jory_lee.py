#!/usr/bin/env python3
"""
Fetch Jory Lee's PRs from TFRR.
"""

import sys
sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')  # noqa: E402
import time  # noqa: E402

from src.website_fetcher.tfrr_fetcher import TFRRFetcher  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402, F401

# First, let's get the roster and find Jory Lee's athlete ID
fetcher = TFRRFetcher()
fetcher._init_selenium_driver()

# Go to men's track roster page
team_url = "https://www.tfrrs.org/teams/PA_college_m_Haverford.html"
print(f"Loading roster page: {team_url}")
fetcher.driver.set_page_load_timeout(30)
fetcher.driver.get(team_url)
time.sleep(3)

soup = BeautifulSoup(fetcher.driver.page_source, "html.parser")

# Find Jory Lee's link
athlete_link = None
for link in soup.find_all("a", href=lambda x: x and "/athletes/" in x):
    if "Lee, Jory" in link.text:
        athlete_link = link
        athlete_href = link.get("href")
        print(f"Found Jory Lee: {athlete_href}")
        break

if athlete_link:
    # Navigate to Jory Lee's page
    athlete_url = f"https://www.tfrrs.org{athlete_href}"
    print(f"\nFetching PRs from: {athlete_url}")
    fetcher.driver.get(athlete_url)
    time.sleep(2)

    athlete_soup = BeautifulSoup(fetcher.driver.page_source, "html.parser")

    # Look for PR table
    print("\nJory Lee's Personal Records:")
    print("=" * 50)

    # Find PR table
    tables = athlete_soup.find_all("table")
    for table in tables:
        # Check if this looks like a PR table
        header_row = table.find("tr")
        if header_row and "event" in header_row.get_text().lower():
            rows = table.find_all("tr")[1:]  # Skip header
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    event = cells[0].get_text(strip=True)
                    result = cells[1].get_text(strip=True)
                    if event and result:
                        print(f"  {event}: {result}")
            break

    # If no table found, just show what we can find
    if not any("event" in h.get_text().lower() for table in tables for h in [table.find("tr")] if h):
        print("Looking for PR data in page...")
        # Try to find any performance data
        for h3 in athlete_soup.find_all("h3"):
            if "personal" in h3.get_text().lower() or "best" in h3.get_text().lower():
                print(f"\nFound section: {h3.get_text()}")
                # Get the next table after this header
                next_table = h3.find_next("table")
                if next_table:
                    for row in next_table.find_all("tr"):
                        cells = row.find_all(["td", "th"])
                        if len(cells) >= 2:
                            print(f"  {cells[0].get_text(strip=True)}: {cells[1].get_text(strip=True)}")

else:
    print("Jory Lee not found on roster")

fetcher._close_driver()
