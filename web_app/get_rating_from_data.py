#!/usr/bin/env python3
"""
Simple script to get Glassdoor rating for a single company from existing data.
This reads from the local glassdoor.json file (no API calls needed).
Usage: python get_rating_from_data.py AAPL
       python get_rating_from_data.py MSFT
       python get_rating_from_data.py "Apple"
"""
import sys
import os
import json

# Path to the Glassdoor data file
GLASSDOOR_DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'glassdoor.json')

def load_glassdoor_data():
    """Load Glassdoor data from JSON file."""
    try:
        with open(GLASSDOOR_DATA_FILE, 'r') as f:
            data = json.load(f)
            return data.get('companies', {})
    except FileNotFoundError:
        print(f"Error: {GLASSDOOR_DATA_FILE} not found")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {GLASSDOOR_DATA_FILE}")
        return {}

def find_company(query, companies):
    """Find company by ticker or name."""
    query_upper = query.strip().upper()
    
    # Try exact ticker match first
    if query_upper in companies:
        return query_upper, companies[query_upper]
    
    # Try case-insensitive ticker match
    for ticker in companies:
        if ticker.upper() == query_upper:
            return ticker, companies[ticker]
    
    # Try company name match (substring)
    for ticker, data in companies.items():
        company_name = data.get('company_name', '').upper()
        if query_upper in company_name or company_name.startswith(query_upper):
            return ticker, data
    
    return None, None

def main():
    """Get and display Glassdoor rating for a ticker or company name."""
    if len(sys.argv) < 2:
        print("Usage: python get_rating_from_data.py <TICKER_OR_NAME>")
        print("Example: python get_rating_from_data.py AAPL")
        print("Example: python get_rating_from_data.py Apple")
        sys.exit(1)
    
    query = sys.argv[1].strip()
    
    print(f"Looking up Glassdoor rating for '{query}'...")
    print("=" * 80)
    
    companies = load_glassdoor_data()
    
    if not companies:
        print("Error: No companies found in data file")
        sys.exit(1)
    
    ticker, data = find_company(query, companies)
    
    if not ticker or not data:
        print(f"Error: Could not find '{query}' in database")
        print(f"\nAvailable tickers: {', '.join(sorted(companies.keys())[:20])}...")
        sys.exit(1)
    
    rating = data.get('rating', 'N/A')
    num_reviews = data.get('num_reviews', 0)
    company_name = data.get('company_name', ticker)
    snippet = data.get('snippet', '')
    url = data.get('url', '')
    
    print(f"\nCompany: {company_name}")
    print(f"Ticker: {ticker}")
    print(f"Glassdoor Rating: {rating}/5.0")
    print(f"Number of Reviews: {num_reviews:,}" if num_reviews else "Number of Reviews: N/A")
    if snippet:
        print(f"Snippet: {snippet}")
    if url:
        print(f"URL: {url}")
    
    print("\n" + "=" * 80)
    print("JSON OUTPUT:")
    print("=" * 80)
    print(json.dumps({
        'ticker': ticker,
        'company_name': company_name,
        'rating': rating,
        'num_reviews': num_reviews,
        'snippet': snippet,
        'url': url
    }, indent=2))

if __name__ == '__main__':
    main()

