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
from datetime import datetime, date

# Ensure project root is on path so we can import src modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.scrapers.get_short_interest import scrape_ticker_short_interest

# Cache file for web app short-interest lookups
CACHE_FILE = os.path.join(os.path.dirname(__file__), "data", "short_interest_cache.json")


def load_cache() -> dict:
    """Load cached short-interest results from JSON file."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load cache file {CACHE_FILE}: {e}")
            return {}
    return {}


def save_cache(cache: dict) -> None:
    """Save cached short-interest results to JSON file."""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save cache file {CACHE_FILE}: {e}")


def get_cached_result(ticker: str) -> dict | None:
    """Return cached result for ticker if available."""
    cache = load_cache()
    key = ticker.strip().upper()
    if key in cache:
        cached = cache[key].copy()
        cached["_cached"] = True
        cached["_cached_at"] = cached.get("_cached_at", "unknown")
        return cached
    return None


def cache_result(ticker: str, result: dict) -> None:
    """Store result in cache for ticker."""
    cache = load_cache()
    key = ticker.strip().upper()
    entry = {k: v for k, v in result.items() if not k.startswith("_")}
    entry["_cached_at"] = datetime.now().isoformat()
    cache[key] = entry
    save_cache(cache)


def get_short_interest_for_ticker(ticker: str):
    """
    Get short interest for a single ticker using existing scraper logic, with caching.
    Automatically refreshes cached data if it's not from today.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        dict or None: Result from scrape_ticker_short_interest, or None on error
    """
    ticker = ticker.strip().upper()

    # Check cache first
    cached = get_cached_result(ticker)
    should_refetch = False
    
    if cached:
        # Check if the scraped_at date is today
        scraped_at_str = cached.get('scraped_at')
        if scraped_at_str:
            try:
                # Parse ISO format date: "2025-12-15T14:04:00.421697"
                scraped_at = datetime.fromisoformat(scraped_at_str).date()
                today = date.today()
                if scraped_at != today:
                    should_refetch = True
                    print(f"Cached data for {ticker} is from {scraped_at}, refreshing...")
            except (ValueError, AttributeError):
                # If date parsing fails, refetch to be safe
                should_refetch = True
                print(f"Could not parse date for cached {ticker}, refreshing...")
        else:
            # No date, refetch
            should_refetch = True
            print(f"No date found for cached {ticker}, refreshing...")
    else:
        # Not in cache, need to fetch
        should_refetch = True
    
    # If we have fresh cached data (from today), return it
    if cached and not should_refetch:
        print(f"Found cached short interest for {ticker} (cached at {cached.get('_cached_at', 'unknown')})")
        return cached

    # Fetch new data (either not cached or needs refresh)
    # Ensure we run with project root as CWD so any relative paths inside the scraper
    # (if added later) will still work correctly.
    prev_cwd = os.getcwd()
    try:
        os.chdir(PROJECT_ROOT)
        result = scrape_ticker_short_interest(ticker)
    finally:
        os.chdir(prev_cwd)

    if result:
        # Replace old cache entry with new data
        cache_result(ticker, result)
        print(f"Fetched and cached short interest for {ticker}")

    return result


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
    if result.get("_cached"):
        print(f"(Cached result from {result.get('_cached_at', 'unknown')})")

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

