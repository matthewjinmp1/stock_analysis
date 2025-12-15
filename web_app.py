#!/usr/bin/env python3
"""
Simple Flask web application to search for Glassdoor ratings by ticker symbol.
"""
from flask import Flask, render_template, jsonify, request
import json
import os

app = Flask(__name__)

# Path to the Glassdoor data file
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

@app.route('/')
def index():
    """Serve the main search page."""
    return render_template('index.html')

@app.route('/api/search/<ticker>')
def search_ticker(ticker):
    """API endpoint to search for a ticker's Glassdoor rating."""
    ticker = ticker.upper().strip()
    companies = load_glassdoor_data()
    
    if ticker in companies:
        company_data = companies[ticker]
        return jsonify({
            'success': True,
            'ticker': ticker,
            'data': company_data
        })
    else:
        return jsonify({
            'success': False,
            'ticker': ticker,
            'message': f'No Glassdoor rating found for ticker {ticker}'
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

