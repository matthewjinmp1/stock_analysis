#!/usr/bin/env python3
"""
Repository for peers data access.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from base_repository import BaseRepository, DB_PATH
from typing import Optional, Dict, Any, List

class PeersRepository(BaseRepository):
    """Repository for peers database operations."""

    def __init__(self, db_path: str = DB_PATH):
        super().__init__(db_path)

    def get_peer_analysis(self, ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get peer analysis history for a ticker from the peers database.

        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of analyses to return

        Returns:
            List of peer analysis records
        """
        try:
            # Import the existing peers database functionality
            peers_db_path = os.path.join(os.path.dirname(__file__), '..', 'peers', 'peers_results_db.py')
            if os.path.exists(peers_db_path):
                # Import the function from the existing module
                import importlib.util
                spec = importlib.util.spec_from_file_location("peers_results_db", peers_db_path)
                peers_db = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(peers_db)

                return peers_db.get_peer_analysis(ticker, limit)
            else:
                return []
        except Exception as e:
            print(f"Error retrieving peer analysis: {e}")
            return []

    def save_peer_analysis(self, ticker: str, company_name: str, peers: List[Dict[str, Any]],
                          token_usage: Optional[Dict[str, Any]] = None,
                          estimated_cost_cents: Optional[float] = None,
                          analysis_timestamp: Optional[str] = None) -> bool:
        """
        Save peer analysis results to the peers database.

        Args:
            ticker: Stock ticker symbol
            company_name: Full company name
            peers: List of peer data (dicts with 'name' and 'ticker' keys)
            token_usage: Dictionary with token usage details
            estimated_cost_cents: Cost in cents
            analysis_timestamp: ISO timestamp of analysis

        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Import the existing peers database functionality
            peers_db_path = os.path.join(os.path.dirname(__file__), '..', 'peers', 'peers_results_db.py')
            if os.path.exists(peers_db_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("peers_results_db", peers_db_path)
                peers_db = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(peers_db)

                return peers_db.save_peer_analysis(
                    ticker=ticker,
                    company_name=company_name,
                    peers=peers,
                    token_usage=token_usage,
                    estimated_cost_cents=estimated_cost_cents,
                    analysis_timestamp=analysis_timestamp
                )
            else:
                return False
        except Exception as e:
            print(f"Error saving peer analysis: {e}")
            return False

    def get_all_peer_analyses(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all peer analyses from the peers database.

        Args:
            limit: Maximum number of analyses to return

        Returns:
            List of all peer analysis records
        """
        try:
            # Import the existing peers database functionality
            peers_db_path = os.path.join(os.path.dirname(__file__), '..', 'peers', 'peers_results_db.py')
            if os.path.exists(peers_db_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("peers_results_db", peers_db_path)
                peers_db = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(peers_db)

                return peers_db.get_all_peer_analyses(limit)
            else:
                return []
        except Exception as e:
            print(f"Error retrieving all peer analyses: {e}")
            return []