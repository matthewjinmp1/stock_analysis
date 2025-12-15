#!/usr/bin/env python3
"""
Simple Flask web application to search for short interest by ticker symbol.
"""
from flask import Flask, render_template, jsonify, request
import json
import os
import sys
from datetime import datetime, date

# Ensure project root is on path so we can import modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import short interest fetching function
from web_app.get_short_interest import get_short_interest_for_ticker

app = Flask(__name__)

# Path to the short interest cache file
SHORT_INTEREST_FILE = os.path.join(os.path.dirname(__file__), 'data', 'short_interest_cache.json')

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
    
    If short interest is not in cache or the cached date is not today, fetches it and caches it.
    """
    ticker = query.strip().upper()
    short_interest = load_short_interest_data()
    
    si = short_interest.get(ticker, {})
    should_refetch = False
    
    # Check if we need to refetch (not in cache or date is not today)
    if not si:
        should_refetch = True
    else:
        # Check if the scraped_at date is today
        scraped_at_str = si.get('scraped_at')
        if scraped_at_str:
            try:
                # Parse ISO format date: "2025-12-15T14:04:00.421697"
                scraped_at = datetime.fromisoformat(scraped_at_str).date()
                today = date.today()
                if scraped_at != today:
                    should_refetch = True
            except (ValueError, AttributeError):
                # If date parsing fails, refetch to be safe
                should_refetch = True
        else:
            # No date, refetch
            should_refetch = True
    
    # If not in cache or date is not today, fetch and cache it
    if should_refetch:
        try:
            si_result = get_short_interest_for_ticker(ticker)
            if si_result:
                # Reload cache to get the newly cached result
                short_interest = load_short_interest_data()
                si = short_interest.get(ticker, {})
        except Exception as e:
            # If fetching fails, return error
            print(f"Warning: Could not fetch short interest for {ticker}: {e}")
            return jsonify({
                'success': False,
                'query': query,
                'message': f'Could not fetch short interest for "{ticker}". Please check that the ticker is valid.'
            }), 404
    
    if si:
        return jsonify({
            'success': True,
            'ticker': ticker,
            'query': query,
            'data': {
                'ticker': ticker,
                'short_float': si.get('short_float'),
            }
        })
    else:
        return jsonify({
            'success': False,
            'query': query,
            'message': f'No short interest data found for "{ticker}". Please check that the ticker is valid.'
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

