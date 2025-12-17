#!/usr/bin/env python3
"""
Test script to check what QuickFS get_supported_companies returns
"""

import json
import os
import sys
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
        sys.exit(1)

def test_get_supported_companies():
    """Test what get_supported_companies returns"""
    try:
        client = QuickFS(API_KEY)

        print("Testing get_supported_companies for NYSE...")

        # Get first few companies from NYSE
        companies = client.get_supported_companies(country='US', exchange='NYSE')

        if not companies:
            print("No companies returned")
            return

        print(f"Total companies returned: {len(companies)}")
        print(f"Type of response: {type(companies)}")

        # Show first 5 items
        print("\nFirst 5 items:")
        for i, company in enumerate(companies[:5]):
            print(f"{i+1}. Type: {type(company)}")
            if isinstance(company, str):
                print(f"   Value: {company}")
            elif isinstance(company, dict):
                print(f"   Keys: {list(company.keys())}")
                print(f"   Full dict: {company}")
            print()

        # Save full response to file
        output_file = 'data/quickfs_companies_raw.json'
        os.makedirs('data', exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(companies, f, indent=2)

        print(f"Full response saved to {output_file}")

        # Also save just the first 10 for easier inspection
        sample_file = 'data/quickfs_companies_sample.json'
        with open(sample_file, 'w') as f:
            json.dump(companies[:10], f, indent=2)

        print(f"Sample (first 10) saved to {sample_file}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_get_supported_companies()