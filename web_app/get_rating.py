#!/usr/bin/env python3
"""
Simple script to get Glassdoor rating for a single company by ticker symbol.
Uses Grok API directly (via xAI) to fetch fresh Glassdoor ratings.

Usage: python get_rating.py AAPL
       python get_rating.py MSFT
       python get_rating.py  (will prompt for ticker)
"""
import sys
import os
import json

# Add parent directory to path to import scraper
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.scrapers.glassdoor_scraper import get_glassdoor_rating, display_snippet

def check_api_availability():
    """Check if Grok API (direct xAI) is available."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from src.clients.grok_client import GrokClient
        from config import XAI_API_KEY
        
        if not XAI_API_KEY:
            print("Error: XAI_API_KEY not found in config.py")
            print("Please make sure your xAI Grok API key is configured.")
            print("Get your API key from: https://console.x.ai/")
            return False
        return True
    except ImportError:
        print("Error: GrokClient not available. Make sure dependencies are installed.")
        return False
    except Exception as e:
        print(f"Error checking API availability: {e}")
        return False

def main():
    """Get and display Glassdoor rating for a ticker using Grok API directly."""
    # Check API availability first
    if not check_api_availability():
        sys.exit(1)
    
    if len(sys.argv) < 2:
        ticker = input("Enter ticker symbol: ").strip().upper()
        if not ticker:
            print("Error: No ticker provided")
            sys.exit(1)
    else:
        ticker = sys.argv[1].strip().upper()
    
    print(f"Fetching Glassdoor rating for {ticker} using Grok API directly (xAI)...")
    print("=" * 80)
    
    # Use direct Grok API (not OpenRouter)
    result = get_glassdoor_rating(ticker, silent=False, use_direct_grok=True)
    
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

