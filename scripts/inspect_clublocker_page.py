"""
Inspect ClubLocker roster page structure

This script loads the ClubLocker roster page with Selenium and inspects
its HTML structure to determine the correct selectors for parsing.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.service import Service  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402
from webdriver_manager.chrome import ChromeDriverManager  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402


def inspect_clublocker_page(team_id="40879"):
    """Inspect ClubLocker roster page structure"""

    print(f"Inspecting ClubLocker team {team_id} roster page...")
    print("=" * 80)

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Load the page
        url = f"https://clublocker.com/teams/{team_id}/roster"
        print(f"\n1. Loading URL: {url}")
        driver.get(url)

        # Wait for Angular to render
        print("2. Waiting 10 seconds for Angular to render...")
        time.sleep(10)

        # Parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Check page title
        print("\n" + "=" * 80)
        print("PAGE TITLE:")
        print("=" * 80)
        title = soup.find("title")
        if title:
            print(f"  {title.text.strip()}")

        # Look for tables
        print("\n" + "=" * 80)
        print("TABLES:")
        print("=" * 80)
        tables = soup.find_all("table")
        print(f"  Number of tables found: {len(tables)}")

        for i, table in enumerate(tables):
            print(f"\n  Table {i+1}:")
            print(f"    Classes: {table.get('class')}")
            print(f"    ID: {table.get('id')}")

            # Get headers
            headers = table.find_all("th")
            if headers:
                header_texts = [h.text.strip() for h in headers]
                print(f"    Headers ({len(headers)}): {header_texts}")

            # Count rows
            rows = table.find_all("tr")
            print(f"    Total rows: {len(rows)}")

            # Show first few data rows
            if len(rows) > 1:
                print("    First 3 data rows:")
                for j, row in enumerate(rows[1:4], 1):
                    cells = row.find_all(["td", "th"])
                    cell_texts = [c.text.strip()[:30] for c in cells]
                    print(f"      Row {j}: {cell_texts}")

        # Look for divs with roster-related classes
        print("\n" + "=" * 80)
        print("ROSTER DIVS/SECTIONS:")
        print("=" * 80)

        roster_keywords = ["roster", "player", "squad", "team"]
        for keyword in roster_keywords:
            elements = soup.find_all(
                ["div", "section"], class_=lambda x: x and keyword in str(x).lower() if x else False
            )
            if elements:
                print(f"\n  Elements with '{keyword}' in class ({len(elements)}):")
                for elem in elements[:3]:
                    print(f"    - Tag: {elem.name}, Classes: {elem.get('class')}")
                    # Get first 100 chars of text
                    text_preview = elem.get_text(strip=True)[:100]
                    if text_preview:
                        print(f"      Text preview: {text_preview}...")

        # Look for win-related elements
        print("\n" + "=" * 80)
        print("WIN/RECORD ELEMENTS:")
        print("=" * 80)

        win_keywords = ["win", "record", "w-l", "match"]
        for keyword in win_keywords:
            elements = soup.find_all(
                ["span", "div", "td"], class_=lambda x: x and keyword in str(x).lower() if x else False
            )
            if elements:
                print(f"\n  Elements with '{keyword}' in class ({len(elements)}):")
                for elem in elements[:5]:
                    elem_text = elem.text.strip()[:50]
                    print(f"    - Tag: {elem.name}, Classes: {elem.get('class')}, Text: {elem_text}")

        # Look for any elements with numbers that might be wins
        print("\n" + "=" * 80)
        print("POTENTIAL STAT ELEMENTS (numbers):")
        print("=" * 80)

        # Look for patterns like "X-Y" (wins-losses) or just numbers
        import re

        stat_pattern = re.compile(r"\d+-\d+|\d+\s*W")

        all_text_elements = soup.find_all(["td", "span", "div"], limit=100)
        stat_elements = []
        for elem in all_text_elements:
            text = elem.text.strip()
            if stat_pattern.search(text):
                stat_elements.append(elem)

        if stat_elements:
            print(f"  Found {len(stat_elements)} elements with stat-like patterns:")
            for elem in stat_elements[:10]:
                print(f"    - Tag: {elem.name}, Classes: {elem.get('class')}, Text: {elem.text.strip()}")

        # Save a snippet of the HTML for reference
        print("\n" + "=" * 80)
        print("SAVING HTML SNIPPET:")
        print("=" * 80)

        output_file = Path(__file__).parent / "clublocker_page_structure.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        print(f"  Full HTML saved to: {output_file}")

        # Save just the roster section if we can find it
        main_content = soup.find("main") or soup.find("div", {"id": "content"}) or soup.body
        if main_content:
            roster_snippet = Path(__file__).parent / "clublocker_roster_snippet.html"
            with open(roster_snippet, "w", encoding="utf-8") as f:
                f.write(main_content.prettify())
            print(f"  Main content saved to: {roster_snippet}")

        print("\n" + "=" * 80)
        print("INSPECTION COMPLETE")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Review the output above to understand the page structure")
        print("2. Check the saved HTML files for detailed structure")
        print("3. Update squash_fetcher.py _parse_roster() with correct selectors")

    finally:
        driver.quit()
        print("\nWebDriver closed.")


if __name__ == "__main__":
    inspect_clublocker_page()
