#!/usr/bin/env python3
"""
Test direct API calls to QuickFS to bypass library issues
"""

import json
import os
import sys
import requests

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

def test_direct_api_call(country, exchange):
    """Test a direct API call to QuickFS"""
    try:
        print(f"\nTesting direct API call for {country}/{exchange}...")

        url = "https://public-api.quickfs.net/v1/companies"
        params = {
            "api_key": API_KEY,
            "country": country,
            "exchange": exchange
        }

        print(f"URL: {url}")
        print(f"Params: {params}")

        response = requests.get(url, params=params, timeout=10)
        print(f"Status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response type: {type(data)}")
            if isinstance(data, list):
                print(f"List length: {len(data)}")
                if len(data) > 0:
                    print(f"First item: {repr(data[0])}")
                    print(f"Sample items: {data[:5]}")
            elif isinstance(data, dict):
                print(f"Dict keys: {list(data.keys())}")
                for key, value in data.items():
                    print(f"  {key}: {type(value)} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")
                    if isinstance(value, list) and len(value) > 0:
                        print(f"    First item: {repr(value[0])}")

            # Save response
            filename = f'direct_api_{country}_{exchange}.json'
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved to {filename}")

        else:
            print(f"Error response: {response.text}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Test direct API calls for different exchanges"""
    # Test working exchange first
    test_direct_api_call('US', 'NYSE')

    # Test failing exchanges
    test_direct_api_call('CA', 'TSX')
    test_direct_api_call('LN', 'LSE')

if __name__ == '__main__':
    main()