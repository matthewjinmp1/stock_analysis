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

# Import financial scores database
from web_app.financial_scores_db import get_financial_scores

# Import financial scorer metrics
from web_app.financial_scorer import METRICS

# Import watchlist database
from web_app.watchlist_db import (
    add_to_watchlist, remove_from_watchlist, 
    is_in_watchlist, get_watchlist, init_watchlist_database
)

# Import score calculator for weights and definitions
from web_app.score_calculator import SCORE_WEIGHTS, SCORE_DEFINITIONS

# Display names for metrics (explicit, no "Score" suffix)
METRIC_DISPLAY_NAMES = {
    'moat_score': 'Economic Moat',
    'barriers_score': 'Barriers to Entry',
    'disruption_risk': 'Disruption Risk',
    'switching_cost': 'Switching Cost',
    'brand_strength': 'Brand Strength',
    'competition_intensity': 'Competition Intensity',
    'network_effect': 'Network Effect',
    'product_differentiation': 'Product Differentiation',
    'innovativeness_score': 'Innovativeness',
    'growth_opportunity': 'Growth Opportunity',
    'riskiness_score': 'Business Risk',
    'pricing_power': 'Pricing Power',
    'ambition_score': 'Ambition',
    'bargaining_power_of_customers': 'Customer Bargaining Power',
    'bargaining_power_of_suppliers': 'Supplier Bargaining Power',
    'product_quality_score': 'Product Quality',
    'culture_employee_satisfaction_score': 'Employee Satisfaction',
    'trailblazer_score': 'Market Leadership',
    'management_quality_score': 'Management Quality',
    'ai_knowledge_score': 'AI Scoring Confidence',
    'size_well_known_score': 'Size',
    'ethical_healthy_environmental_score': 'Ethical, Healthy, Environmental',
    'long_term_orientation_score': 'Long Term Focus',
}

app = Flask(__name__)

# Initialize databases on startup
init_database()
init_watchlist_database()

def find_best_match(query: str) -> tuple:
    """Find exact ticker match for a query.
    
    First checks cache for perfect match. If not in cache, returns the ticker
    anyway so it can be fetched (company name will be looked up from ticker files).
    
    Args:
        query: User search query (must be exact ticker symbol)
        
    Returns:
        tuple: (ticker, match_type) where match_type is 'ticker' or 'ticker_not_cached'
    """
    query_upper = query.strip().upper()
    
    # First, check cache for perfect match
    cache_db_path = os.path.join(os.path.dirname(__file__), 'data', 'ui_cache.db')
    if os.path.exists(cache_db_path):
        try:
            conn = sqlite3.connect(cache_db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT ticker FROM ui_cache WHERE ticker = ?', (query_upper,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0], 'ticker'
        except Exception as e:
            print(f"Error querying cache for matching: {e}")
    
    # If not in cache, still return the ticker so we can fetch it
    # The company name will be looked up from ticker files during fetch
    return query_upper, 'ticker_not_cached'

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
    # Find ticker (checks cache first, but returns ticker even if not cached)
    ticker, match_type = find_best_match(query)
    
    if not ticker:
        return jsonify({
            'success': False,
            'query': query,
            'message': f'Invalid ticker format for "{query}". Please enter a valid ticker symbol (e.g., AAPL).'
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
        
        # Get financial scores
        financial_scores = get_financial_scores(ticker)
        
        # Build response data from unified cache
        response_data = {
            'ticker': ticker,
            'company_name': data.get('company_name'),
            'short_float': data.get('short_float'),
            'total_score_percentage': data.get('total_score_percentage'),
            'total_score_percentile_rank': data.get('total_score_percentile_rank'),
        }
        
        # Add financial scores if available
        if financial_scores:
            response_data['financial_total_percentile'] = financial_scores.get('total_percentile')
            response_data['financial_total_rank'] = financial_scores.get('total_rank')
        
        # Check if ticker is in watchlist
        in_watchlist = is_in_watchlist(ticker)
        
        return jsonify({
            'success': True,
            'ticker': ticker,
            'query': query,
            'match_type': match_type,
            'data': response_data,
            'in_watchlist': in_watchlist
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
            
            # Format metric name for display (use explicit name if available)
            display_name = METRIC_DISPLAY_NAMES.get(score_key, score_key.replace('_', ' ').title())
            
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

@app.route('/financial/<ticker>')
def financial_metrics_page(ticker):
    """Display all financial metric scores for a ticker."""
    ticker = ticker.strip().upper()
    
    # Get financial scores from database
    financial_scores = get_financial_scores(ticker)
    
    if not financial_scores:
        # Get company name from cache for error message
        data = get_complete_data(ticker)
        company_name = data.get('company_name') if data else None
        return render_template('financial_metrics.html', 
                             ticker=ticker,
                             company_name=company_name,
                             error="No financial score data found for this ticker.")
    
    # Build metrics detail list
    metrics_detail = []
    for metric in METRICS:
        value = financial_scores.get(metric.key)
        rank = financial_scores.get(f'{metric.key}_rank')
        percentile = financial_scores.get(f'{metric.key}_percentile')
        
        if value is not None:
            metrics_detail.append({
                'key': metric.key,
                'name': metric.display_name,
                'description': metric.description,
                'value': value,
                'rank': rank,
                'percentile': percentile,
                'sort_descending': metric.sort_descending,
            })
    
    # Sort by percentile (descending) - higher percentile is better
    metrics_detail.sort(key=lambda x: x['percentile'] if x['percentile'] is not None else 0, reverse=True)
    
    # Get total percentile and rank
    total_percentile = financial_scores.get('total_percentile')
    total_rank = financial_scores.get('total_rank')
    
    return render_template('financial_metrics.html',
                         ticker=ticker,
                         company_name=financial_scores.get('company_name'),
                         metrics=metrics_detail,
                         total_percentile=total_percentile,
                         total_rank=total_rank)

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

@app.route('/watchlist')
def watchlist_page():
    """Serve the watchlist page."""
    return render_template('watchlist.html')

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist_api():
    """Get all tickers in watchlist with their data."""
    try:
        tickers = get_watchlist()
        watchlist_data = []
        
        for ticker in tickers:
            # Get data from cache
            data = get_complete_data(ticker)
            financial_scores = get_financial_scores(ticker)
            
            if data:
                watchlist_data.append({
                    'ticker': ticker,
                    'company_name': data.get('company_name'),
                    'short_float': data.get('short_float'),
                    'total_score_percentile_rank': data.get('total_score_percentile_rank'),
                    'financial_total_percentile': financial_scores.get('total_percentile') if financial_scores else None,
                })
            else:
                # Include ticker even if no data available
                watchlist_data.append({
                    'ticker': ticker,
                    'company_name': None,
                    'short_float': None,
                    'total_score_percentile_rank': None,
                    'financial_total_percentile': None,
                })
        
        return jsonify({
            'success': True,
            'watchlist': watchlist_data
        })
    except Exception as e:
        print(f"Error getting watchlist: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/watchlist/add/<ticker>', methods=['POST'])
def add_to_watchlist_api(ticker):
    """Add a ticker to the watchlist."""
    try:
        added = add_to_watchlist(ticker)
        if added:
            return jsonify({
                'success': True,
                'message': f'{ticker} added to watchlist'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'{ticker} is already in watchlist'
            }), 400
    except Exception as e:
        print(f"Error adding to watchlist: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/watchlist/remove/<ticker>', methods=['POST'])
def remove_from_watchlist_api(ticker):
    """Remove a ticker from the watchlist."""
    try:
        removed = remove_from_watchlist(ticker)
        if removed:
            return jsonify({
                'success': True,
                'message': f'{ticker} removed from watchlist'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'{ticker} not found in watchlist'
            }), 404
    except Exception as e:
        print(f"Error removing from watchlist: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

