#!/usr/bin/env python3
"""
Test the QuickFS company name scraper with a few known tickers
"""

import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from quickfs_tickers.scrape_quickfs_company_names import QuickFSCompanyScraper

def test_scraper():
    """Test the scraper with known tickers"""
    scraper = QuickFSCompanyScraper(delay=2.0)  # Longer delay for testing

    # Test with well-known tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']

    print("Testing QuickFS Company Name Scraper")
    print("=" * 50)

    for ticker in test_tickers:
        print(f"\nTesting {ticker}...")
        company_name = scraper.scrape_company_name(ticker)

        if company_name:
            print(f"  SUCCESS {ticker}: {company_name}")

            # Test database update (without actually updating)
            print(f"  UPDATE: Would set {ticker} -> {company_name}")
        else:
            print(f"  FAILED {ticker}: Could not extract company name")

    print("\n" + "=" * 50)
    print("Test complete. If successful, the scraper logic works!")
    print("Run the full scraper with: python scrape_quickfs_company_names.py --limit 10")

if __name__ == '__main__':
    test_scraper()