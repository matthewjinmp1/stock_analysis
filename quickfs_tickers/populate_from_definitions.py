#!/usr/bin/env python3
"""
Populate QuickFS database with company names from ticker_definitions.json
"""

import json
import sqlite3
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Change to project root directory
os.chdir(PROJECT_ROOT)

# File paths
TICKER_DEFINITIONS_FILE = os.path.join(PROJECT_ROOT, 'data', 'ticker_definitions.json')
DB_PATH = os.path.join(PROJECT_ROOT, 'quickfs_tickers', 'quickfs_tickers.db')

def load_ticker_definitions():
    """Load ticker definitions from JSON file"""
    if not os.path.exists(TICKER_DEFINITIONS_FILE):
        print(f"Error: {TICKER_DEFINITIONS_FILE} not found")
        return {}

    try:
        with open(TICKER_DEFINITIONS_FILE, 'r') as f:
            data = json.load(f)
        return data.get('definitions', {})
    except Exception as e:
        print(f"Error loading ticker definitions: {e}")
        return {}

def populate_company_names():
    """Populate company names from definitions into QuickFS database"""

    # Load ticker definitions
    ticker_definitions = load_ticker_definitions()
    if not ticker_definitions:
        print("No ticker definitions found")
        return

    print(f"Loaded {len(ticker_definitions)} ticker definitions")

    # Connect to database
    if not os.path.exists(DB_PATH):
        print(f"Error: Database {DB_PATH} not found")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get current stats
        cursor.execute("SELECT COUNT(*) as total, COUNT(company_name) as with_names FROM tickers")
        before_stats = cursor.fetchone()

        print(f"\nBefore population:")
        print(f"  Total tickers: {before_stats[0]}")
        print(f"  With company names: {before_stats[1]}")

        # Update company names where ticker exists in definitions
        successful = 0
        not_found = 0

        for ticker, company_name in ticker_definitions.items():
            # Check if ticker exists in our database
            cursor.execute("SELECT 1 FROM tickers WHERE ticker = ?", (ticker.upper(),))
            if cursor.fetchone():
                # Update the company name
                cursor.execute(
                    "UPDATE tickers SET company_name = ? WHERE ticker = ?",
                    (company_name.strip(), ticker.upper())
                )
                successful += 1
                print(f"  UPDATED: {ticker} -> {company_name}")
            else:
                not_found += 1
                print(f"  NOT FOUND: {ticker} not found in QuickFS database")

        conn.commit()

        # Get final stats
        cursor.execute("SELECT COUNT(*) as total, COUNT(company_name) as with_names FROM tickers")
        after_stats = cursor.fetchone()

        print(f"\n{'='*60}")
        print("POPULATION COMPLETE")
        print(f"{'='*60}")
        print(f"Definitions processed: {len(ticker_definitions)}")
        print(f"Successfully updated: {successful}")
        print(f"Not found in database: {not_found}")
        print(f"\nFinal database status:")
        print(f"  Total tickers: {after_stats[0]}")
        print(f"  With company names: {after_stats[1]} ({after_stats[1] - before_stats[1]} added)")
        print(f"  Success rate: {successful}/{len(ticker_definitions)} ({successful/len(ticker_definitions)*100:.1f}%)")

        # Show sample of updated tickers
        if successful > 0:
            print(f"\nSample of updated tickers:")
            cursor.execute("SELECT ticker, company_name FROM tickers WHERE company_name IS NOT NULL ORDER BY ticker LIMIT 10")
            samples = cursor.fetchall()
            for ticker, name in samples:
                print(f"  {ticker}: {name}")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Main function"""
    print("Populate QuickFS Database from Ticker Definitions")
    print("=" * 60)

    populate_company_names()

    print("\n" + "=" * 60)
    print("Done! You now have company names without using API credits!")
    print("=" * 60)

if __name__ == '__main__':
    main()