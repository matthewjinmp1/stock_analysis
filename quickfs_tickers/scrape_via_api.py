#!/usr/bin/env python3
"""
Scrape company names using QuickFS API instead of web scraping
"""

import os
import sys
import time
from typing import List, Dict, Optional

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Change to project root directory
os.chdir(PROJECT_ROOT)

# Try to import config
try:
    from config import QUICKFS_API_KEY
    API_KEY = QUICKFS_API_KEY
except ImportError:
    API_KEY = os.environ.get('QUICKFS_API_KEY')
    if not API_KEY:
        print("Error: QuickFS API key not found.")
        sys.exit(1)

def get_company_name_via_api(ticker: str) -> Optional[str]:
    """
    Get company name using QuickFS API get_data_full method
    This is much more reliable than web scraping
    """
    try:
        from quickfs import QuickFS

        client = QuickFS(API_KEY)

        # Use the same format as our existing code
        if ':' not in ticker:
            formatted_ticker = f"{ticker}:US"
        else:
            formatted_ticker = ticker

        # Get full data which includes company name in metadata
        data = client.get_data_full(formatted_ticker)

        if data and 'metadata' in data:
            metadata = data['metadata']
            company_name = metadata.get('name')
            if company_name:
                return company_name.strip()

        return None

    except Exception as e:
        print(f"API error for {ticker}: {e}")
        return None

def test_api_scraper():
    """Test the API-based scraper"""
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']

    print("Testing QuickFS API Company Name Extraction")
    print("=" * 50)

    for ticker in test_tickers:
        print(f"\nTesting {ticker}...")
        company_name = get_company_name_via_api(ticker)

        if company_name:
            print(f"  SUCCESS: {ticker} -> {company_name}")
        else:
            print(f"  FAILED: {ticker} -> No company name found")

        # Small delay to be respectful
        time.sleep(1)

    print("\n" + "=" * 50)
    print("API test complete!")

if __name__ == '__main__':
    test_api_scraper()