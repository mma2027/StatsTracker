"""
Test the .ics (iCal) endpoint
"""

import requests

url = "https://haverfordathletics.com/sports/baseball/schedule.ics"

print(f"Testing: {url}")
print("=" * 70)

try:
    # Follow redirects
    response = requests.get(url, timeout=10, allow_redirects=True)

    print(f"Final URL: {response.url}")
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Content length: {len(response.text)}")

    if response.status_code == 200:
        print("\n" + "=" * 70)
        print("Response preview:")
        print("=" * 70)
        print(response.text[:2000])

        # Count events in iCal
        event_count = response.text.count("BEGIN:VEVENT")
        print(f"\nFound {event_count} events in iCal feed")

        # Look for dates
        if "20260" in response.text:  # 2026 dates
            print("\nContains 2026 dates!")

            # Extract a few dates for testing
            import re

            date_pattern = re.compile(r"DTSTART[^:]*:(\d{8})")
            dates = date_pattern.findall(response.text)

            if dates:
                print("Sample dates found:")  # noqa: F541
                for date in dates[:10]:
                    # Format: YYYYMMDD -> YYYY-MM-DD
                    formatted = f"{date[0:4]}-{date[4:6]}-{date[6:8]}"
                    print(f"  - {formatted}")

except Exception as _e:  # noqa: F841
    print(f"Error: {_e}")

# Try other sports too
print("\n" + "=" * 70)
print("Testing other sports")
print("=" * 70)

for sport in ["mens-basketball", "mens-lacrosse", "wten"]:
    sport_url = f"https://haverfordathletics.com/sports/{sport}/schedule.ics"
    try:
        resp = requests.head(sport_url, timeout=5, allow_redirects=True)
        if resp.status_code == 200:
            print(f"✓ {sport}: {resp.status_code} - {resp.headers.get('content-type')}")
        else:
            print(f"✗ {sport}: {resp.status_code}")
    except Exception:  # noqa: F841
        print(f"✗ {sport}: Error")
