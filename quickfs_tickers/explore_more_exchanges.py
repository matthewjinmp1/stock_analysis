#!/usr/bin/env python3
"""
Explore additional exchanges and countries to find more QuickFS tickers
"""

import json
import os
import sys
from quickfs import QuickFS

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

def test_exchange_quickly(country, exchange):
    """Test an exchange quickly without verbose output"""
    try:
        client = QuickFS(API_KEY)
        companies = client.get_supported_companies(country=country, exchange=exchange)

        if companies and len(companies) > 0:
            # Extract tickers
            tickers = []
            if isinstance(companies, list):
                for company in companies[:10]:  # Just check first 10
                    if isinstance(company, str):
                        ticker = company.replace(f':{country}', '').strip()
                        if ticker:
                            tickers.append(ticker)

            return {
                "country": country,
                "exchange": exchange,
                "success": True,
                "ticker_count": len(companies),
                "sample_tickers": tickers[:3]
            }
        else:
            return {
                "country": country,
                "exchange": exchange,
                "success": False,
                "ticker_count": 0,
                "error": "No companies returned"
            }
    except Exception as e:
        return {
            "country": country,
            "exchange": exchange,
            "success": False,
            "ticker_count": 0,
            "error": str(e)
        }

def main():
    """Test many different exchanges and countries"""
    print("Exploring additional QuickFS exchanges...")

    # Known working exchanges from before
    known_working = [
        ('US', 'NYSE'),
        ('US', 'NASDAQ'),
        ('AU', 'ASX'),
        ('NZ', 'NZX')
    ]

    # Previously failing exchanges
    previously_failing = [
        ('CA', 'TSX'),
        ('LN', 'LSE'),
        ('MM', 'YSX')
    ]

    # Additional exchanges to try - more countries and exchanges
    additional_exchanges = [
        # European exchanges
        ('DE', 'XETRA'),  # Germany
        ('FR', 'PAR'),    # France
        ('NL', 'AMS'),    # Netherlands
        ('CH', 'SWX'),    # Switzerland
        ('SE', 'STO'),    # Sweden
        ('NO', 'OSL'),    # Norway
        ('DK', 'CPH'),    # Denmark
        ('FI', 'HEL'),    # Finland
        ('IT', 'MIL'),    # Italy
        ('ES', 'MAD'),    # Spain
        ('BE', 'BRU'),    # Belgium
        ('AT', 'VIE'),    # Austria
        ('PT', 'LIS'),    # Portugal
        ('IE', 'DUB'),    # Ireland
        ('GR', 'ATH'),    # Greece

        # Asian exchanges
        ('JP', 'TYO'),    # Japan
        ('HK', 'HKG'),    # Hong Kong
        ('SG', 'SES'),    # Singapore
        ('KR', 'KRX'),    # South Korea
        ('TW', 'TAI'),    # Taiwan
        ('TH', 'SET'),    # Thailand
        ('MY', 'KLSE'),   # Malaysia
        ('ID', 'IDX'),    # Indonesia
        ('PH', 'PSE'),    # Philippines
        ('VN', 'VSE'),    # Vietnam
        ('IN', 'NSE'),    # India NSE
        ('IN', 'BSE'),    # India BSE

        # Americas
        ('BR', 'SAO'),    # Brazil
        ('MX', 'MEX'),    # Mexico
        ('CL', 'SGO'),    # Chile
        ('AR', 'BUE'),    # Argentina
        ('CO', 'BOG'),    # Colombia
        ('PE', 'LIM'),    # Peru

        # Middle East/Africa
        ('IL', 'TLV'),    # Israel
        ('ZA', 'JSE'),    # South Africa
        ('AE', 'DFM'),    # Dubai
        ('TR', 'IST'),    # Turkey
        ('EG', 'EGX'),    # Egypt
        ('NG', 'NSE'),    # Nigeria

        # Try different exchange codes for previously failing ones
        ('CA', 'TSE'),    # Alternative code for Toronto
        ('GB', 'LSE'),    # Try GB instead of LN for London
        ('UK', 'LSE'),    # Try UK instead of LN
        ('MM', 'YSE'),    # Alternative code for Myanmar
    ]

    results = []

    # Test known working first
    print("\nTesting known working exchanges:")
    for country, exchange in known_working:
        result = test_exchange_quickly(country, exchange)
        results.append(result)
        status = "OK" if result["success"] else "FAIL"
        print(f"  {status} {country}/{exchange}: {result['ticker_count']} tickers")

    # Test previously failing
    print("\nTesting previously failing exchanges:")
    for country, exchange in previously_failing:
        result = test_exchange_quickly(country, exchange)
        results.append(result)
        status = "OK" if result["success"] else "FAIL"
        print(f"  {status} {country}/{exchange}: {result.get('error', 'Failed')}")

    # Test additional exchanges
    print("\nTesting additional exchanges:")
    working_additional = []
    for i, (country, exchange) in enumerate(additional_exchanges):
        result = test_exchange_quickly(country, exchange)
        results.append(result)
        if result["success"]:
            working_additional.append((country, exchange))
            status = "✓"
            print(f"  {status} {country}/{exchange}: {result['ticker_count']} tickers")
        else:
            status = "✗"
            if i % 10 == 0:  # Print every 10th failure to avoid spam
                print(f"  {status} {country}/{exchange}: Failed")

    # Summary
    successful = [r for r in results if r["success"]]
    total_tickers = sum(r["ticker_count"] for r in successful)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total exchanges tested: {len(results)}")
    print(f"Successful exchanges: {len(successful)}")
    print(f"Total tickers found: {total_tickers}")

    if working_additional:
        print(f"\nNew working exchanges found: {len(working_additional)}")
        for country, exchange in working_additional:
            result = next(r for r in results if r["country"] == country and r["exchange"] == exchange)
            print(f"  {country}/{exchange}: {result['ticker_count']} tickers")

    # Save results
    with open('quickfs_tickers/exchange_exploration_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\nDetailed results saved to exchange_exploration_results.json")
    print(f"Current total tickers: {total_tickers} (from {len(successful)} exchanges)")

if __name__ == '__main__':
    main()