#!/usr/bin/env python3
"""
Simple script to get short interest (short float) for a single ticker.
Uses the existing Finviz short interest scraper logic from src/scrapers/get_short_interest.py.

Usage:
    python get_short_interest.py AAPL
    python get_short_interest.py      # will prompt for ticker
"""

import os
import sys
import shutil
import json

# Ensure project root is on path so we can import src modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.scrapers.get_short_interest import scrape_ticker_short_interest


def get_short_interest_for_ticker(ticker: str):
    """
    Get short interest for a single ticker using existing scraper logic.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        dict or None: Result from scrape_ticker_short_interest, or None on error
    """
    # Ensure we run with project root as CWD so any relative paths inside the scraper
    # (if added later) will still work correctly.
    prev_cwd = os.getcwd()
    try:
        os.chdir(PROJECT_ROOT)
        return scrape_ticker_short_interest(ticker)
    finally:
        os.chdir(prev_cwd)


def process_ticker(ticker: str) -> bool:
    """Fetch and display short interest for a single ticker."""
    ticker = ticker.strip().upper()
    if not ticker:
        print("Error: No ticker provided.")
        return False

    print(f"\nFetching short interest (short float) for {ticker}...")
    print("=" * 80)

    result = get_short_interest_for_ticker(ticker)

    if not result:
        print(f"Error: Could not fetch short interest for {ticker}.")
        return False

    short_float = result.get("short_float")
    scraped_at = result.get("scraped_at")
    note = result.get("note")

    print(f"Ticker: {result.get('ticker', ticker)}")
    if short_float is not None:
        print(f"Short Float: {short_float}")
    else:
        print("Short Float: (no data available)")
        if note:
            print(f"Note: {note}")
    if scraped_at:
        print(f"Scraped At: {scraped_at}")

    print("=" * 80)

    # Also print JSON for easy machine parsing
    print("\nJSON OUTPUT:")
    print("=" * 80)
    print(json.dumps(result, indent=2))

    return True


def main() -> None:
    """Run single-ticker short interest lookup (CLI arg once, or continuous prompt)."""
    # If command-line argument provided, run once and exit (backward compatibility)
    if len(sys.argv) >= 2:
        ticker = sys.argv[1].strip().upper()
        ok = process_ticker(ticker)
        sys.exit(0 if ok else 1)

    # Otherwise, run continuously
    print("Short Interest Lookup (Finviz short float)")
    print("=" * 80)
    print("Enter ticker symbols to look up short interest.")
    print("Type 'quit', 'exit', or 'q' to exit.")
    print("=" * 80)

    try:
        while True:
            ticker = input("\nEnter ticker symbol: ").strip()

            if not ticker:
                continue

            if ticker.lower() in ("quit", "exit", "q"):
                print("\nExiting...")
                break

            process_ticker(ticker)
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    except EOFError:
        print("\n\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()

