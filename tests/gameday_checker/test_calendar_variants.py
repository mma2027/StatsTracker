"""
Test different variations of the calendar endpoint
"""

import requests

base_url = "https://haverfordathletics.com"

# Test 1: Try the exact URL from browser
print("=" * 70)
print("Test 1: Direct URL with query string")
print("=" * 70)
url1 = f"{base_url}/services/responsive-calendar.ashx?type=month&sport=0&location=all&date=2/12/2026"
try:
    resp = requests.get(url1, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Length: {len(resp.text)}")
    if resp.status_code == 200:
        print(f"First 500 chars: {resp.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Try with headers mimicking browser
print("\n" + "=" * 70)
print("Test 2: With browser-like headers")
print("=" * 70)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://haverfordathletics.com/calendar",
    "X-Requested-With": "XMLHttpRequest",
}
url2 = f"{base_url}/services/responsive-calendar.ashx"
params = {"type": "month", "sport": "0", "location": "all", "date": "2/12/2026"}
try:
    resp = requests.get(url2, params=params, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Length: {len(resp.text)}")
    if resp.status_code == 200:
        print(f"First 500 chars: {resp.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Try POST instead of GET
print("\n" + "=" * 70)
print("Test 3: POST request")
print("=" * 70)
try:
    resp = requests.post(url2, data=params, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Length: {len(resp.text)}")
    if resp.status_code == 200:
        print(f"First 500 chars: {resp.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test 4: Check if the calendar page itself has any clues
print("\n" + "=" * 70)
print("Test 4: Check main calendar page")
print("=" * 70)
try:
    resp = requests.get(f"{base_url}/calendar", timeout=10)
    print(f"Status: {resp.status_code}")

    # Look for the calendar service URL in the page
    if "responsive-calendar" in resp.text:
        print("Found 'responsive-calendar' in page")
        # Extract the actual URL being used
        import re

        url_pattern = re.compile(r'["\']([^"\']*responsive-calendar[^"\']*)["\']')
        matches = url_pattern.findall(resp.text)
        if matches:
            print(f"Found {len(matches)} references:")
            for match in matches[:5]:
                print(f"  - {match}")
    else:
        print("'responsive-calendar' not found in page")

except Exception as e:
    print(f"Error: {e}")
