#!/usr/bin/env python3
"""
Simple Flask web application to search for stock data by ticker symbol.
Uses unified cache database to store and retrieve all UI data.
"""
from flask import Flask, render_template, jsonify, request, send_from_directory
import json
import os
import sys
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime

# Ensure project root is on path so we can import modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import unified cache database manager
from web_app.ui_cache_db import (
    get_complete_data,
    init_database,
    get_cached_data,
    fetch_adjusted_pe_ratio_and_breakdown,
    calculate_two_year_annualized_growth,
)

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

# Import peer database
from web_app.peer_db import get_peers_for_ticker, init_peers_database

# Import adjusted PE storage
from web_app.adjusted_pe_db import get_adjusted_pe, init_adjusted_pe_db

# Import score calculator for weights and definitions
from web_app.score_calculator import SCORE_WEIGHTS, SCORE_DEFINITIONS

# Import revenue growth analyzer
try:
    from web_app.yfinance.yfinance_revenue_growth import get_revenue_growth_estimates
    REVENUE_GROWTH_AVAILABLE = True
except ImportError:
    REVENUE_GROWTH_AVAILABLE = False
    print("Warning: Revenue growth analyzer not available")

def find_ticker_for_company(company_name: str) -> str:
    """Find ticker for a company name by searching available databases.
    Only returns real tickers from tickers.db.
    """
    # Check tickers.db first (only contains real tickers)
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'tickers.db'))
        cur = conn.cursor()
        cur.execute("SELECT ticker FROM tickers WHERE company_name = ?", (company_name,))
        result = cur.fetchone()
        conn.close()
        if result:
            return result[0]
    except:
        pass

    # If not found in tickers.db, return None (no fake ticker)
    return None

# Import AI client for peer finding
try:
    from src.clients.grok_client import GrokClient
    from src.clients.openrouter_client import OpenRouterClient
    from config import XAI_API_KEY, OPENROUTER_KEY

    def get_api_client():
        """Get configured API client."""
        if XAI_API_KEY:
            return GrokClient(XAI_API_KEY)
        elif OPENROUTER_KEY:
            return OpenRouterClient(OPENROUTER_KEY)
        else:
            raise ValueError("No API key configured")

    def get_model_for_ticker(ticker):
        """Get appropriate model for ticker analysis."""
        return "grok-4-1-fast-reasoning" if XAI_API_KEY else "anthropic/claude-3.5-sonnet"

    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("Warning: AI client imports failed, peer finding will not be available")

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

app = Flask(__name__, static_folder='frontend/dist', static_url_path='/')

# Initialize databases on startup
init_database()
init_watchlist_database()
init_peers_database()
init_adjusted_pe_db()

def find_best_match(query: str) -> tuple:
    """Find ticker match using exact prefix matching on tickers and company names.

    Validates against tickers database for exact prefix matches on both tickers and company names.
    Allows partial input (e.g., "A" matches "AAPL", "AMD", "Apple Inc.", etc.)

    Args:
        query: User search query (prefix of ticker symbol or company name)

    Returns:
        tuple: (ticker, match_type) where match_type is 'ticker' or None if no prefix match
    """
    query_upper = query.strip().upper()

    # Validate that it's a valid ticker or company name prefix by checking against tickers.db
    tickers_db_path = os.path.join(os.path.dirname(__file__), 'data', 'tickers.db')
    if os.path.exists(tickers_db_path):
        try:
            conn = sqlite3.connect(tickers_db_path)
            cursor = conn.cursor()

            # First, try exact ticker prefix match
            cursor.execute('SELECT ticker FROM tickers WHERE ticker LIKE ? ORDER BY ticker LIMIT 1', (query_upper + '%',))
            ticker_result = cursor.fetchone()

            if ticker_result:
                ticker = ticker_result[0]
            else:
                # If no ticker match, try company name prefix match
                cursor.execute('SELECT ticker FROM tickers WHERE UPPER(company_name) LIKE ? ORDER BY ticker LIMIT 1', (query_upper + '%',))
                company_result = cursor.fetchone()
                if company_result:
                    ticker = company_result[0]
                else:
                    ticker = None

            conn.close()

            if ticker:
                # Check if we have cached data for this ticker
                cache_db_path = os.path.join(os.path.dirname(__file__), 'data', 'ui_cache.db')
                if os.path.exists(cache_db_path):
                    try:
                        conn = sqlite3.connect(cache_db_path)
                        cursor = conn.cursor()
                        cursor.execute('SELECT ticker FROM ui_cache WHERE ticker = ?', (ticker,))
                        cache_result = cursor.fetchone()
                        conn.close()

                        if cache_result:
                            return ticker, 'ticker'
                        else:
                            return ticker, 'ticker_not_cached'
                    except Exception as e:
                        print(f"Error querying cache for matching: {e}")
                        return ticker, 'ticker_not_cached'
                else:
                    return ticker, 'ticker_not_cached'
        except Exception as e:
            print(f"Error querying tickers database: {e}")

    # No prefix match found in tickers database
    return None, None

# API Routes
@app.route('/api/search/<query>')
def search_ticker(query):
    """API endpoint to search for stock data by exact ticker symbol."""
    ticker, match_type = find_best_match(query)

    if not ticker:
        return jsonify({
            'success': False,
            'query': query,
            'message': f'No tickers found starting with "{query}". Please enter a valid ticker prefix (e.g., AAPL).'
        }), 404
    
    try:
        data = get_complete_data(ticker)
        if not data:
            return jsonify({
                'success': False,
                'query': query,
                'message': f'Could not fetch data for "{ticker}". Please check that the ticker is valid.'
            }), 404
        
        financial_scores = get_financial_scores(ticker)
        response_data = {
            'ticker': ticker,
            'company_name': data.get('company_name'),
            'short_float': data.get('short_float'),
            'total_score_percentage': data.get('total_score_percentage'),
            'total_score_percentile_rank': data.get('total_score_percentile_rank'),
            'adjusted_pe_ratio': data.get('adjusted_pe_ratio'),
            'current_year_growth': data.get('current_year_growth'),
            'next_year_growth': data.get('next_year_growth'),
        }
        
        if financial_scores:
            response_data['financial_total_percentile'] = financial_scores.get('total_percentile')
            response_data['financial_total_rank'] = financial_scores.get('total_rank')
        
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
        print(f"Error fetching data for {ticker}: {e}")
        return jsonify({
            'success': False,
            'query': query,
            'message': f'Error fetching data for "{ticker}": {str(e)}'
        }), 500

@app.route('/api/search_suggestions/<query>')
def search_suggestions(query):
    """API endpoint to get search suggestions."""
    if not query or len(query.strip()) < 1:
        return jsonify({'success': False, 'message': 'Query too short'}), 400

    query_upper = query.strip().upper()
    try:
        tickers_db_path = os.path.join(os.path.dirname(__file__), 'data', 'tickers.db')
        if not os.path.exists(tickers_db_path):
            return jsonify({'success': False, 'message': 'Tickers database not found'}), 500

        conn = sqlite3.connect(tickers_db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT ticker, company_name,
                   CASE
                       WHEN ticker LIKE ? THEN 'ticker'
                       WHEN UPPER(company_name) LIKE ? THEN 'company'
                   END as match_type,
                   CASE
                       WHEN ticker LIKE ? THEN 1
                       WHEN UPPER(company_name) LIKE ? THEN 2
                   END as priority
            FROM tickers
            WHERE ticker LIKE ? OR UPPER(company_name) LIKE ?
            ORDER BY priority, ticker
            LIMIT 10
        """, (query_upper + '%', query_upper + '%', query_upper + '%', query_upper + '%', query_upper + '%', query_upper + '%'))

        results = []
        seen_tickers = set()
        for row in cur.fetchall():
            ticker, company_name, match_type, priority = row
            if ticker not in seen_tickers:
                results.append({'ticker': ticker, 'company_name': company_name, 'match_type': match_type})
                seen_tickers.add(ticker)
        conn.close()
        return jsonify({'success': True, 'query': query, 'suggestions': results, 'count': len(results)})
    except Exception as e:
        print(f"Error searching tickers: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500

@app.route('/api/metrics/<ticker>')
def get_metrics_api(ticker):
    """API endpoint to get all metric scores for a ticker."""
    ticker = ticker.strip().upper()
    data = get_complete_data(ticker)
    if not data:
        return jsonify({'success': False, 'message': f'No data found for "{ticker}"'}), 404
    
    score_data = {k: v for k, v in data.items() if k not in ['ticker', 'company_name', 'last_updated', 'short_float', 'short_interest_scraped_at']}
    if not score_data or not any(score_data.values()):
        return jsonify({'success': False, 'message': f'No score data found for "{ticker}"'}), 404
    
    metrics_detail = []
    total_score = 0.0
    max_score = sum(SCORE_WEIGHTS.get(key, 1.0) for key in SCORE_DEFINITIONS) * 10
    
    for score_key in SCORE_DEFINITIONS:
        score_def = SCORE_DEFINITIONS[score_key]
        weight = SCORE_WEIGHTS.get(score_key, 1.0)
        try:
            score_value = float(score_data.get(score_key))
            adjusted_value = 10 - score_value if score_def['is_reverse'] else score_value
            contribution = adjusted_value * weight
            total_score += contribution
            display_name = METRIC_DISPLAY_NAMES.get(score_key, score_key.replace('_', ' ').title())
            metrics_detail.append({
                'key': score_key, 'name': display_name, 'raw_score': score_value,
                'adjusted_score': adjusted_value, 'weight': weight, 'contribution': contribution,
                'is_reverse': score_def['is_reverse'], 'percentage': (contribution / max_score) * 100 if max_score > 0 else 0
            })
        except: continue
    
    metrics_detail.sort(key=lambda x: x['contribution'], reverse=True)
    return jsonify({
        'success': True, 'ticker': ticker, 'company_name': data.get('company_name'),
        'metrics': metrics_detail, 'total_score_percentage': score_data.get('total_score_percentage'),
        'total_score_percentile_rank': score_data.get('total_score_percentile_rank'), 'max_score': max_score
    })

@app.route('/api/financial/<ticker>')
def get_financial_metrics_api(ticker):
    """API endpoint to get all financial metric scores for a ticker."""
    ticker = ticker.strip().upper()
    financial_scores = get_financial_scores(ticker)
    if not financial_scores:
        data = get_complete_data(ticker)
        return jsonify({'success': False, 'company_name': data.get('company_name') if data else None, 'message': f'No financial score data found for "{ticker}"'}), 404
    
    metrics_detail = []
    for metric in METRICS:
        value = financial_scores.get(metric.key)
        if value is not None:
            metrics_detail.append({
                'key': metric.key, 'name': metric.display_name, 'description': metric.description,
                'value': value, 'rank': financial_scores.get(f'{metric.key}_rank'),
                'percentile': financial_scores.get(f'{metric.key}_percentile'), 'sort_descending': metric.sort_descending,
            })
    metrics_detail.sort(key=lambda x: x['percentile'] if x['percentile'] is not None else 0, reverse=True)
    return jsonify({
        'success': True, 'ticker': ticker, 'company_name': financial_scores.get('company_name'),
        'metrics': metrics_detail, 'total_percentile': financial_scores.get('total_percentile'),
        'total_rank': financial_scores.get('total_rank')
    })

@app.route('/api/list')
def list_all():
    """API endpoint to list all available tickers."""
    cache_db_path = os.path.join(os.path.dirname(__file__), 'data', 'ui_cache.db')
    if not os.path.exists(cache_db_path):
        return jsonify({'success': True, 'count': 0, 'tickers': []})
    try:
        conn = sqlite3.connect(cache_db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT ticker FROM ui_cache ORDER BY ticker')
        tickers = [row[0] for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'count': len(tickers), 'tickers': tickers})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist_api():
    """Get all tickers in watchlist."""
    try:
        tickers = get_watchlist()
        watchlist_data = []
        for ticker in tickers:
            data = get_complete_data(ticker)
            financial_scores = get_financial_scores(ticker)
            if data:
                # Calculate 2-year annualized growth from analyst estimates
                current_year_growth = data.get('current_year_growth')
                next_year_growth = data.get('next_year_growth')
                two_year_annualized_growth = calculate_two_year_annualized_growth(current_year_growth, next_year_growth) if current_year_growth is not None and next_year_growth is not None else None

                watchlist_data.append({
                    'ticker': ticker, 'company_name': data.get('company_name'),
                    'short_float': data.get('short_float'), 'total_score_percentile_rank': data.get('total_score_percentile_rank'),
                    'financial_total_percentile': financial_scores.get('total_percentile') if financial_scores else None,
                    'adjusted_pe_ratio': data.get('adjusted_pe_ratio'),
                    'two_year_annualized_growth': two_year_annualized_growth,
                })
            else:
                watchlist_data.append({'ticker': ticker, 'company_name': None, 'short_float': None, 'total_score_percentile_rank': None, 'financial_total_percentile': None, 'adjusted_pe_ratio': None, 'two_year_annualized_growth': None})
        return jsonify({'success': True, 'watchlist': watchlist_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/watchlist/add/<ticker>', methods=['POST'])
def add_to_watchlist_api(ticker):
    """Add a ticker to the watchlist."""
    try:
        ticker = ticker.strip().upper()
        if not get_complete_data(ticker):
            return jsonify({'success': False, 'message': f'Ticker "{ticker}" not found'}), 404
        if is_in_watchlist(ticker):
            return jsonify({'success': False, 'message': f'{ticker} is already in watchlist'}), 400
        if add_to_watchlist(ticker):
            return jsonify({'success': True, 'message': f'{ticker} added to watchlist'})
        return jsonify({'success': False, 'message': f'Failed to add {ticker} to watchlist'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/watchlist/remove/<ticker>', methods=['POST'])
def remove_from_watchlist_api(ticker):
    """Remove a ticker from the watchlist."""
    try:
        if remove_from_watchlist(ticker.strip().upper()):
            return jsonify({'success': True, 'message': f'{ticker} removed from watchlist'})
        return jsonify({'success': False, 'message': f'{ticker} not found in watchlist'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def fetch_peer_data(peer_ticker):
    peer_data = get_complete_data(peer_ticker)
    peer_financial_scores = get_financial_scores(peer_ticker)
    return {
        'ticker': peer_ticker,
        'company_name': peer_data.get('company_name') if peer_data else None,
        'total_score_percentile_rank': peer_data.get('total_score_percentile_rank') if peer_data else None,
        'financial_total_percentile': peer_financial_scores.get('total_percentile') if peer_financial_scores else None,
        'adjusted_pe_ratio': peer_data.get('adjusted_pe_ratio') if peer_data else None,
        'short_float': peer_data.get('short_float') if peer_data else None,
    }

def find_peers_for_ticker_ai(ticker, company_name=None):
    if not AI_AVAILABLE: return None, "AI functionality not available"
    try:
        if not company_name:
            ticker_data = get_complete_data(ticker)
            company_name = ticker_data.get('company_name') if ticker_data else ticker
        prompt = f"""You are analyzing companies to find the 10 most comparable companies to {company_name}.

Your task is to find the 10 MOST comparable companies to {company_name}.

Consider factors such as:
1. Industry and market segment similarity (MUST be in same or very similar industry)
2. Business model similarity
3. Product/service similarity
4. Market overlap and customer base similarity
5. Competitive dynamics (direct competitors)
6. Company size and scale (if relevant)

For each company, provide both the clean company name and its stock ticker symbol (if it has one).
Return ONLY a semicolon-separated list of exactly 10 entries, starting with the most comparable company first.
Each entry should be in format: "Company Name|Ticker" or "Company Name|NONE" if no ticker exists.

CRITICAL: Use semicolons (;) to separate entries, NOT commas.
IMPORTANT: Use ONLY the core company name without generic suffixes like Inc, Corp, Co, Ltd, LLC, Group, Holdings, Corporation, Incorporated, Limited, etc.
Examples: "Microsoft|MSFT", "Alphabet|GOOG", "Apple|AAPL", "Nike|NKE", "Meta|META".
For private companies or those without tickers, use "NONE" as the ticker.

Do not include explanations, ranking numbers, or any other text - just the 10 entries separated by semicolons in order from most to least comparable.

Example format: "Microsoft|MSFT; Alphabet|GOOG; Meta|META; Amazon|AMZN; Nvidia|NVDA; Intel|INTC; Advanced Micro Devices|AMD; Salesforce|CRM; Oracle|ORCL; Adobe|ADBE"

Return exactly 10 entries in ranked order, separated by semicolons, nothing else."""
        grok = get_api_client()
        model = get_model_for_ticker(ticker)
        start_time = time.time()
        response, token_usage = grok.simple_query_with_tokens(prompt, model=model)
        elapsed_time = time.time() - start_time
        entries = [entry.strip() for entry in response.strip().split(';') if entry.strip()]
        peers_data = []
        for entry in entries[:10]:
            if '|' in entry:
                parts = entry.split('|', 1)
                peers_data.append({'name': parts[0].strip(), 'ticker': parts[1].strip() if parts[1].strip() != 'NONE' else None})
            else:
                peers_data.append({'name': entry, 'ticker': None})
        return peers_data, None, token_usage, elapsed_time
    except Exception as e: return None, str(e)

@app.route('/api/peers/<ticker>', methods=['GET'])
def get_peers_api(ticker):
    """Get peer data for a ticker."""
    try:
        ticker = ticker.strip().upper()
        peers_data_from_db = get_peers_for_ticker(ticker)
        peer_tickers = [p.get('ticker') for p in peers_data_from_db if p.get('ticker')]
        if not peer_tickers:
            ticker_data = get_complete_data(ticker)
            company_name = ticker_data.get('company_name') if ticker_data else ticker
            peers_data, error, token_usage, elapsed_time = find_peers_for_ticker_ai(ticker, company_name)
            if error or not peers_data: return jsonify({'success': False, 'message': f'Failed to generate peers: {error}'}), 500
            peer_tickers = [p.get('ticker') for p in peers_data if p.get('ticker')]
        
        main_ticker_data = get_complete_data(ticker)
        main_financial_scores = get_financial_scores(ticker)
        main_data = {
            'ticker': ticker, 'company_name': main_ticker_data.get('company_name') if main_ticker_data else None,
            'total_score_percentile_rank': main_ticker_data.get('total_score_percentile_rank') if main_ticker_data else None,
            'financial_total_percentile': main_financial_scores.get('total_percentile') if main_financial_scores else None,
            'adjusted_pe_ratio': main_ticker_data.get('adjusted_pe_ratio') if main_ticker_data else None,
            'short_float': main_ticker_data.get('short_float') if main_ticker_data else None,
        }
        peers_data = []
        with ThreadPoolExecutor(max_workers=max(1, len(peer_tickers))) as executor:
            future_to_peer = {executor.submit(fetch_peer_data, pt): pt for pt in peer_tickers}
            for future in as_completed(future_to_peer):
                peers_data.append(future.result())
        return jsonify({'success': True, 'main_ticker': main_data, 'peers': peers_data})
    except Exception as e: return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/find_peers/<ticker>', methods=['GET'])
def find_peers_api(ticker):
    """Find peers for a ticker using AI."""
    try:
        ticker = ticker.strip().upper()
        ticker_data = get_complete_data(ticker)
        company_name = ticker_data.get('company_name') if ticker_data else ticker
        peers, error, token_usage, elapsed_time = find_peers_for_ticker_ai(ticker, company_name)
        if error: return jsonify({'success': False, 'message': f'Error: {error}'}), 500
        return jsonify({'success': True, 'ticker': ticker, 'company_name': company_name, 'peers': peers, 'elapsed_time': elapsed_time})
    except Exception as e: return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/adjusted_pe/<ticker>', methods=['GET'])
def get_adjusted_pe_api(ticker):
    """Get adjusted PE ratio."""
    try:
        ticker = ticker.strip().upper()
        stored = get_adjusted_pe(ticker)
        ratio = stored.get('adjusted_pe_ratio') if stored else None
        if not stored or ratio is None:
            ratio, breakdown = fetch_adjusted_pe_ratio_and_breakdown(ticker)
        else: breakdown = stored
        if ratio is None or breakdown is None: return jsonify({'success': False, 'message': 'Data not available'}), 404
        breakdown['ticker'] = ticker
        return jsonify({'success': True, 'adjusted_pe_ratio': ratio, 'breakdown': breakdown})
    except Exception as e: return jsonify({'success': False, 'message': str(e)}), 500

AI_SCORES_DB = os.path.join(os.path.dirname(__file__), 'data', 'ai_scores.db')
@app.route('/api/ai_scores')
def get_ai_scores_api():
    """Get all AI scores."""
    try:
        conn = sqlite3.connect(AI_SCORES_DB)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(f"ATTACH DATABASE '{os.path.join(os.path.dirname(__file__), 'data', 'tickers.db')}' AS tickers_db")
        cur.execute("SELECT s.*, t.company_name FROM scores s LEFT JOIN tickers_db.tickers t ON s.ticker = t.ticker ORDER BY s.total_score_percentile_rank DESC")
        scores = [dict(row) for row in cur.fetchall()]
        conn.close()
        return jsonify({'success': True, 'scores': scores})
    except Exception as e: return jsonify({'success': False, 'message': str(e)}), 500

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
