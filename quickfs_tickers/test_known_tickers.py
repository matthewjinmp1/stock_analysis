#!/usr/bin/env python3
"""
Test populating company names for known valid tickers
"""

import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from quickfs_tickers.populate_company_names import QuickFSCompanyNamePopulator

def test_known_tickers():
    """Test with known valid tickers"""
    populator = QuickFSCompanyNamePopulator(delay=1.0)

    # Test with known valid tickers from different exchanges
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'BHP:AU', 'CBA:AU']

    print("Testing company name population for known tickers")
    print("=" * 60)

    successful = 0
    for ticker in test_tickers:
        print(f"\nProcessing {ticker}...")

        company_name = populator.get_company_name(ticker)

        if company_name:
            if populator.update_company_name(ticker, company_name):
                print(f"  SUCCESS: {ticker} -> {company_name}")
                successful += 1
            else:
                print(f"  FAILED: Could not update database for {ticker}")
        else:
            print(f"  FAILED: No company name found for {ticker}")

    print(f"\n{'='*60}")
    print(f"Results: {successful}/{len(test_tickers)} successful")
    print(f"{'='*60}")

if __name__ == '__main__':
    test_known_tickers()