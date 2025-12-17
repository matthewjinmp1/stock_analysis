#!/usr/bin/env python3
"""
Test the failing exchanges to see what they return
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

def test_failing_exchange(country, exchange):
    """Test a single failing exchange"""
    try:
        client = QuickFS(API_KEY)
        print(f"\nTesting {country}/{exchange}...")

        companies = client.get_supported_companies(country=country, exchange=exchange)

        print(f"Type: {type(companies)}")
        print(f"Length: {len(companies) if hasattr(companies, '__len__') else 'N/A'}")

        if hasattr(companies, '__getitem__') and len(companies) > 0:
            print("First item:")
            print(f"  Type: {type(companies[0])}")
            print(f"  Value: {repr(companies[0])}")

        # Save the raw response
        filename = f'{country}_{exchange}_raw.json'
        with open(filename, 'w') as f:
            json.dump(companies, f, indent=2)
        print(f"Saved raw response to {filename}")

        # Try to process it like the main script does
        tickers = []
        try:
            if isinstance(companies, list):
                print("Processing as list...")
                for company in companies[:5]:  # Just first 5
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
                print("Processing as dict...")
                for key, value in companies.items():
                    print(f"Dict key: {key}, type: {type(value)}")
                    if isinstance(value, list):
                        for company in value[:3]:  # Just first 3
                            if isinstance(company, str):
                                ticker = company.replace(f':{country}', '').strip()
                                if ticker:
                                    tickers.append(ticker)

            print(f"Extracted {len(tickers)} tickers from sample")
            if tickers:
                print(f"Sample tickers: {tickers}")

        except Exception as e:
            print(f"Error processing: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Test the failing exchanges"""
    failing_exchanges = [
        ('CA', 'TSX'),
        ('LN', 'LSE'),
        ('MM', 'YSX')
    ]

    for country, exchange in failing_exchanges:
        test_failing_exchange(country, exchange)

if __name__ == '__main__':
    main()