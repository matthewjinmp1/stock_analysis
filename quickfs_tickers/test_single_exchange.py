#!/usr/bin/env python3
"""
Test a single exchange to debug the hanging issue
"""

import json
import os
import sys
import time

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

def test_single_exchange(country, exchange):
    """Test one exchange"""
    print(f"Testing {country}/{exchange}...")

    try:
        from quickfs import QuickFS

        print("Creating QuickFS client...")
        client = QuickFS(API_KEY)
        print("Client created successfully")

        print("Calling get_supported_companies...")
        start_time = time.time()
        companies = client.get_supported_companies(country=country, exchange=exchange)
        end_time = time.time()

        print(f"Call completed in {end_time - start_time:.2f} seconds")
        print(f"Response type: {type(companies)}")

        if companies:
            print(f"Response length: {len(companies)}")
            if isinstance(companies, list) and len(companies) > 0:
                print(f"First item: {companies[0]}")
                print(f"Last item: {companies[-1]}")
        else:
            print("No companies returned")

        return companies

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Test one exchange at a time"""
    # Start with a known working exchange
    result = test_single_exchange('US', 'NYSE')

    if result:
        print("Success! Saving result...")
        with open('quickfs_tickers/test_result.json', 'w') as f:
            json.dump(result[:10], f, indent=2)  # Just first 10
        print("Result saved to test_result.json")

if __name__ == '__main__':
    main()