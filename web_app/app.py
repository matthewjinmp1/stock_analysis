#!/usr/bin/env python3
"""
Simple Flask web application to search for Glassdoor ratings by ticker symbol or company name.
"""
from flask import Flask, render_template, jsonify, request
import json
import os
from difflib import SequenceMatcher

app = Flask(__name__)

# Path to the Glassdoor data file (relative to this script)
GLASSDOOR_DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'glassdoor.json')

def load_glassdoor_data():
    """Load Glassdoor data from JSON file."""
    try:
        with open(GLASSDOOR_DATA_FILE, 'r') as f:
            data = json.load(f)
            return data.get('companies', {})
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def similarity(a, b):
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_best_match(query, companies):
    """Find the best matching company by ticker or company name."""
    query = query.strip()
    query_upper = query.upper()
    import re
    
    # First, try exact ticker match (highest priority)
    if query_upper in companies:
        return query_upper, companies[query_upper], 1.0
    
    # Try case-insensitive ticker match
    for ticker in companies:
        if ticker.upper() == query_upper:
            return ticker, companies[ticker], 1.0
    
    # Search by company name - find exact word matches first
    exact_word_matches = []
    
    query_words = query_upper.split()
    
    for ticker, data in companies.items():
        company_name = data.get('company_name', '')
        company_name_upper = company_name.upper()
        
        # Split company name into words by spaces and punctuation
        company_words = re.split(r'[\s,\-\.&()]+', company_name_upper)
        company_words = [word.strip() for word in company_words if word.strip()]
        
        # Check if ALL query words appear as complete words in company name
        all_words_match = True
        for query_word in query_words:
            if query_word not in company_words:
                all_words_match = False
                break
        
        if all_words_match and len(query_words) > 0:
            # Perfect match - all words found as complete words
            exact_word_matches.append((ticker, data, 1.0, len(query_words)))
    
    # If we found exact word matches, return the best one
    if exact_word_matches:
        # Sort by number of words matched (more is better)
        exact_word_matches.sort(key=lambda x: x[3], reverse=True)
        best = exact_word_matches[0]
        return best[0], best[1], best[2]
    
    # No exact word matches - fall back to other matching methods
    # Only for short queries that look like tickers, try ticker fuzzy match
    if len(query) <= 4 and query_upper.isalnum():
        best_ticker = None
        best_score = 0.0
        for ticker in companies:
            score = similarity(query_upper, ticker.upper())
            if score > best_score:
                best_score = score
                best_ticker = ticker
        if best_score > 0.6:  # Higher threshold for ticker matching
            return best_ticker, companies[best_ticker], best_score
    
    # Try fuzzy company name matching as last resort
    fuzzy_matches = []
    for ticker, data in companies.items():
        company_name = data.get('company_name', '')
        score = similarity(query, company_name)
        if score > 0.4:  # Higher threshold
            fuzzy_matches.append((ticker, data, score))
    
    if fuzzy_matches:
        fuzzy_matches.sort(key=lambda x: x[2], reverse=True)
        best = fuzzy_matches[0]
        return best[0], best[1], best[2]
    
    return None, None, 0.0

@app.route('/')
def index():
    """Serve the main search page."""
    return render_template('index.html')

@app.route('/api/search/<query>')
def search_ticker(query):
    """API endpoint to search for a ticker or company name's Glassdoor rating."""
    companies = load_glassdoor_data()
    
    best_ticker, company_data, match_score = find_best_match(query, companies)
    
    if best_ticker and company_data:
        return jsonify({
            'success': True,
            'ticker': best_ticker,
            'query': query,
            'match_score': match_score,
            'data': company_data
        })
    else:
        return jsonify({
            'success': False,
            'query': query,
            'message': f'No matching company found for "{query}". Try a ticker symbol (e.g., AAPL) or company name (e.g., Apple).'
        }), 404

@app.route('/api/list')
def list_all():
    """API endpoint to list all available tickers."""
    companies = load_glassdoor_data()
    tickers = sorted(companies.keys())
    return jsonify({
        'success': True,
        'count': len(tickers),
        'tickers': tickers
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

