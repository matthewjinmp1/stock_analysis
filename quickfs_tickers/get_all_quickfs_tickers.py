#!/usr/bin/env python3
"""
Script to fetch all available tickers from QuickFS API across all supported exchanges.

This script:
1. Gets API metadata to discover all supported countries and exchanges
2. Fetches all companies for each exchange
3. Combines all tickers into a single list
4. Saves the results to a JSON file

Usage:
    python get_all_quickfs_tickers.py
    python get_all_quickfs_tickers.py --output custom_tickers.json
    python get_all_quickfs_tickers.py --verbose

Requirements:
- QuickFS API key in config.py or QUICKFS_API_KEY environment variable
- quickfs package: pip install quickfs
"""

import json
import os
import sys
import argparse
from typing import List, Dict, Set
from quickfs import QuickFS

# Add project root to path to find config.py
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
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

def get_api_metadata(client: QuickFS) -> Dict:
    """
    Get API metadata to discover supported countries and exchanges.

    Args:
        client: QuickFS API client

    Returns:
        Dictionary containing metadata about supported countries and exchanges
    """
    try:
        print("Fetching API metadata...")
        metadata = client.get_api_metadata()

        if not metadata:
            print("Warning: No metadata returned from API")
            return {}

        return metadata
    except Exception as e:
        print(f"Error fetching API metadata: {e}")
        return {}

def parse_metadata_countries(metadata: Dict) -> List[tuple]:
    """
    Parse metadata to extract country and exchange combinations.

    Args:
        metadata: API metadata dictionary

    Returns:
        List of (country, exchange) tuples
    """
    country_exchanges = []

    # Try different possible structures in the metadata
    if 'countries' in metadata:
        countries_data = metadata['countries']
        if isinstance(countries_data, dict):
            for country_code, country_info in countries_data.items():
                if isinstance(country_info, dict) and 'exchanges' in country_info:
                    exchanges = country_info['exchanges']
                    if isinstance(exchanges, list):
                        for exchange in exchanges:
                            country_exchanges.append((country_code, exchange))
                    elif isinstance(exchanges, dict):
                        for exchange in exchanges.keys():
                            country_exchanges.append((country_code, exchange))
                elif isinstance(country_info, list):
                    # Country info is a list of exchanges
                    for exchange in country_info:
                        country_exchanges.append((country_code, exchange))

    # If metadata structure is different, try fallback methods
    if not country_exchanges:
        print("Warning: Could not parse metadata structure. Using known exchanges...")
        # Known exchanges based on QuickFS documentation
        known_exchanges = [
            ('US', 'NYSE'),
            ('US', 'NASDAQ'),
            ('CA', 'TSX'),
            ('LN', 'LSE'),
            ('AU', 'ASX'),
            ('NZ', 'NZX'),
            ('MM', 'YSX')
        ]
        country_exchanges = known_exchanges

    return country_exchanges

def get_supported_companies(client: QuickFS, country: str, exchange: str, verbose: bool = False) -> List[str]:
    """
    Get all supported companies for a specific country and exchange.

    Args:
        client: QuickFS API client
        country: Country code (e.g., 'US')
        exchange: Exchange code (e.g., 'NYSE')
        verbose: If True, print detailed progress

    Returns:
        List of ticker symbols
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
            print(f"    Found {len(tickers)} tickers for {country}/{exchange}")

        return tickers

    except Exception as e:
        error_str = str(e).lower()
        if '429' in error_str or 'rate limit' in error_str:
            print(f"    Rate limit hit for {country}/{exchange}, skipping...")
        else:
            print(f"    Error fetching {country}/{exchange}: {e}")
        return []

def fetch_all_tickers(verbose: bool = False) -> Dict:
    """
    Fetch all available tickers from all supported exchanges.

    Args:
        verbose: If True, print detailed progress

    Returns:
        Dictionary containing tickers organized by exchange and summary stats
    """
    try:
        client = QuickFS(API_KEY)

        # Get API metadata
        metadata = get_api_metadata(client)
        country_exchanges = parse_metadata_countries(metadata)

        if verbose:
            print(f"Found {len(country_exchanges)} country/exchange combinations:")
            for country, exchange in country_exchanges:
                print(f"  {country}/{exchange}")
            print()

        # Fetch tickers for each exchange
        all_tickers = []
        exchange_counts = {}

        for country, exchange in country_exchanges:
            tickers = get_supported_companies(client, country, exchange, verbose)
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
        description="Fetch all available tickers from QuickFS API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python get_all_quickfs_tickers.py
  python get_all_quickfs_tickers.py --verbose
  python get_all_quickfs_tickers.py --output my_tickers.json
  python get_all_quickfs_tickers.py --verbose --output custom_tickers.json
        """
    )

    parser.add_argument(
        '--output', '-o',
        default='data/quickfs_all_tickers.json',
        help='Output JSON file path (default: data/quickfs_all_tickers.json)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output with detailed progress'
    )

    args = parser.parse_args()

    print(f"{'='*60}")
    print("QuickFS All Tickers Fetcher")
    print(f"{'='*60}")
    print("Fetching all available tickers from QuickFS API...")
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