#!/usr/bin/env python3
"""
Scrape historical team IDs from NCAA stats website.

This script attempts to discover historical team IDs by:
1. Accessing the school's main page
2. Looking for links to different academic years
3. Extracting team IDs from each year's page
"""

import sys
import json
import time
import re
from datetime import datetime

sys.path.insert(0, "/Users/maxfieldma/CS/projects/StatsTracker")

from src.website_fetcher.ncaa_fetcher import HAVERFORD_SCHOOL_ID  # noqa: E402, F401
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.service import Service  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402, F401
from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402, F401
from selenium.webdriver.support import expected_conditions as EC  # noqa: E402, F401
from webdriver_manager.chrome import ChromeDriverManager  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402


def scrape_historical_ids(school_id=HAVERFORD_SCHOOL_ID):
    """
    Scrape historical team IDs for Haverford from NCAA website.

    Args:
        school_id: NCAA school ID

    Returns:
        Dict of {sport_key: {season: team_id}}
    """
    print("=" * 70)
    print("Scraping Historical Team IDs from NCAA Website")
    print("=" * 70)
    print()

    # Initialize Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)

    historical_data = {}

    try:
        # Access school page
        school_url = f"https://stats.ncaa.org/team/{school_id}"
        print(f"Accessing: {school_url}")
        driver.get(school_url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Look for academic year selector/dropdown
        print("\nLooking for academic year selector...")

        # Try to find year dropdown or links
        year_links = []

        # Method 1: Look for dropdown/select with years
        selects = soup.find_all("select")
        for select in selects:
            options = select.find_all("option")
            for option in options:
                text = option.get_text()
                if re.search(r"\d{4}-\d{2}", text):  # Match "2024-25" format
                    value = option.get("value")
                    if value:
                        year_links.append(
                            {
                                "year": text.strip(),
                                "url": f"https://stats.ncaa.org/team/{school_id}?academic_year={value}",
                            }
                        )

        # Method 2: Look for links with year patterns
        links = soup.find_all("a", href=True)
        for link in links:
            text = link.get_text()
            href = link.get("href")
            if re.search(r"\d{4}-\d{2}", text) and "academic_year" in href:
                year_links.append(
                    {"year": text.strip(), "url": f"https://stats.ncaa.org{href}" if href.startswith("/") else href}
                )

        if not year_links:
            print("⚠️  No year selector found - can only get current year")
            print("💡 NCAA may require manual navigation to access historical years")

            # Just get current year teams
            print("\nFetching current year teams...")
            teams = extract_teams_from_page(soup)

            if teams:
                current_year = f"{datetime.now().year}-{str(datetime.now().year + 1)[-2:]}"
                historical_data = organize_by_sport(teams, current_year)
        else:
            print(f"✓ Found {len(year_links)} academic years")

            # Visit each year and extract team IDs
            for year_info in year_links[:6]:  # Last 6 years
                year = year_info["year"]
                url = year_info["url"]

                print(f"\nFetching {year}... ", end="", flush=True)

                try:
                    driver.get(url)
                    time.sleep(2)

                    year_soup = BeautifulSoup(driver.page_source, "html.parser")
                    teams = extract_teams_from_page(year_soup)

                    if teams:
                        print(f"✓ Found {len(teams)} teams")

                        # Organize by sport and add to historical data
                        year_data = organize_by_sport(teams, year)

                        for sport, team_id in year_data.items():
                            if sport not in historical_data:
                                historical_data[sport] = {}
                            historical_data[sport][year] = team_id
                    else:
                        print("✗ No teams found")

                except Exception as e:
                    print(f"✗ Error: {e}")

    finally:
        driver.quit()

    return historical_data


def extract_teams_from_page(soup):
    """
    Extract team information from a BeautifulSoup page.

    Returns:
        List of {sport: str, team_id: int}
    """
    teams = []

    # Find team links (format: /teams/{team_id})
    team_links = soup.find_all("a", href=lambda x: x and "/teams/" in x)

    for link in team_links:
        href = link.get("href")
        text = link.get_text().strip()

        # Extract team ID from URL
        match = re.search(r"/teams/(\d+)", href)
        if match:
            team_id = int(match.group(1))

            # Clean up sport name (remove season year and record)
            sport_name = re.sub(r"^\d{4}-\d{2}\s+", "", text)
            sport_name = re.sub(r"\s*\(\d+-\d+(-\d+)?\)\s*$", "", sport_name)
            sport_name = sport_name.strip()

            if sport_name and team_id:
                teams.append({"sport": sport_name, "team_id": team_id})

    return teams


def organize_by_sport(teams, year):
    """
    Organize teams by sport key.

    Returns:
        Dict of {sport_key: team_id}
    """
    sport_mapping = {
        "Men's Basketball": "mens_basketball",
        "Women's Basketball": "womens_basketball",
        "Men's Soccer": "mens_soccer",
        "Women's Soccer": "womens_soccer",
        "Field Hockey": "field_hockey",
        "Women's Volleyball": "womens_volleyball",
        "Baseball": "baseball",
        "Men's Lacrosse": "mens_lacrosse",
        "Women's Lacrosse": "womens_lacrosse",
        "Softball": "softball",
    }

    organized = {}

    for team in teams:
        sport_name = team["sport"]
        if sport_name in sport_mapping:
            sport_key = sport_mapping[sport_name]
            organized[sport_key] = team["team_id"]

    return organized


def save_to_json(data, output_file="data/historical_team_ids.json"):
    """
    Save historical team IDs to JSON file.

    Args:
        data: Historical team ID data
        output_file: Output file path
    """
    try:
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\n✓ Saved to: {output_file}")
        return True
    except Exception as e:
        print(f"\n✗ Error saving: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape historical team IDs from NCAA website")
    parser.add_argument(
        "--school-id", type=int, default=HAVERFORD_SCHOOL_ID, help=f"NCAA school ID (default: {HAVERFORD_SCHOOL_ID})"
    )
    parser.add_argument(
        "--output",
        default="data/historical_team_ids.json",
        help="Output JSON file (default: data/historical_team_ids.json)",
    )

    args = parser.parse_args()

    print("\n⚠️  IMPORTANT:")
    print("NCAA's website structure may not expose historical years easily.")
    print("If scraping fails, you'll need to manually collect team IDs.")
    print()

    historical_data = scrape_historical_ids(args.school_id)

    if historical_data:
        print("\n" + "=" * 70)
        print("FOUND HISTORICAL TEAM IDs:")
        print("=" * 70)
        print(json.dumps(historical_data, indent=2))

        save_to_json(historical_data, args.output)
    else:
        print("\n⚠️  No historical data found")
        print("\n💡 ALTERNATIVE METHODS:")
        print("1. Manual collection: Browse NCAA stats site and record team IDs")
        print("2. Database records: If you've been storing data, query old team_ids")
        print("3. Git history: Check previous commits for old HAVERFORD_TEAMS values")
        print("4. Contact Haverford athletics: They may have historical team ID records")
