#!/usr/bin/env python3
"""
API controller for handling web requests.
"""
from flask import jsonify
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.data_service import DataService
from services.watchlist_service import WatchlistService

class ApiController:
    """Controller for API endpoints."""

    def __init__(self, data_service: DataService, watchlist_service: WatchlistService):
        self.data_service = data_service
        self.watchlist_service = watchlist_service

    def search_ticker(self, query: str):
        """Handle ticker search requests."""
        result = self.data_service.search_ticker(query)
        status_code = 404 if not result['success'] else 200
        return jsonify(result), status_code

    def get_search_suggestions(self, query: str):
        """Handle search suggestions requests."""
        result = self.data_service.get_search_suggestions(query)
        status_code = 400 if not result['success'] else 200
        return jsonify(result), status_code

    def get_metrics(self, ticker: str):
        """Handle metrics requests."""
        result = self.data_service.get_metrics_data(ticker)
        status_code = 404 if not result['success'] else 200
        return jsonify(result), status_code

    def get_financial_metrics(self, ticker: str):
        """Handle financial metrics requests."""
        result = self.data_service.get_financial_metrics_data(ticker)
        status_code = 404 if not result['success'] else 200
        return jsonify(result), status_code

    def get_watchlist(self):
        """Handle watchlist retrieval requests."""
        try:
            result = self.watchlist_service.get_watchlist()
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    def add_to_watchlist(self, ticker: str):
        """Handle add to watchlist requests."""
        try:
            result = self.watchlist_service.add_to_watchlist(ticker)
            status_code = 400 if not result['success'] else 200
            if not result['success'] and 'already in watchlist' in result['message']:
                status_code = 400
            elif not result['success'] and 'not found' in result['message']:
                status_code = 404
            return jsonify(result), status_code
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    def remove_from_watchlist(self, ticker: str):
        """Handle remove from watchlist requests."""
        try:
            result = self.watchlist_service.remove_from_watchlist(ticker)
            status_code = 404 if not result['success'] else 200
            return jsonify(result), status_code
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    def get_list(self):
        """Handle ticker list requests."""
        try:
            from ..repositories.data_repository import DataRepository
            repo = DataRepository()
            tickers = repo.get_all_tickers()
            return jsonify({'success': True, 'count': len(tickers), 'tickers': tickers})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    def get_adjusted_pe(self, ticker: str):
        """Handle adjusted PE requests."""
        try:
            from ..repositories.adjusted_pe_repository import AdjustedPERepository
            repo = AdjustedPERepository()
            ratio, breakdown = repo.get_adjusted_pe_with_breakdown(ticker)
            if ratio is None or breakdown is None:
                return jsonify({'success': False, 'message': 'Data not available'}), 404

            breakdown['ticker'] = ticker
            return jsonify({'success': True, 'adjusted_pe_ratio': ratio, 'breakdown': breakdown})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    def get_ai_scores(self):
        """Handle AI scores list requests."""
        try:
            from ..repositories.ai_scores_repository import AIScoresRepository
            repo = AIScoresRepository()
            scores = repo.get_all_ai_scores()
            return jsonify({'success': True, 'scores': scores})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # Placeholder methods for future implementation
    def get_peers(self, ticker: str):
        """Handle peer requests (placeholder)."""
        return jsonify({'success': False, 'message': 'Peers functionality not yet implemented'}), 501

    def find_peers(self, ticker: str):
        """Handle find peers requests (placeholder)."""
        return jsonify({'success': False, 'message': 'Find peers functionality not yet implemented'}), 501