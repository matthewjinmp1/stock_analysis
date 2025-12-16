#!/usr/bin/env python3
"""
Simple Flask web application to search for stock data by ticker symbol.
Uses unified cache database to store and retrieve all UI data.
"""
from flask import Flask, render_template, jsonify, request
import json
import os
import sys
import sqlite3

# Ensure project root is on path so we can import modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import unified cache database manager
from web_app.ui_cache_db import get_complete_data, init_database, get_cached_data

# Import company name lookup function
from src.scrapers.glassdoor_scraper import get_company_name_from_ticker

# Import score calculator for weights and definitions
from web_app.score_calculator import SCORE_WEIGHTS, SCORE_DEFINITIONS

app = Flask(__name__)

# Initialize database on startup
init_database()

def find_best_match(query: str) -> tuple:
    """Find exact ticker match for a query.
    
    Args:
        query: User search query (must be exact ticker symbol)
        
    Returns:
        tuple: (ticker, match_type) where match_type is 'ticker' or None if not found
    """
    query_upper = query.strip().upper()
    
    # Get all cached data to search through
    cache_db_path = os.path.join(os.path.dirname(__file__), 'data', 'ui_cache.db')
    if not os.path.exists(cache_db_path):
        return None, None
    
    try:
        conn = sqlite3.connect(cache_db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT ticker FROM ui_cache WHERE ticker = ?', (query_upper,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0], 'ticker'
        else:
            return None, None
    except Exception as e:
        print(f"Error querying cache for matching: {e}")
        return None, None

@app.route('/')
def index():
    """Serve the main search page."""
    return render_template('index.html')

@app.route('/api/search/<query>')
def search_ticker(query):
    """API endpoint to search for stock data by exact ticker symbol.
    
    Uses unified cache database. If data is missing, fetches and caches it.
    Only exact ticker matches are supported for speed and unambiguity.
    """
    # Find best matching ticker (handles both ticker and company name queries)
    ticker, match_type = find_best_match(query)
    
    if not ticker:
        return jsonify({
            'success': False,
            'query': query,
            'message': f'No exact ticker match found for "{query}". Please enter an exact ticker symbol (e.g., AAPL).'
        }), 404
    
    try:
        # Get complete data from unified cache (fetches if missing)
        data = get_complete_data(ticker)
        
        if not data:
            return jsonify({
                'success': False,
                'query': query,
                'message': f'Could not fetch data for "{ticker}". Please check that the ticker is valid.'
            }), 404
        
        # Build response data from unified cache
        response_data = {
            'ticker': ticker,
            'company_name': data.get('company_name'),
            'short_float': data.get('short_float'),
            'moat_score': data.get('moat_score'),
            'total_score_percentage': data.get('total_score_percentage'),
            'total_score_percentile_rank': data.get('total_score_percentile_rank'),
        }
        
        return jsonify({
            'success': True,
            'ticker': ticker,
            'query': query,
            'match_type': match_type,
            'data': response_data
        })
    except Exception as e:
        # If fetching fails, return error
        print(f"Error fetching data for {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'query': query,
            'message': f'Error fetching data for "{ticker}": {str(e)}'
        }), 500

@app.route('/metrics/<ticker>')
def metrics_page(ticker):
    """Display all metric scores for a ticker."""
    ticker = ticker.strip().upper()
    
    # Get complete data from unified cache
    data = get_complete_data(ticker)
    
    if not data:
        return render_template('metrics.html', 
                             ticker=ticker,
                             company_name=None,
                             error="No data found for this ticker.")
    
    # Extract score data from unified cache
    score_data = {}
    for key in data.keys():
        # Include all metric columns and calculated scores
        if key not in ['ticker', 'company_name', 'last_updated', 'short_float', 
                       'short_interest_scraped_at']:
            score_data[key] = data[key]
    
    if not score_data or not any(score_data.values()):
        return render_template('metrics.html', 
                             ticker=ticker,
                             company_name=data.get('company_name'),
                             error="No score data found for this ticker.")
    
    # Calculate contribution of each metric to total score
    metrics_detail = []
    total_score = 0.0
    max_score = sum(SCORE_WEIGHTS.get(key, 1.0) for key in SCORE_DEFINITIONS) * 10
    
    for score_key in SCORE_DEFINITIONS:
        score_def = SCORE_DEFINITIONS[score_key]
        weight = SCORE_WEIGHTS.get(score_key, 1.0)
        
        try:
            score_value_str = score_data.get(score_key)
            if score_value_str is None:
                continue
                
            score_value = float(score_value_str)
            
            # For reverse scores, invert to get "goodness" value
            if score_def['is_reverse']:
                adjusted_value = 10 - score_value
                contribution = adjusted_value * weight
            else:
                adjusted_value = score_value
                contribution = score_value * weight
            
            total_score += contribution
            
            # Format metric name for display
            display_name = score_key.replace('_', ' ').title()
            
            metrics_detail.append({
                'key': score_key,
                'name': display_name,
                'raw_score': score_value,
                'adjusted_score': adjusted_value,
                'weight': weight,
                'contribution': contribution,
                'is_reverse': score_def['is_reverse'],
                'percentage': (contribution / max_score) * 100 if max_score > 0 else 0
            })
        except (ValueError, TypeError):
            continue
    
    # Sort by contribution (descending)
    metrics_detail.sort(key=lambda x: x['contribution'], reverse=True)
    
    # Get total score percentage
    total_score_percentage = score_data.get('total_score_percentage')
    total_score_percentile_rank = score_data.get('total_score_percentile_rank')
    
    return render_template('metrics.html',
                         ticker=ticker,
                         company_name=data.get('company_name'),
                         metrics=metrics_detail,
                         total_score_percentage=total_score_percentage,
                         total_score_percentile_rank=total_score_percentile_rank,
                         max_score=max_score)

@app.route('/api/list')
def list_all():
    """API endpoint to list all available tickers in the unified cache."""
    cache_db_path = os.path.join(os.path.dirname(__file__), 'data', 'ui_cache.db')
    if not os.path.exists(cache_db_path):
        return jsonify({
            'success': True,
            'count': 0,
            'tickers': []
        })
    
    try:
        conn = sqlite3.connect(cache_db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT ticker FROM ui_cache ORDER BY ticker')
        rows = cursor.fetchall()
        conn.close()
        tickers = [row[0] for row in rows]
        return jsonify({
            'success': True,
            'count': len(tickers),
            'tickers': tickers
        })
    except Exception as e:
        print(f"Error listing tickers: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

