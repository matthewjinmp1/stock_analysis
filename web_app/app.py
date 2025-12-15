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
    query = query.strip().upper()
    
    # First, try exact ticker match
    if query in companies:
        return query, companies[query], 1.0
    
    # Try case-insensitive ticker match
    for ticker in companies:
        if ticker.upper() == query:
            return ticker, companies[ticker], 1.0
    
    # If query looks like a ticker (short, uppercase, alphanumeric), search only tickers
    if len(query) <= 5 and query.isalnum():
        best_ticker = None
        best_score = 0.0
        for ticker in companies:
            score = similarity(query, ticker)
            if score > best_score:
                best_score = score
                best_ticker = ticker
        if best_score > 0.5:  # Threshold for ticker matching
            return best_ticker, companies[best_ticker], best_score
    
    # Otherwise, search by company name
    best_ticker = None
    best_score = 0.0
    best_company_name = None
    
    for ticker, data in companies.items():
        company_name = data.get('company_name', '').upper()
        query_upper = query.upper()
        
        # Check if query is contained in company name or vice versa
        if query_upper in company_name or company_name in query_upper:
            score = 0.9  # High score for substring match
        else:
            # Calculate similarity
            score = similarity(query, company_name)
        
        if score > best_score:
            best_score = score
            best_ticker = ticker
            best_company_name = company_name
    
    if best_score > 0.3:  # Threshold for company name matching
        return best_ticker, companies[best_ticker], best_score
    
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

