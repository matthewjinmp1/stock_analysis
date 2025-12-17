#!/usr/bin/env python3
"""
Get all tickers from ALL supported QuickFS exchanges using correct exchange codes
"""

import json
import os
import sys
import argparse
from typing import List, Dict, Set
from quickfs import QuickFS

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
        print("Please set QUICKFS_API_KEY environment variable or create config.py with QUICKFS_API_KEY")
        print(f"Looking for config.py at: {os.path.join(PROJECT_ROOT, 'config.py')}")
        sys.exit(1)

def get_supported_companies_safe(client: QuickFS, country: str, exchange: str, verbose: bool = False) -> List[str]:
    """
    Safely get supported companies with proper error handling
    """
    try:
        if verbose:
            print(f"  Fetching {country}/{exchange}...")

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

        if verbose:
            print(f"    Found {len(tickers)} tickers for {country}/{exchange}")

        return tickers

    except Exception as e:
        error_str = str(e).lower()
        if '429' in error_str or 'rate limit' in error_str:
            if verbose:
                print(f"    Rate limit hit for {country}/{exchange}, skipping...")
        else:
            if verbose:
                print(f"    Error fetching {country}/{exchange}: {e}")
        return []

def fetch_all_tickers_correct(verbose: bool = False) -> Dict:
    """
    Fetch all available tickers using the CORRECT exchange codes from API metadata
    """
    try:
        client = QuickFS(API_KEY)

        # Correct exchange codes from API metadata
        country_exchanges = [
            # United States
            ('US', 'NYSE'),
            ('US', 'NASDAQ'),
            ('US', 'OTC'),
            ('US', 'NYSEARCA'),
            ('US', 'BATS'),
            ('US', 'NYSEAMERICAN'),

            # Canada
            ('CA', 'TORONTO'),      # Not TSX!
            ('CA', 'CSE'),
            ('CA', 'TSXVENTURE'),

            # Australia & New Zealand
            ('AU', 'ASX'),
            ('NZ', 'NZX'),

            # Mexico
            ('MM', 'BMV'),          # Not YSX!

            # London
            ('LN', 'LONDON')        # Not LSE!
        ]

        if verbose:
            print(f"Fetching from {len(country_exchanges)} supported exchanges:")
            for country, exchange in country_exchanges:
                print(f"  {country}/{exchange}")
            print()

        # Fetch tickers for each exchange
        all_tickers = []
        exchange_counts = {}

        for country, exchange in country_exchanges:
            tickers = get_supported_companies_safe(client, country, exchange, verbose)
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
    Save ticker data to JSON file
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
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Fetch all available tickers from ALL supported QuickFS exchanges",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Uses correct exchange codes from QuickFS API metadata.

Examples:
  python get_all_correct_exchanges.py
  python get_all_correct_exchanges.py --verbose
  python get_all_correct_exchanges.py --output all_quickfs_tickers_complete.json
        """
    )

    parser.add_argument(
        '--output', '-o',
        default='quickfs_tickers/all_quickfs_tickers_complete.json',
        help='Output JSON file path'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output with detailed progress'
    )

    args = parser.parse_args()

    print(f"{'='*70}")
    print("QuickFS Complete Tickers Fetcher")
    print(f"{'='*70}")
    print("Fetching tickers from ALL supported exchanges using correct codes...")
    print(f"Output file: {args.output}")
    print()

    # Fetch all tickers
    data = fetch_all_tickers_correct(verbose=args.verbose)

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