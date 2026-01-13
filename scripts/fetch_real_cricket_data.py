#!/usr/bin/env python3
"""
Fetch real cricket data using Selenium to bypass Cloudflare protection.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from src.website_fetcher.cricket_urls import get_url

def setup_driver():
    """Setup Chrome driver with options."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def fetch_table_with_selenium(url, stat_type):
    """Fetch cricket stats table using Selenium."""
    print(f"\n{'='*70}")
    print(f"Fetching {stat_type} statistics from:")
    print(f"{url}")
    print('='*70)

    driver = setup_driver()

    try:
        # Load page
        print(f"Loading page...")
        driver.get(url)

        # Wait for Cloudflare to load and table to appear
        print(f"Waiting for Cloudflare and table to load...")
        wait = WebDriverWait(driver, 30)
        table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

        # Give extra time for JavaScript to fully load
        time.sleep(3)

        print(f"✅ Table found, extracting data...")

        # Get page source and parse with pandas
        page_source = driver.page_source

        # Parse all tables and find the right one
        tables = pd.read_html(page_source)

        if not tables:
            print(f"❌ No tables found in page")
            return None

        # Usually the first or largest table contains the stats
        df = max(tables, key=lambda x: len(x))

        print(f"✅ Extracted {len(df)} rows, {len(df.columns)} columns")
        print(f"Columns: {list(df.columns)}")

        return df

    except Exception as e:
        print(f"❌ Error fetching {stat_type}: {e}")
        return None

    finally:
        driver.quit()

def main():
    """Fetch all cricket statistics and merge them."""
    print("\n" + "="*70)
    print("REAL CRICKET DATA FETCHER (Using Selenium)")
    print("="*70)

    # Fetch batting stats
    batting_url = get_url("batting")
    batting_df = fetch_table_with_selenium(batting_url, "BATTING")

    if batting_df is None:
        print("\n❌ Failed to fetch batting stats")
        return

    # Save batting to CSV
    batting_df.to_csv("csv_exports/batting_real.csv", index=False)
    print(f"💾 Saved to batting_real.csv")

    # Fetch bowling stats
    bowling_url = get_url("bowling")
    bowling_df = fetch_table_with_selenium(bowling_url, "BOWLING")

    if bowling_df is None:
        print("\n❌ Failed to fetch bowling stats")
        return

    # Save bowling to CSV
    bowling_df.to_csv("csv_exports/bowling_real.csv", index=False)
    print(f"💾 Saved to bowling_real.csv")

    # Fetch fielding stats
    fielding_url = get_url("fielding")
    fielding_df = fetch_table_with_selenium(fielding_url, "FIELDING")

    if fielding_df is None:
        print("\n❌ Failed to fetch fielding stats")
        return

    # Save fielding to CSV
    fielding_df.to_csv("csv_exports/fielding_real.csv", index=False)
    print(f"💾 Saved to fielding_real.csv")

    # Now merge using the manual merge script
    print("\n" + "="*70)
    print("MERGING DATA")
    print("="*70)

    import subprocess
    result = subprocess.run([
        "python", "src/website_fetcher/merge_manual_cricket_data.py",
        "--batting", "csv_exports/batting_real.csv",
        "--bowling", "csv_exports/bowling_real.csv",
        "--fielding", "csv_exports/fielding_real.csv",
        "--output", "csv_exports/haverford_cricket_stats.csv"
    ])

    if result.returncode == 0:
        print("\n" + "="*70)
        print("✅ SUCCESS! Real cricket data has been fetched and merged!")
        print("="*70)
        print(f"\n📁 Output file: haverford_cricket_stats.csv")
    else:
        print("\n❌ Merge failed")

if __name__ == "__main__":
    main()
