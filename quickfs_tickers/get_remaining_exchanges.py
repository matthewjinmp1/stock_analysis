#!/usr/bin/env python3
"""
Get tickers from the remaining exchanges that we haven't successfully fetched yet
"""

import json
import os
import sys
import requests
import time
from typing import List, Dict, Set

# Add project root to path to find config.py
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Change to project root directory so config.py can be found
os.chdir(PROJECT_ROOT)

# Try to import config, fallback to environment variable
try:
    from config import QUICKFS_API_KEY
    API_KEY = QUICKFS_API_KEY
except ImportError:
    # Try environment variable
    API_KEY = os.environ.get('QUICKFS_API_KEY')
    if not API_KEY:
        print("Error: QuickFS API key not found.")
        sys.exit(1)

def get_companies_direct_api(country: str, exchange: str, timeout: int = 10) -> List[str]:
    """
    Get companies using direct API call with timeout
    """
    try:
        print(f"  Trying direct API for {country}/{exchange}...")

        url = "https://public-api.quickfs.net/v1/companies"
        params = {
            "api_key": API_KEY,
            "country": country,
            "exchange": exchange
        }

        response = requests.get(url, params=params, timeout=timeout)

        if response.status_code == 200:
            data = response.json()

            # Handle different response formats
            companies = []
            if isinstance(data, list):
                companies = data
            elif isinstance(data, dict):
                # Check various possible keys
                for key in ['companies', 'tickers', 'symbols', 'data']:
                    if key in data and isinstance(data[key], list):
                        companies = data[key]
                        break

            if companies:
                # Extract tickers
                tickers = []
                for company in companies:
                    if isinstance(company, str):
                        ticker = company.replace(f':{country}', '').strip()
                        if ticker:
                            tickers.append(ticker)

                print(f"    Success: {len(tickers)} tickers")
                return tickers
            else:
                print("    No companies in response")
                return []
        else:
            print(f"    HTTP {response.status_code}: {response.text}")
            return []

    except requests.exceptions.Timeout:
        print(f"    Timeout after {timeout}s")
        return []
    except Exception as e:
        print(f"    Error: {e}")
        return []

def get_companies_library(country: str, exchange: str) -> List[str]:
    """
    Try using QuickFS library with short timeout
    """
    try:
        print(f"  Trying QuickFS library for {country}/{exchange}...")

        from quickfs import QuickFS
        client = QuickFS(API_KEY)

        # Set a short timeout by monkey-patching or just trying quickly
        companies = client.get_supported_companies(country=country, exchange=exchange)

        if companies and isinstance(companies, list):
            tickers = []
            for company in companies:
                if isinstance(company, str):
                    ticker = company.replace(f':{country}', '').strip()
                    if ticker:
                        tickers.append(ticker)

            print(f"    Success: {len(tickers)} tickers")
            return tickers
        else:
            print("    No companies returned")
            return []

    except Exception as e:
        print(f"    Library error: {e}")
        return []

def get_exchange_tickers(country: str, exchange: str) -> List[str]:
    """
    Try multiple methods to get tickers for an exchange
    """
    # First try library
    tickers = get_companies_library(country, exchange)
    if tickers:
        return tickers

    # If library fails, try direct API
    tickers = get_companies_direct_api(country, exchange)
    if tickers:
        return tickers

    print(f"  All methods failed for {country}/{exchange}")
    return []

def main():
    """Get tickers from remaining exchanges"""

    # Exchanges we haven't successfully gotten yet (from metadata)
    remaining_exchanges = [
        # US exchanges we don't have
        ('US', 'OTC'),
        ('US', 'NYSEARCA'),
        ('US', 'BATS'),
        ('US', 'NYSEAMERICAN'),

        # Canadian exchanges (correct codes)
        ('CA', 'TORONTO'),
        ('CA', 'CSE'),
        ('CA', 'TSXVENTURE'),

        # Mexican exchange
        ('MM', 'BMV'),

        # London exchange
        ('LN', 'LONDON')
    ]

    print(f"{'='*60}")
    print("Getting Remaining QuickFS Exchanges")
    print(f"{'='*60}")
    print(f"Attempting to fetch from {len(remaining_exchanges)} additional exchanges...")
    print()

    all_new_tickers = []
    successful_exchanges = {}

    for country, exchange in remaining_exchanges:
        print(f"\nTrying {country}/{exchange}:")
        tickers = get_exchange_tickers(country, exchange)

        if tickers:
            successful_exchanges[f"{country}_{exchange}"] = len(tickers)
            all_new_tickers.extend(tickers)

    # Remove duplicates
    seen = set()
    unique_new_tickers = []
    for ticker in all_new_tickers:
        if ticker and ticker not in seen:
            seen.add(ticker)
            unique_new_tickers.append(ticker)

    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")

    if successful_exchanges:
        print(f"Successfully fetched from {len(successful_exchanges)} exchanges:")
        for exchange, count in successful_exchanges.items():
            print(f"  {exchange}: {count} tickers")
        print(f"Total new unique tickers: {len(unique_new_tickers)}")

        # Save the new tickers
        result = {
            "new_tickers": unique_new_tickers,
            "exchange_counts": successful_exchanges,
            "total_new_tickers": len(unique_new_tickers)
        }

        with open('quickfs_tickers/remaining_exchanges_tickers.json', 'w') as f:
            json.dump(result, f, indent=2)

        print("Results saved to remaining_exchanges_tickers.json")

        # Show sample
        if unique_new_tickers:
            print(f"\nSample new tickers: {unique_new_tickers[:10]}")

    else:
        print("No additional exchanges were successfully fetched.")

    # Load existing tickers and combine
    try:
        with open('quickfs_tickers/quickfs_all_tickers.json', 'r') as f:
            existing_data = json.load(f)

        existing_tickers = existing_data.get('tickers', [])
        combined_tickers = list(set(existing_tickers + unique_new_tickers))
        combined_tickers.sort()

        print(f"\nCombined total: {len(combined_tickers)} tickers")
        print(f"  Existing: {len(existing_tickers)}")
        print(f"  New: {len(unique_new_tickers)}")
        print(f"  Overlap/removed: {len(existing_tickers) + len(unique_new_tickers) - len(combined_tickers)}")

        # Save combined result
        combined_result = {
            "total_tickers": len(combined_tickers),
            "existing_exchanges": existing_data.get('exchange_counts', {}),
            "new_exchanges": successful_exchanges,
            "tickers": combined_tickers
        }

        with open('quickfs_tickers/all_quickfs_tickers_combined.json', 'w') as f:
            json.dump(combined_result, f, indent=2)

        print("Combined results saved to all_quickfs_tickers_combined.json")

    except FileNotFoundError:
        print("Could not find existing tickers file to combine with.")

if __name__ == '__main__':
    main()