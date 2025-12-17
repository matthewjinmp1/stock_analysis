#!/usr/bin/env python3
"""
Create a database with all QuickFS tickers
Combines data from quickfs_all_tickers.json and remaining_exchanges_tickers.json
"""

import json
import sqlite3
import os
import sys

# Ensure project root is on path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Paths to data files
MAIN_TICKERS_FILE = os.path.join(PROJECT_ROOT, 'quickfs_tickers', 'quickfs_all_tickers.json')
REMAINING_TICKERS_FILE = os.path.join(PROJECT_ROOT, 'quickfs_tickers', 'remaining_exchanges_tickers.json')
OUTPUT_DB = os.path.join(PROJECT_ROOT, 'quickfs_tickers', 'quickfs_tickers.db')

def load_main_tickers():
    """Load tickers from the main collection."""
    if not os.path.exists(MAIN_TICKERS_FILE):
        print(f"Warning: {MAIN_TICKERS_FILE} not found")
        return []

    try:
        with open(MAIN_TICKERS_FILE, 'r') as f:
            data = json.load(f)

        tickers = data.get('tickers', [])
        print(f"Loaded {len(tickers)} tickers from main collection")
        return tickers
    except Exception as e:
        print(f"Error loading main tickers: {e}")
        return []

def load_remaining_tickers():
    """Load tickers from the remaining exchanges collection."""
    if not os.path.exists(REMAINING_TICKERS_FILE):
        print(f"Warning: {REMAINING_TICKERS_FILE} not found")
        return []

    try:
        with open(REMAINING_TICKERS_FILE, 'r') as f:
            data = json.load(f)

        tickers = data.get('new_tickers', [])
        print(f"Loaded {len(tickers)} tickers from remaining exchanges")
        return tickers
    except Exception as e:
        print(f"Error loading remaining tickers: {e}")
        return []

def create_database(main_tickers, remaining_tickers):
    """Create database with all QuickFS tickers."""

    # Combine and deduplicate tickers
    all_tickers = list(set(main_tickers + remaining_tickers))
    all_tickers.sort()  # Sort alphabetically

    print(f"\nCombined data:")
    print(f"  From main collection: {len(main_tickers)}")
    print(f"  From remaining exchanges: {len(remaining_tickers)}")
    print(f"  Total unique tickers: {len(all_tickers)}")
    print(f"  Duplicates removed: {len(main_tickers) + len(remaining_tickers) - len(all_tickers)}")

    # Create database directory if needed
    os.makedirs(os.path.dirname(OUTPUT_DB), exist_ok=True)

    # Create database
    conn = sqlite3.connect(OUTPUT_DB)
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickers (
            ticker TEXT PRIMARY KEY,
            company_name TEXT,
            source TEXT DEFAULT 'quickfs'
        )
    ''')

    # Clear existing data
    cursor.execute('DELETE FROM tickers')

    # Insert data (company_name will be NULL since QuickFS doesn't provide names)
    ticker_data = [(ticker, None, 'quickfs') for ticker in all_tickers]
    cursor.executemany(
        'INSERT INTO tickers (ticker, company_name, source) VALUES (?, ?, ?)',
        ticker_data
    )

    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON tickers(ticker)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON tickers(source)')

    conn.commit()
    conn.close()

    print(f"\nCreated database: {OUTPUT_DB}")
    print(f"Inserted {len(all_tickers)} tickers")

    # Show sample
    print("\nSample tickers:")
    for ticker in all_tickers[:15]:
        print(f"  {ticker}")

    if len(all_tickers) > 15:
        print(f"  ... and {len(all_tickers) - 15} more")

def main():
    """Main function."""
    print("=" * 70)
    print("Creating QuickFS Tickers Database")
    print("=" * 70)

    # Load data
    main_tickers = load_main_tickers()
    remaining_tickers = load_remaining_tickers()

    if not main_tickers and not remaining_tickers:
        print("\nError: No ticker data found!")
        return

    # Create database
    create_database(main_tickers, remaining_tickers)

    print("\n" + "=" * 70)
    print("Database created successfully!")
    print(f"Location: {OUTPUT_DB}")
    print("Note: Company names are NULL (not provided by QuickFS API)")
    print("=" * 70)

if __name__ == '__main__':
    main()