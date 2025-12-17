#!/usr/bin/env python3
"""
Improved script to fetch all available tickers from QuickFS API across all supported exchanges.
This version handles the QuickFS library bug where some exchanges return lists instead of dicts.
"""

import json
import os
import sys
import argparse
import requests
from typing import List, Dict, Set
from quickfs import QuickFS

# Add project root to path to find config.py
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Try to import config, fallback to environment variable
try:
    from config import QUICKFS_API_KEY
    API_KEY = QUICKFS_API_KEY
except ImportError:
    # Try environment variable
    API_KEY = os.environ.get('QUICKFS_API_KEY')
    if not API_KEY:
        print("Error: QuickFS API key not found.")
        print("Please set QUICKFS_API_KEY environment variable or create config.py with QUICKFS_API_KEY")
        print(f"Looking for config.py at: {os.path.join(PROJECT_ROOT, 'config.py')}")
        sys.exit(1)

def get_supported_companies_direct(country: str, exchange: str, api_key: str, verbose: bool = False) -> List[str]:
    """
    Get supported companies directly using requests to bypass QuickFS library bugs.

    Args:
        country: Country code (e.g., 'US')
        exchange: Exchange code (e.g., 'NYSE')
        api_key: QuickFS API key
        verbose: If True, print detailed progress

    Returns:
        List of ticker symbols
    """
    try:
        if verbose:
            print(f"  Fetching {country}/{exchange} (direct API call)...")

        # Direct API call to bypass QuickFS library issues
        url = "https://public-api.quickfs.net/v1/companies"
        params = {
            "api_key": api_key,
            "country": country,
            "exchange": exchange
        }

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Handle different response formats
        companies = []
        if isinstance(data, list):
            # Direct list of tickers
            companies = data
        elif isinstance(data, dict):
            # Check various possible keys
            for key in ['companies', 'tickers', 'symbols', 'data']:
                if key in data and isinstance(data[key], list):
                    companies = data[key]
                    break
            # If no list found, check if the dict values contain lists
            if not companies:
                for key, value in data.items():
                    if isinstance(value, list):
                        companies = value
                        break

        if not companies:
            if verbose:
                print(f"    No companies found in response for {country}/{exchange}")
            return []

        # Extract ticker symbols
        tickers = []
        for company in companies:
            if isinstance(company, str):
                # Direct ticker string like "AAPL:US"
                ticker = company.replace(f':{country}', '').strip()
                if ticker:
                    tickers.append(ticker)
            elif isinstance(company, dict):
                # Dictionary with ticker info
                ticker = company.get('ticker') or company.get('symbol') or company.get('code')
                if ticker:
                    ticker = str(ticker).replace(f':{country}', '').strip()
                    if ticker:
                        tickers.append(ticker)

        if verbose:
            print(f"    Found {len(tickers)} tickers for {country}/{exchange}")

        return tickers

    except Exception as e:
        if verbose:
            print(f"    Direct API call failed for {country}/{exchange}: {e}")
        return []

def get_supported_companies_fallback(client: QuickFS, country: str, exchange: str, verbose: bool = False) -> List[str]:
    """
    Try QuickFS library first, fall back to direct API call if it fails.

    Args:
        client: QuickFS API client
        country: Country code (e.g., 'US')
        exchange: Exchange code (e.g., 'NYSE')
        verbose: If True, print detailed progress

    Returns:
        List of ticker symbols
    """
    # First try the QuickFS library method
    try:
        if verbose:
            print(f"  Fetching {country}/{exchange} (QuickFS library)...")

        companies = client.get_supported_companies(country=country, exchange=exchange)

        if not companies:
            if verbose:
                print(f"    No companies returned for {country}/{exchange}")
            return []

        # Extract ticker symbols
        tickers = []
        if isinstance(companies, list):
            for company in companies:
                if isinstance(company, str):
                    # If it's already a string (ticker symbol)
                    ticker = company.replace(f':{country}', '').strip()
                    if ticker:
                        tickers.append(ticker)
                elif isinstance(company, dict):
                    # If it's a dictionary, try to extract ticker from common fields
                    ticker = company.get('ticker') or company.get('symbol') or company.get('code')
                    if ticker:
                        ticker = str(ticker).replace(f':{country}', '').strip()
                        if ticker:
                            tickers.append(ticker)
        elif isinstance(companies, dict):
            # Handle case where companies is a dict
            for key, value in companies.items():
                if isinstance(value, list):
                    for company in value:
                        if isinstance(company, str):
                            ticker = company.replace(f':{country}', '').strip()
                            if ticker:
                                tickers.append(ticker)
                        elif isinstance(company, dict):
                            ticker = company.get('ticker') or company.get('symbol') or company.get('code')
                            if ticker:
                                ticker = str(ticker).replace(f':{country}', '').strip()
                                if ticker:
                                    tickers.append(ticker)
                elif isinstance(value, str):
                    ticker = value.replace(f':{country}', '').strip()
                    if ticker:
                        tickers.append(ticker)

        if verbose:
            print(f"    Found {len(tickers)} tickers for {country}/{exchange} (library)")

        return tickers

    except Exception as e:
        error_str = str(e).lower()
        if '429' in error_str or 'rate limit' in error_str:
            if verbose:
                print(f"    Rate limit hit for {country}/{exchange}, skipping...")
            return []
        else:
            if verbose:
                print(f"    QuickFS library failed for {country}/{exchange}: {e}")
                print("    Trying direct API call...")
            # Fall back to direct API call
            return get_supported_companies_direct(country, exchange, API_KEY, verbose)

def fetch_all_tickers(verbose: bool = False) -> Dict:
    """
    Fetch all available tickers from all supported exchanges using improved error handling.

    Args:
        verbose: If True, print detailed progress

    Returns:
        Dictionary containing tickers organized by exchange and summary stats
    """
    try:
        client = QuickFS(API_KEY)

        # All known exchanges from QuickFS documentation
        country_exchanges = [
            ('US', 'NYSE'),
            ('US', 'NASDAQ'),
            ('CA', 'TSX'),
            ('LN', 'LSE'),
            ('AU', 'ASX'),
            ('NZ', 'NZX'),
            ('MM', 'YSX')
        ]

        if verbose:
            print(f"Found {len(country_exchanges)} country/exchange combinations:")
            for country, exchange in country_exchanges:
                print(f"  {country}/{exchange}")
            print()

        # Fetch tickers for each exchange
        all_tickers = []
        exchange_counts = {}

        for country, exchange in country_exchanges:
            tickers = get_supported_companies_fallback(client, country, exchange, verbose)
            if tickers:
                exchange_key = f"{country}_{exchange}"
                exchange_counts[exchange_key] = len(tickers)
                all_tickers.extend(tickers)

        # Remove duplicates while preserving order
        seen = set()
        unique_tickers = []
        for ticker in all_tickers:
            if ticker and ticker not in seen:
                seen.add(ticker)
                unique_tickers.append(ticker)

        # Sort tickers alphabetically
        unique_tickers.sort()

        result = {
            "total_tickers": len(unique_tickers),
            "total_exchanges": len(country_exchanges),
            "exchange_counts": exchange_counts,
            "tickers": unique_tickers
        }

        return result

    except Exception as e:
        print(f"Error fetching tickers: {e}")
        return {}

def save_to_json(data: Dict, filename: str, verbose: bool = False):
    """
    Save ticker data to JSON file.

    Args:
        data: Dictionary containing ticker data
        filename: Output filename
        verbose: If True, print detailed output
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        if verbose:
            print(f"\n{'='*60}")
            print("SUMMARY")
            print(f"{'='*60}")
            print(f"Total exchanges queried: {data.get('total_exchanges', 0)}")
            print(f"Total unique tickers: {data.get('total_tickers', 0)}")
            print(f"Data saved to: {filename}")
            print(f"{'='*60}")

            # Show breakdown by exchange
            exchange_counts = data.get('exchange_counts', {})
            if exchange_counts:
                print("\nTickers by exchange:")
                for exchange, count in sorted(exchange_counts.items()):
                    print(f"  {exchange}: {count}")
                print()

            # Show sample tickers
            tickers = data.get('tickers', [])
            if tickers:
                print("Sample tickers (first 20):")
                for i, ticker in enumerate(tickers[:20], 1):
                    print(f"  {i:2}. {ticker}")
                if len(tickers) > 20:
                    print(f"  ... and {len(tickers) - 20} more")

        else:
            print(f"\nData saved to {filename}")
            print(f"Total tickers: {data.get('total_tickers', 0)}")

    except Exception as e:
        print(f"Error saving to {filename}: {e}")

def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Fetch all available tickers from QuickFS API across all supported exchanges (improved version)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python get_all_tickers_improved.py
  python get_all_tickers_improved.py --verbose
  python get_all_tickers_improved.py --output all_tickers_improved.json
  python get_all_tickers_improved.py --verbose --output custom_tickers.json

This improved version handles QuickFS library bugs where some exchanges return
lists instead of dictionaries, using direct API calls as fallback.
        """
    )

    parser.add_argument(
        '--output', '-o',
        default='all_tickers_improved.json',
        help='Output JSON file path (default: all_tickers_improved.json)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output with detailed progress'
    )

    args = parser.parse_args()

    print(f"{'='*70}")
    print("QuickFS All Tickers Fetcher (Improved Version)")
    print(f"{'='*70}")
    print("Fetching all available tickers from QuickFS API...")
    print("This version handles library bugs with fallback to direct API calls.")
    print(f"Output file: {args.output}")
    print()

    # Fetch all tickers
    data = fetch_all_tickers(verbose=args.verbose)

    if not data:
        print("No data was fetched. Please check your API key and connection.")
        sys.exit(1)

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating output directory {output_dir}: {e}")
            sys.exit(1)

    # Save to JSON file
    save_to_json(data, args.output, verbose=args.verbose)

    print("\nDone!")

if __name__ == '__main__':
    main()