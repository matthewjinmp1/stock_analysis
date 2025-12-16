#!/usr/bin/env python3
"""
Simple Flask web application to search for short interest by ticker symbol.
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

# Import short interest fetching function
from web_app.get_short_interest import get_short_interest_for_ticker

# Import company name lookup function
from src.scrapers.glassdoor_scraper import get_company_name_from_ticker

# Import score calculator for weights and definitions
from web_app.score_calculator import SCORE_WEIGHTS, SCORE_DEFINITIONS

app = Flask(__name__)

# Path to the short interest cache file
SHORT_INTEREST_FILE = os.path.join(os.path.dirname(__file__), 'data', 'short_interest_cache.json')
# Path to the scores database
SCORES_DB = os.path.join(os.path.dirname(__file__), 'data', 'scores.db')

def get_score_for_ticker(ticker: str):
    """Get score data for a ticker from the database.

    Args:
        ticker: Stock ticker symbol (uppercase)
        
    Returns:
        dict: Score data for the ticker, or None if not found
    """
    if not os.path.exists(SCORES_DB):
        return None
    
    try:
        conn = sqlite3.connect(SCORES_DB)
        cursor = conn.cursor()
        
        # Get all columns (ticker + all metrics + calculated scores)
        cursor.execute('SELECT * FROM scores WHERE ticker = ?', (ticker.upper(),))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # Get column names
        column_names = [description[0] for description in cursor.description]
        
        # Build dictionary from row data
        score_data = {}
        for i, value in enumerate(row):
            if column_names[i] != 'ticker' and value is not None:
                score_data[column_names[i]] = value
        
        conn.close()
        return score_data if score_data else None
    except Exception as e:
        print(f"Error querying scores database: {e}")
        return None

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
    Also includes score data from scores.db if available.
    """
    ticker = query.strip().upper()
    
    # Get company name from ticker
    company_name = get_company_name_from_ticker(ticker)
    
    # Get score data from database
    score_data = get_score_for_ticker(ticker)
    
    try:
        # get_short_interest_for_ticker handles cache checking and refreshing
        si_result = get_short_interest_for_ticker(ticker)
        
        if si_result:
            # Build response data
            response_data = {
                'ticker': ticker,
                'company_name': company_name,
                'short_float': si_result.get('short_float'),
            }
            
            # Add score data if available
            if score_data:
                response_data['moat_score'] = score_data.get('moat_score')
                
                # Get pre-calculated total score percentage and percentile rank from database
                response_data['total_score_percentage'] = score_data.get('total_score_percentage')
                response_data['total_score_percentile_rank'] = score_data.get('total_score_percentile_rank')
            
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

@app.route('/metrics/<ticker>')
def metrics_page(ticker):
    """Display all metric scores for a ticker."""
    ticker = ticker.strip().upper()
    
    # Get company name
    company_name = get_company_name_from_ticker(ticker)
    
    # Get all score data from database
    score_data = get_score_for_ticker(ticker)
    
    if not score_data:
        return render_template('metrics.html', 
                             ticker=ticker,
                             company_name=company_name,
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
                         company_name=company_name,
                         metrics=metrics_detail,
                         total_score_percentage=total_score_percentage,
                         total_score_percentile_rank=total_score_percentile_rank,
                         max_score=max_score)

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

