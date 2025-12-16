#!/usr/bin/env python3
"""
Create a database with ticker and company_name columns
using data from stock_tickers_clean.json and ticker_definitions.json
"""

import json
import sqlite3
import os
import sys

# Ensure project root is on path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Paths to data files
CLEAN_TICKERS_FILE = os.path.join(PROJECT_ROOT, 'data', 'stock_tickers_clean.json')
TICKER_DEFINITIONS_FILE = os.path.join(PROJECT_ROOT, 'data', 'ticker_definitions.json')
OUTPUT_DB = os.path.join(os.path.dirname(__file__), 'data', 'tickers.db')

def load_clean_tickers():
    """Load tickers from stock_tickers_clean.json."""
    if not os.path.exists(CLEAN_TICKERS_FILE):
        print(f"Warning: {CLEAN_TICKERS_FILE} not found")
        return {}
    
    try:
        with open(CLEAN_TICKERS_FILE, 'r') as f:
            data = json.load(f)
        
        tickers = {}
        for company in data.get('companies', []):
            ticker = company.get('ticker', '').upper()
            name = company.get('name', '').strip()
            if ticker and name:
                tickers[ticker] = name
        
        print(f"Loaded {len(tickers)} tickers from stock_tickers_clean.json")
        return tickers
    except Exception as e:
        print(f"Error loading clean tickers: {e}")
        return {}

def load_ticker_definitions():
    """Load tickers from ticker_definitions.json."""
    if not os.path.exists(TICKER_DEFINITIONS_FILE):
        print(f"Warning: {TICKER_DEFINITIONS_FILE} not found")
        return {}
    
    try:
        with open(TICKER_DEFINITIONS_FILE, 'r') as f:
            data = json.load(f)
        
        definitions = data.get('definitions', {})
        tickers = {}
        for ticker, name in definitions.items():
            ticker_upper = ticker.upper().strip()
            name_clean = name.strip()
            if ticker_upper and name_clean:
                tickers[ticker_upper] = name_clean
        
        print(f"Loaded {len(tickers)} tickers from ticker_definitions.json")
        return tickers
    except Exception as e:
        print(f"Error loading ticker definitions: {e}")
        return {}

def create_database(clean_tickers, ticker_definitions):
    """Create database with combined ticker data."""
    # Combine data: ticker_definitions take precedence
    all_tickers = clean_tickers.copy()
    
    # Add/override with ticker_definitions
    override_count = 0
    new_count = 0
    for ticker, name in ticker_definitions.items():
        if ticker in all_tickers:
            override_count += 1
        else:
            new_count += 1
        all_tickers[ticker] = name
    
    print(f"\nCombined data:")
    print(f"  From clean tickers: {len(clean_tickers)}")
    print(f"  From ticker definitions: {len(ticker_definitions)}")
    print(f"  Overrides: {override_count}")
    print(f"  New from definitions: {new_count}")
    print(f"  Total unique tickers: {len(all_tickers)}")
    
    # Create database
    os.makedirs(os.path.dirname(OUTPUT_DB), exist_ok=True)
    
    conn = sqlite3.connect(OUTPUT_DB)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickers (
            ticker TEXT PRIMARY KEY,
            company_name TEXT NOT NULL
        )
    ''')
    
    # Clear existing data
    cursor.execute('DELETE FROM tickers')
    
    # Insert data
    ticker_list = sorted(all_tickers.items())
    cursor.executemany(
        'INSERT INTO tickers (ticker, company_name) VALUES (?, ?)',
        ticker_list
    )
    
    # Create index
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON tickers(ticker)')
    
    conn.commit()
    conn.close()
    
    print(f"\nCreated database: {OUTPUT_DB}")
    print(f"Inserted {len(ticker_list)} tickers")
    
    # Show sample
    print("\nSample tickers:")
    for ticker, name in ticker_list[:10]:
        print(f"  {ticker:6} - {name}")

def main():
    """Main function."""
    print("=" * 60)
    print("Creating Ticker Database")
    print("=" * 60)
    
    # Load data
    clean_tickers = load_clean_tickers()
    ticker_definitions = load_ticker_definitions()
    
    if not clean_tickers and not ticker_definitions:
        print("\nError: No ticker data found!")
        return
    
    # Create database
    create_database(clean_tickers, ticker_definitions)
    
    print("\n" + "=" * 60)
    print("Done!")

if __name__ == '__main__':
    main()
