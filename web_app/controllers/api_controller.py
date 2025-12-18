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
from services.peers_service import PeersService
from repositories.peers_repository import PeersRepository

class ApiController:
    """Controller for API endpoints."""

    def __init__(self, data_service: DataService, watchlist_service: WatchlistService):
        self.data_service = data_service
        self.watchlist_service = watchlist_service

        # Initialize peers components
        from repositories.data_repository import DataRepository
        peers_repo = PeersRepository()
        data_repo = DataRepository()
        self.peers_service = PeersService(peers_repo, data_repo)

        # Track ongoing peer finding operations to prevent duplicate requests
        self.ongoing_peer_finding = set()

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
            from repositories.adjusted_pe_repository import AdjustedPERepository
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
            from repositories.ai_scores_repository import AIScoresRepository
            repo = AIScoresRepository()
            scores = repo.get_all_ai_scores()
            return jsonify({'success': True, 'scores': scores})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # Placeholder methods for future implementation
    def get_peers(self, ticker: str):
        """Handle peer requests."""
        result = self.peers_service.get_peers(ticker)

        # If no peers found, automatically trigger peer finding (but only once per ticker)
        if not result['success'] and 'No peer analysis found' in result.get('message', ''):
            if ticker.upper() in self.ongoing_peer_finding:
                # Peer finding already in progress for this ticker
                print(f"Peer finding already in progress for {ticker}")
                return jsonify({
                    'success': True,
                    'finding_peers': True,
                    'message': 'Peer finding is already in progress...',
                    'main_ticker': {
                        'ticker': ticker,
                        'company_name': None,
                        'total_score_percentile_rank': None,
                        'financial_total_percentile': None,
                        'adjusted_pe_ratio': None,
                        'short_float': None
                    },
                    'peers': []
                }), 202

            print(f"No existing peers found for {ticker}, triggering automatic peer finding...")
            # Mark peer finding as in progress
            self.ongoing_peer_finding.add(ticker.upper())

            # Trigger peer finding in background
            try:
                import threading
                def find_peers_background():
                    try:
                        self.peers_service.find_peers(ticker)
                        print(f"Background peer finding completed for {ticker}")
                    except Exception as e:
                        print(f"Background peer finding failed for {ticker}: {e}")
                    finally:
                        # Remove from ongoing set regardless of success/failure
                        self.ongoing_peer_finding.discard(ticker.upper())

                # Start background peer finding
                thread = threading.Thread(target=find_peers_background, daemon=True)
                thread.start()

                # Return a "finding peers" response
                return jsonify({
                    'success': True,
                    'finding_peers': True,
                    'message': 'No existing peers found. Automatically finding peers...',
                    'main_ticker': {
                        'ticker': ticker,
                        'company_name': None,  # Will be filled when peers are found
                        'total_score_percentile_rank': None,
                        'financial_total_percentile': None,
                        'adjusted_pe_ratio': None,
                        'short_float': None
                    },
                    'peers': []
                }), 202  # 202 Accepted - processing request

            except Exception as e:
                print(f"Failed to start background peer finding: {e}")
                # Remove from ongoing set if thread creation failed
                self.ongoing_peer_finding.discard(ticker.upper())
                return jsonify({
                    'success': False,
                    'message': f'Failed to find peers: {str(e)}'
                }), 500

        status_code = 404 if not result['success'] else 200
        return jsonify(result), status_code

    def find_peers(self, ticker: str):
        """Handle find peers requests."""
        result = self.peers_service.find_peers(ticker)
        status_code = 400 if not result['success'] else 200
        return jsonify(result), status_code