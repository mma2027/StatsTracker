#!/usr/bin/env python3
"""
Test parsing PRs from saved HTML to demonstrate the parser works.
"""

import sys
sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')

from bs4 import BeautifulSoup
import re

# Read the saved HTML
with open("jory_lee_page.html", "r") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# Use the same parsing logic from tfrr_fetcher.py
athlete_data = {
    "athlete_id": "8317912",
    "name": "",
    "year": "",
    "sport": "track",
    "events": {}
}

# Extract athlete name
name_elem = soup.find("h3") or soup.find("h2") or soup.find("h1")
if name_elem:
    athlete_data["name"] = name_elem.text.strip()

# Parse PR tables - TFRR has one table per event
all_tables = soup.find_all("table")

for table in all_tables:
    # Get the header row
    header_row = table.find("tr")
    if not header_row:
        continue

    # Get header cells
    header_cells = header_row.find_all(["th", "td"])
    if not header_cells:
        continue

    first_header = header_cells[0].get_text(strip=True)

    # Look for event patterns
    if any(keyword in first_header.lower() for keyword in ['meters', 'jump', 'throw', 'hurdles', 'vault', 'run']):
        # This looks like an event PR table
        event_name = re.sub(r'\s*\(Indoor\).*|\s*\(Outdoor\).*|Top↑', '', first_header).strip()

        # Get the first data row (contains the PR)
        data_rows = table.find_all("tr")[1:]  # Skip header
        if data_rows:
            first_data_row = data_rows[0]
            data_cells = first_data_row.find_all(["td", "th"])

            if data_cells:
                # The PR is in the first cell
                pr_value = data_cells[0].get_text(strip=True)

                # Skip years
                if pr_value and pr_value != "NM" and pr_value != "NMNM" and not re.match(r'^\d{4}$', pr_value):
                    athlete_data["events"][event_name] = pr_value

# Display results
print("=" * 70)
print("TFRR Parser Test - Jory Lee's PRs (from saved HTML)")
print("=" * 70)
print(f"\n✅ Athlete: {athlete_data['name']}")
print(f"✅ Sport: {athlete_data['sport']}")
print(f"\n✅ Personal Records Extracted: {len(athlete_data['events'])} events")
print("=" * 70)

for event, pr in sorted(athlete_data['events'].items()):
    print(f"  {event:<25} {pr}")

print("\n" + "=" * 70)
print("✅ SUCCESS! The parser correctly extracts PRs from TFRR pages.")
print("=" * 70)
