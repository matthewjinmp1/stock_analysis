#!/usr/bin/env python3
"""
Flask web application with layered architecture for stock analysis.
"""
from flask import Flask, render_template, jsonify, request, send_from_directory
import os
import sys

# Ensure project root is on path so we can import modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import layered architecture components
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from repositories.data_repository import DataRepository
from repositories.watchlist_repository import WatchlistRepository
from services.data_service import DataService
from services.watchlist_service import WatchlistService
from controllers.api_controller import ApiController

# Initialize Flask app
app = Flask(__name__, static_folder='frontend/dist', static_url_path='/')

# Initialize layered architecture components
data_repo = DataRepository()
watchlist_repo = WatchlistRepository()
data_service = DataService(data_repo, watchlist_repo)
watchlist_service = WatchlistService(watchlist_repo, data_repo)
api_controller = ApiController(data_service, watchlist_service)

# API Routes
@app.route('/api/search/<query>')
def search_ticker(query):
    """API endpoint to search for stock data by exact ticker symbol."""
    return api_controller.search_ticker(query)

@app.route('/api/search_suggestions/<query>')
def search_suggestions(query):
    """API endpoint to get search suggestions."""
    return api_controller.get_search_suggestions(query)

@app.route('/api/metrics/<ticker>')
def get_metrics_api(ticker):
    """API endpoint to get all metric scores for a ticker."""
    return api_controller.get_metrics(ticker)

@app.route('/api/financial/<ticker>')
def get_financial_metrics_api(ticker):
    """API endpoint to get all financial metric scores for a ticker."""
    return api_controller.get_financial_metrics(ticker)

@app.route('/api/list')
def list_all():
    """API endpoint to list all available tickers."""
    return api_controller.get_list()

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist_api():
    """Get all tickers in watchlist."""
    return api_controller.get_watchlist()

@app.route('/api/watchlist/add/<ticker>', methods=['POST'])
def add_to_watchlist_api(ticker):
    """Add a ticker to the watchlist."""
    return api_controller.add_to_watchlist(ticker)

@app.route('/api/watchlist/remove/<ticker>', methods=['POST'])
def remove_from_watchlist_api(ticker):
    """Remove a ticker from the watchlist."""
    return api_controller.remove_from_watchlist(ticker)

@app.route('/api/adjusted_pe/<ticker>', methods=['GET'])
def get_adjusted_pe_api(ticker):
    """Get adjusted PE ratio."""
    return api_controller.get_adjusted_pe(ticker)

@app.route('/api/ai_scores')
def get_ai_scores_api():
    """Get all AI scores."""
    return api_controller.get_ai_scores()

@app.route('/api/peers/<ticker>', methods=['GET'])
def get_peers_api(ticker):
    """Get peer data for a ticker."""
    return api_controller.get_peers(ticker)

@app.route('/api/find_peers/<ticker>', methods=['GET'])
def find_peers_api(ticker):
    """Find peers for a ticker using AI."""
    return api_controller.find_peers(ticker)

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