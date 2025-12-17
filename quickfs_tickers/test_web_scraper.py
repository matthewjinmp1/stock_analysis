#!/usr/bin/env python3
"""
Test the QuickFS web scraper with a few known tickers
"""

import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from quickfs_tickers.quickfs_web_scraper import QuickFSWebScraper

def test_web_scraper():
    """Test the web scraper with known tickers"""
    scraper = QuickFSWebScraper(delay=3.0)  # Longer delay for testing

    # Test with known tickers from different exchanges
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'BHP']

    print("Testing QuickFS Web Scraper")
    print("=" * 50)
    print("WARNING: This scrapes the QuickFS website - use responsibly!")

    successful = 0
    for ticker in test_tickers:
        print(f"\nTesting {ticker}...")
        company_name = scraper.scrape_company_name(ticker)

        if company_name:
            print(f"  SUCCESS: {ticker} -> {company_name}")
            successful += 1
        else:
            print(f"  FAILED: {ticker} -> No company name found")

    print(f"\n{'='*50}")
    print(f"Results: {successful}/{len(test_tickers)} successful")
    if successful > 0:
        print("✅ Web scraping appears to work!")
        print("Run: python quickfs_tickers/quickfs_web_scraper.py --limit 10")
    else:
        print("❌ Web scraping may not be working - check QuickFS website structure")
    print(f"{'='*50}")

if __name__ == '__main__':
    test_web_scraper()