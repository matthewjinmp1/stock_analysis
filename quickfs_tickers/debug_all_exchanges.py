#!/usr/bin/env python3
"""
Debug script to test all exchanges and see what formats they return
"""

import json
import os
import sys
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
        sys.exit(1)

def test_exchange(client, country, exchange):
    """Test a single exchange and return detailed info"""
    try:
        print(f"\nTesting {country}/{exchange}...")

        companies = client.get_supported_companies(country=country, exchange=exchange)

        if not companies:
            print(f"  No companies returned")
            return {"country": country, "exchange": exchange, "status": "empty", "error": None}

        print(f"  Type: {type(companies)}")
        print(f"  Length: {len(companies) if hasattr(companies, '__len__') else 'N/A'}")

        # Show first few items
        if hasattr(companies, '__getitem__') and len(companies) > 0:
            print("  First 3 items:")
            for i, item in enumerate(companies[:3]):
                print(f"    [{i}]: {type(item)} - {repr(item)}")

        # Try to extract tickers
        tickers = []
        if isinstance(companies, list):
            for company in companies:
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
        elif isinstance(companies, dict):
            print("  Dictionary keys:")
            for key in companies.keys():
                print(f"    {key}: {type(companies[key])}")
                if isinstance(companies[key], list) and len(companies[key]) > 0:
                    print(f"      First item: {repr(companies[key][0])}")

        print(f"  Successfully extracted {len(tickers)} tickers")

        return {
            "country": country,
            "exchange": exchange,
            "status": "success",
            "response_type": str(type(companies)),
            "total_items": len(companies) if hasattr(companies, '__len__') else None,
            "tickers_extracted": len(tickers),
            "sample_tickers": tickers[:5],
            "error": None
        }

    except Exception as e:
        print(f"  Error: {e}")
        return {
            "country": country,
            "exchange": exchange,
            "status": "error",
            "error": str(e),
            "response_type": None,
            "total_items": None,
            "tickers_extracted": 0,
            "sample_tickers": []
        }

def main():
    """Test all known exchanges"""
    try:
        client = QuickFS(API_KEY)

        # All known exchanges from documentation
        exchanges = [
            ('US', 'NYSE'),
            ('US', 'NASDAQ'),
            ('CA', 'TSX'),
            ('LN', 'LSE'),
            ('AU', 'ASX'),
            ('NZ', 'NZX'),
            ('MM', 'YSX')
        ]

        results = []
        total_tickers = 0

        print("Testing all QuickFS exchanges...")
        print("=" * 60)

        for country, exchange in exchanges:
            result = test_exchange(client, country, exchange)
            results.append(result)
            if result["tickers_extracted"] > 0:
                total_tickers += result["tickers_extracted"]

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "error"]

        print(f"Successful exchanges: {len(successful)}")
        print(f"Failed exchanges: {len(failed)}")
        print(f"Total tickers extracted: {total_tickers}")

        print("\nSuccessful exchanges:")
        for result in successful:
            print(f"  {result['country']}/{result['exchange']}: {result['tickers_extracted']} tickers")

        print("\nFailed exchanges:")
        for result in failed:
            print(f"  {result['country']}/{result['exchange']}: {result['error']}")

        # Save detailed results
        with open('exchange_debug_results.json', 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nDetailed results saved to exchange_debug_results.json")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()