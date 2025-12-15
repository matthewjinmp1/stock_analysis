#!/usr/bin/env python3
"""
Simple Flask web application to search for short interest by ticker symbol.
"""
from flask import Flask, render_template, jsonify, request
import json
import os
import sys

# Ensure project root is on path so we can import modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import short interest fetching function
from web_app.get_short_interest import get_short_interest_for_ticker

app = Flask(__name__)

# Path to the short interest cache file
SHORT_INTEREST_FILE = os.path.join(os.path.dirname(__file__), 'data', 'short_interest_cache.json')
# Path to the scores file
SCORES_FILE = os.path.join(os.path.dirname(__file__), 'data', 'scores.json')

def load_scores_data():
    """Load scores data from JSON file.

    Returns:
        dict mapping ticker -> score info dict
    """
    try:
        with open(SCORES_FILE, 'r') as f:
            data = json.load(f)
            # File format: {"companies": {"AAPL": {...}, "MSFT": {...}, ...}}
            return data.get('companies', {})
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def load_short_interest_data():
    """Load short interest data from cache JSON file.

    Returns:
        dict mapping ticker -> short interest info dict
    """
    try:
        with open(SHORT_INTEREST_FILE, 'r') as f:
            data = json.load(f)
            # Cache file format: {"AAPL": {...}, "MSFT": {...}, ...}
            # Already a flat dict, so return it directly
            return data
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

@app.route('/')
def index():
    """Serve the main search page."""
    return render_template('index.html')

@app.route('/api/search/<query>')
def search_ticker(query):
    """API endpoint to search for short interest by ticker symbol.
    
    get_short_interest_for_ticker handles all caching and date checking logic.
    Also includes score data from scores.json if available.
    """
    ticker = query.strip().upper()
    
    # Load scores data
    scores = load_scores_data()
    score_data = scores.get(ticker, {})
    
    try:
        # get_short_interest_for_ticker handles cache checking and refreshing
        si_result = get_short_interest_for_ticker(ticker)
        
        if si_result:
            # Build response data
            response_data = {
                'ticker': ticker,
                'short_float': si_result.get('short_float'),
            }
            
            # Add score if available
            if score_data:
                response_data['moat_score'] = score_data.get('moat_score')
            
            return jsonify({
                'success': True,
                'ticker': ticker,
                'query': query,
                'data': response_data
            })
        else:
            return jsonify({
                'success': False,
                'query': query,
                'message': f'No short interest data found for "{ticker}". Please check that the ticker is valid.'
            }), 404
    except Exception as e:
        # If fetching fails, return error
        print(f"Warning: Could not fetch short interest for {ticker}: {e}")
        return jsonify({
            'success': False,
            'query': query,
            'message': f'Could not fetch short interest for "{ticker}". Please check that the ticker is valid.'
        }), 404

@app.route('/api/list')
def list_all():
    """API endpoint to list all available tickers with cached short interest."""
    short_interest = load_short_interest_data()
    tickers = sorted(short_interest.keys())
    return jsonify({
        'success': True,
        'count': len(tickers),
        'tickers': tickers
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

