"""
Test the calendar AJAX endpoint that the browser uses
"""

import requests
import re
import json

# Test the endpoint with March 2026
url = "https://haverfordathletics.com/services/responsive-calendar.ashx"
params = {"type": "month", "sport": "0", "location": "all", "date": "3/5/2026"}  # 0 = all sports  # March 5, 2026

print("=" * 70)
print(f"Testing: {url}")
print(f"Params: {params}")
print("=" * 70)

response = requests.get(url, params=params, timeout=10)

print(f"Status: {response.status_code}")
print(f"Content-Type: {response.headers.get('content-type')}")
print(f"Response length: {len(response.text)}")

print("\n" + "=" * 70)
print("Analyzing response format")
print("=" * 70)

# Check if it's JSON
try:
    data = response.json()
    print("✓ Response is JSON")
    print(f"Type: {type(data)}")
    if isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
    elif isinstance(data, list):
        print(f"Array with {len(data)} items")
        if data:
            print(f"First item type: {type(data[0])}")
            if isinstance(data[0], dict):
                print(f"First item keys: {list(data[0].keys())[:10]}")
except Exception:  # noqa: E722
    print("✗ Response is not JSON, likely HTML")

# If HTML, check for embedded data
if "text/html" in response.headers.get("content-type", ""):
    print("\nResponse is HTML - checking for embedded data")

    # Look for the same regex pattern we use for sport pages
    pattern = re.compile(r"var obj = (\{.*?\});\s*if\s*\(", re.DOTALL)
    matches = pattern.findall(response.text)
    print(f"Found {len(matches)} var obj matches")

    # Parse matches
    events_found = 0
    total_games = 0
    dates_found = set()

    for i, match in enumerate(matches):
        try:
            obj = json.loads(match)
            if obj.get("type") == "events" and "data" in obj:
                events_found += 1
                games = obj["data"]
                total_games += len(games)

                for game in games:
                    date_str = game.get("date", "").split("T")[0]
                    if date_str:
                        dates_found.add(date_str)

                print(f"\n  Events object {events_found}: {len(games)} games")
        except Exception:  # noqa: E722
            pass

    print(f"\nTotal events objects: {events_found}")
    print(f"Total games: {total_games}")
    if dates_found:
        print(f"Date range: {min(dates_found)} to {max(dates_found)}")

        # Check for specific dates
        if "2026-03-05" in dates_found:
            print("  ✓ Contains March 5, 2026")
        if "2026-01-14" in dates_found:
            print("  ✓ Contains January 14, 2026")

# Test with January date
print("\n" + "=" * 70)
print("Testing with January 14, 2026")
print("=" * 70)

jan_params = {"type": "month", "sport": "0", "location": "all", "date": "1/14/2026"}

jan_response = requests.get(url, params=jan_params, timeout=10)
print(f"Status: {jan_response.status_code}")
print(f"Response length: {len(jan_response.text)}")

# Quick check for game data
if '"date":"2026-01-14' in jan_response.text:
    print("✓ Contains January 14 game data!")
elif '"date":"2026-01' in jan_response.text:
    print("✓ Contains January 2026 data")
else:
    print("✗ No January 2026 data found")
