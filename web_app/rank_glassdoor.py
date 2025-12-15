#!/usr/bin/env python3
"""
Script to rank companies by their Glassdoor ratings and save to a JSON file.
"""
import json
import os

# Path to the Glassdoor data file
GLASSDOOR_DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'glassdoor.json')
RANKED_OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'data', 'glassdoor_ranked.json')

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

def rank_companies(companies):
    """Rank companies by Glassdoor rating."""
    ranked = []
    
    for ticker, data in companies.items():
        rating = data.get('rating')
        if rating is not None:
            ranked.append({
                'ticker': ticker,
                'company_name': data.get('company_name', ticker),
                'rating': rating,
                'num_reviews': data.get('num_reviews', 0),
                'snippet': data.get('snippet', ''),
                'url': data.get('url', ''),
                'fetched_at': data.get('fetched_at', '')
            })
    
    # Sort by rating (highest first), then by number of reviews (most reviews first)
    ranked.sort(key=lambda x: (x['rating'], x['num_reviews']), reverse=True)
    
    # Add rank number
    for i, company in enumerate(ranked, 1):
        company['rank'] = i
    
    return ranked

def main():
    """Main function to rank and save Glassdoor ratings."""
    print("Loading Glassdoor data...")
    companies = load_glassdoor_data()
    
    if not companies:
        print("No companies found in data file.")
        return
    
    print(f"Found {len(companies)} companies")
    print("Ranking companies by Glassdoor rating...")
    
    ranked = rank_companies(companies)
    
    # Create output structure
    output = {
        'total_companies': len(ranked),
        'ranked_companies': ranked,
        'top_10': ranked[:10],
        'bottom_10': ranked[-10:] if len(ranked) >= 10 else ranked
    }
    
    # Save to file
    print(f"Saving ranked data to {RANKED_OUTPUT_FILE}...")
    with open(RANKED_OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSuccessfully ranked {len(ranked)} companies")
    print(f"\nTop 10 Companies by Glassdoor Rating:")
    print("=" * 80)
    print(f"{'Rank':<6} {'Ticker':<8} {'Company':<35} {'Rating':<8} {'Reviews':<12}")
    print("=" * 80)
    for company in ranked[:10]:
        print(f"{company['rank']:<6} {company['ticker']:<8} {company['company_name'][:35]:<35} {company['rating']:<8.1f} {company['num_reviews']:<12,}")
    
    print(f"\nBottom 10 Companies by Glassdoor Rating:")
    print("=" * 80)
    print(f"{'Rank':<6} {'Ticker':<8} {'Company':<35} {'Rating':<8} {'Reviews':<12}")
    print("=" * 80)
    for company in ranked[-10:]:
        print(f"{company['rank']:<6} {company['ticker']:<8} {company['company_name'][:35]:<35} {company['rating']:<8.1f} {company['num_reviews']:<12,}")

if __name__ == '__main__':
    main()

