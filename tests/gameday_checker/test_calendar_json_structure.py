"""
Examine the JSON structure from the calendar endpoint
"""

import requests
import json
from datetime import date


def fetch_calendar_month(target_date):
    """Fetch calendar data for a given month"""
    base_url = "https://haverfordathletics.com"
    url = f"{base_url}/services/responsive-calendar.ashx"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://haverfordathletics.com/calendar",
        "X-Requested-With": "XMLHttpRequest",
    }

    # Format date as M/D/YYYY
    date_str = f"{target_date.month}/{target_date.day}/{target_date.year}"

    params = {"type": "month", "sport": "0", "location": "all", "date": date_str}

    response = requests.get(url, params=params, headers=headers, timeout=10)
    if response.status_code == 200:
        return response.json()
    return None


# Test with March 2026
print("=" * 70)
print("March 2026 Calendar Data")
print("=" * 70)

march_data = fetch_calendar_month(date(2026, 3, 5))

if march_data:
    print(f"Response type: {type(march_data)}")
    print(f"Number of days: {len(march_data)}")

    # Show structure of first day
    if march_data:
        first_day = march_data[0]
        print(f"\nFirst day structure:")
        print(f"  Keys: {list(first_day.keys())}")
        print(f"  Date: {first_day.get('date')}")
        print(f"  Number of events: {len(first_day.get('events', []))}")

        # Show structure of first event
        if first_day.get("events"):
            first_event = first_day["events"][0]
            print(f"\nFirst event structure:")
            print(f"  Keys: {list(first_event.keys())}")
            print(f"  Sport: {first_event['sport']['title']}")
            print(f"  Opponent: {first_event['opponent']['title']}")
            print(f"  Date/Time: {first_event['date']} at {first_event['time']}")
            print(f"  Location: {first_event['location']}")
            print(f"  Location indicator: {first_event['location_indicator']} (H=Home, A=Away)")

    # Find March 5 specifically
    print("\n" + "=" * 70)
    print("March 5, 2026 Games")
    print("=" * 70)

    for day in march_data:
        if day["date"].startswith("2026-03-05"):
            print(f"Found {len(day['events'])} games on March 5:")
            for event in day["events"]:
                sport = event["sport"]["title"]
                opponent = event["opponent"]["title"]
                time_str = event.get("time", "TBA")
                loc = event["location_indicator"]
                print(f"  - {sport}: vs {opponent} at {time_str} ({'Home' if loc == 'H' else 'Away'})")
            break
    else:
        print("No games found on March 5")

    # Count total games in the month
    total_games = sum(len(day.get("events") or []) for day in march_data)
    print(f"\nTotal games in March data: {total_games}")

    # Get date range
    dates = [day["date"].split("T")[0] for day in march_data if day.get("events")]
    if dates:
        print(f"Date range with games: {min(dates)} to {max(dates)}")

# Test with January 2026
print("\n" + "=" * 70)
print("January 2026 Calendar Data")
print("=" * 70)

jan_data = fetch_calendar_month(date(2026, 1, 14))

if jan_data:
    # Find January 14 specifically
    for day in jan_data:
        if day["date"].startswith("2026-01-14"):
            print(f"Found {len(day['events'])} games on January 14:")
            for event in day["events"]:
                sport = event["sport"]["title"]
                opponent = event["opponent"]["title"]
                time_str = event.get("time", "TBA")
                print(f"  - {sport}: vs {opponent} at {time_str}")
            break
    else:
        print("No games found on January 14")

    # Count total games in January
    total_games = sum(len(day.get("events") or []) for day in jan_data)
    print(f"\nTotal games in January data: {total_games}")

# Test with April 2026
print("\n" + "=" * 70)
print("April 2026 Calendar Data")
print("=" * 70)

april_data = fetch_calendar_month(date(2026, 4, 15))

if april_data:
    # Find any games in April
    april_games = []
    for day in april_data:
        if day.get("events") and day["date"].startswith("2026-04"):
            april_games.extend(day["events"])

    print(f"Found {len(april_games)} games in April")
    if april_games:
        print("Sample games:")
        for event in april_games[:5]:
            sport = event["sport"]["title"]
            opponent = event["opponent"]["title"]
            date_str = event["date"].split("T")[0]
            print(f"  - {date_str}: {sport} vs {opponent}")
