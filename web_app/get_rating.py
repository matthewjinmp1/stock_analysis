#!/usr/bin/env python3
"""
Simple script to get Glassdoor rating for a single company by ticker symbol.
Usage: python get_rating.py AAPL
       python get_rating.py MSFT
"""
import sys
import os
import json

# Add parent directory to path to import scraper
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.scrapers.glassdoor_scraper import get_glassdoor_rating, display_snippet

def main():
    """Get and display Glassdoor rating for a ticker."""
    if len(sys.argv) < 2:
        ticker = input("Enter ticker symbol: ").strip().upper()
        if not ticker:
            print("Error: No ticker provided")
            sys.exit(1)
    else:
        ticker = sys.argv[1].strip().upper()
    
    print(f"Fetching Glassdoor rating for {ticker}...")
    print("=" * 80)
    
    result = get_glassdoor_rating(ticker, silent=False)
    
    if result:
        print("\n" + "=" * 80)
        print("RESULT:")
        print("=" * 80)
        display_snippet(result)
        
        # Also print as JSON for easy parsing
        print("\n" + "=" * 80)
        print("JSON OUTPUT:")
        print("=" * 80)
        print(json.dumps({
            'ticker': ticker,
            'company_name': result.get('company_name'),
            'rating': result.get('rating'),
            'num_reviews': result.get('num_reviews'),
            'snippet': result.get('snippet'),
            'url': result.get('url')
        }, indent=2))
    else:
        print(f"\nError: Could not fetch Glassdoor rating for {ticker}")
        sys.exit(1)

if __name__ == '__main__':
    main()

