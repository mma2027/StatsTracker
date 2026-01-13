"""
Look for iCal or RSS feeds that might have full schedules
"""

import requests
from bs4 import BeautifulSoup
import re

# Check main calendar page
url = "https://haverfordathletics.com/calendar"
response = requests.get(url, timeout=10)
soup = BeautifulSoup(response.text, "html.parser")

print("=" * 70)
print("Looking for iCal, RSS, or subscribe links")
print("=" * 70)

# Look for links with common feed indicators
feed_keywords = ["ical", "ics", "rss", "subscribe", "webcal", "feed", "export"]

found_feeds = []

for link in soup.find_all("a"):
    href = link.get("href", "")
    text = link.get_text().lower().strip()

    for keyword in feed_keywords:
        if keyword in href.lower() or keyword in text:
            found_feeds.append((text[:50], href))
            print(f"Found: {text[:50]}")
            print(f"  URL: {href}")
            break

# Also check for meta tags or special feed links
for link_tag in soup.find_all("link"):
    rel = link_tag.get("rel", [])
    href = link_tag.get("href", "")
    if any(keyword in str(rel).lower() + href.lower() for keyword in ["alternate", "feed", "ics"]):
        print(f"Found in <link> tag:")
        print(f"  rel={rel}, href={href}")

# Check individual sport pages for subscribe options
print("\n" + "=" * 70)
print("Checking baseball schedule page for feed links")
print("=" * 70)

sport_url = "https://haverfordathletics.com/sports/baseball/schedule?season=2025-26"
sport_response = requests.get(sport_url, timeout=10)
sport_soup = BeautifulSoup(sport_response.text, "html.parser")

for link in sport_soup.find_all("a"):
    href = link.get("href", "")
    text = link.get_text().lower().strip()

    for keyword in feed_keywords:
        if keyword in href.lower() or keyword in text:
            print(f"Found: {text[:50]}")
            print(f"  URL: {href}")
            break

# Look for calendar export buttons/links in the page
export_pattern = re.compile(r"(export|download|subscribe|ical|\.ics)", re.IGNORECASE)
if export_pattern.search(sport_response.text):
    print("\nPage contains export/subscribe-related text")
    # Find context
    for match in export_pattern.finditer(sport_response.text):
        start = max(0, match.start() - 100)
        end = min(len(sport_response.text), match.end() + 100)
        context = sport_response.text[start:end]
        if "href" in context or "url" in context.lower():
            print(f"Context: ...{context}...")
            break

print("\n" + "=" * 70)
print("Checking for schedule.ashx or calendar.ashx endpoints")
print("=" * 70)

# Try common schedule endpoint patterns
test_urls = [
    "https://haverfordathletics.com/calendar.ashx/calendar.ics",
    "https://haverfordathletics.com/schedule.ashx?sport_id=1&season_id=latest",
    "https://haverfordathletics.com/sports/baseball/schedule.ics",
    "https://haverfordathletics.com/sports/baseball.ics",
]

for test_url in test_urls:
    try:
        resp = requests.head(test_url, timeout=5)
        if resp.status_code == 200:
            print(f"✓ {test_url} - {resp.status_code}")
            print(f"  Content-Type: {resp.headers.get('content-type')}")
        elif resp.status_code != 404:
            print(f"? {test_url} - {resp.status_code}")
    except Exception as e:
        pass
