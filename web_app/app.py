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
    
    # First, try exact ticker match
    if query_upper in companies:
        return query_upper, companies[query_upper], 1.0
    
    # Try case-insensitive ticker match
    for ticker in companies:
        if ticker.upper() == query_upper:
            return ticker, companies[ticker], 1.0
    
    # If query looks like a ticker (short, uppercase, alphanumeric), search only tickers
    if len(query) <= 5 and query.replace(' ', '').isalnum():
        best_ticker = None
        best_score = 0.0
        for ticker in companies:
            score = similarity(query_upper, ticker.upper())
            if score > best_score:
                best_score = score
                best_ticker = ticker
        if best_score > 0.5:  # Threshold for ticker matching
            return best_ticker, companies[best_ticker], best_score
    
    # Search by company name - prioritize exact word matches
    exact_word_matches = []
    substring_matches = []
    fuzzy_matches = []
    
    query_words = query_upper.split()
    import re
    
    for ticker, data in companies.items():
        company_name = data.get('company_name', '')
        company_name_upper = company_name.upper()
        
        # Normalize company name: split by word boundaries (spaces, punctuation)
        # Split by spaces, commas, periods, hyphens, etc. to get individual words
        company_words = re.split(r'[\s,\-\.&()]+', company_name_upper)
        # Remove empty strings and normalize
        company_words = [word.strip() for word in company_words if word.strip()]
        
        # Check for exact word matches (highest priority)
        # A word matches ONLY if it appears as a complete word in the company name
        exact_word_count = 0
        for query_word in query_words:
            # Check if query_word appears as a complete word (exact match, not substring)
            for company_word in company_words:
                if company_word == query_word:
                    exact_word_count += 1
                    break  # Found match for this query word, move to next
        
        # Only consider it an exact word match if ALL query words match
        if exact_word_count == len(query_words) and len(query_words) > 0:
            # Perfect match - all words found as complete words
            score = 1.0
            exact_word_matches.append((ticker, data, score, exact_word_count))
        # Only do substring/fuzzy matching if NO exact word matches were found
        elif exact_word_count == 0:
            # Check if query is contained in company name as substring (word boundary aware)
            # Use word boundaries to avoid matching "apple" in "applovin"
            if re.search(r'\b' + re.escape(query_upper) + r'\b', company_name_upper):
                score = 0.85  # High score for word-boundary substring match
                substring_matches.append((ticker, data, score))
            # Check if company name starts with query (as whole word)
            elif company_name_upper.startswith(query_upper + ' ') or company_name_upper == query_upper:
                score = 0.80
                substring_matches.append((ticker, data, score))
            else:
                # Calculate fuzzy similarity
                score = similarity(query, company_name)
                if score > 0.3:
                    fuzzy_matches.append((ticker, data, score))
    
    # Return best match in priority order: exact words > substring > fuzzy
    if exact_word_matches:
        # Sort by number of exact word matches, then by score
        exact_word_matches.sort(key=lambda x: (x[3], x[2]), reverse=True)
        best = exact_word_matches[0]
        return best[0], best[1], best[2]
    
    if substring_matches:
        substring_matches.sort(key=lambda x: x[2], reverse=True)
        best = substring_matches[0]
        return best[0], best[1], best[2]
    
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

