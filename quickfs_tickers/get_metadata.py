#!/usr/bin/env python3
"""
Get QuickFS API metadata to discover all supported exchanges
"""

import json
import os
import sys

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

def get_metadata():
    """Get API metadata from QuickFS"""
    try:
        from quickfs import QuickFS

        print("Getting QuickFS API metadata...")
        client = QuickFS(API_KEY)
        metadata = client.get_api_metadata()

        print(f"Metadata type: {type(metadata)}")
        print(f"Metadata: {metadata}")

        if metadata:
            # Save metadata
            with open('quickfs_tickers/api_metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            print("Metadata saved to api_metadata.json")

            # Try to parse countries and exchanges
            if isinstance(metadata, dict) and 'countries' in metadata:
                countries = metadata['countries']
                print(f"\nFound countries: {list(countries.keys())}")

                all_exchanges = []
                for country_code, country_data in countries.items():
                    if isinstance(country_data, dict) and 'exchanges' in country_data:
                        exchanges = country_data['exchanges']
                        if isinstance(exchanges, list):
                            for exchange in exchanges:
                                all_exchanges.append((country_code, exchange))
                                print(f"  {country_code}: {exchange}")
                        elif isinstance(exchanges, dict):
                            for exchange in exchanges.keys():
                                all_exchanges.append((country_code, exchange))
                                print(f"  {country_code}: {exchange}")

                print(f"\nTotal exchange combinations found: {len(all_exchanges)}")
                return all_exchanges
            else:
                print("Unexpected metadata structure")
                return []
        else:
            print("No metadata returned")
            return []

    except Exception as e:
        print(f"Error getting metadata: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Main function"""
    exchanges = get_metadata()

    if exchanges:
        # Save exchange list
        with open('quickfs_tickers/all_supported_exchanges.json', 'w') as f:
            json.dump(exchanges, f, indent=2)
        print("All supported exchanges saved to all_supported_exchanges.json")

if __name__ == '__main__':
    main()