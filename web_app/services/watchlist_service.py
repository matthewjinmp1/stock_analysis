#!/usr/bin/env python3
"""
Watchlist service for watchlist-related business logic.
"""
from typing import List, Dict, Any
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from repositories.watchlist_repository import WatchlistRepository
from repositories.data_repository import DataRepository

class WatchlistService:
    """Service for watchlist business logic."""

    def __init__(self, watchlist_repo: WatchlistRepository, data_repo: DataRepository):
        self.watchlist_repo = watchlist_repo
        self.data_repo = data_repo

    def get_watchlist(self) -> Dict[str, Any]:
        """Get complete watchlist with enriched data."""
        watchlist_data = self.watchlist_repo.get_watchlist()

        # Enrich with additional calculated fields
        for item in watchlist_data:
            # Calculate two-year annualized growth if data exists
            current_growth = item.get('current_year_growth')
            next_growth = item.get('next_year_growth')
            if current_growth is not None and next_growth is not None:
                item['two_year_annualized_growth'] = self.data_repo.calculate_two_year_annualized_growth(
                    current_growth, next_growth
                )

        return {
            'success': True,
            'watchlist': watchlist_data
        }

    def add_to_watchlist(self, ticker: str) -> Dict[str, Any]:
        """Add ticker to watchlist with validation."""
        ticker = ticker.strip().upper()

        # Validate ticker exists
        data = self.data_repo.get_complete_data(ticker)
        if not data:
            return {
                'success': False,
                'message': f'Ticker "{ticker}" not found'
            }

        # Check if already in watchlist
        if self.watchlist_repo.is_in_watchlist(ticker):
            return {
                'success': False,
                'message': f'{ticker} is already in watchlist'
            }

        # Add to watchlist
        if self.watchlist_repo.add_to_watchlist(ticker):
            return {
                'success': True,
                'message': f'{ticker} added to watchlist'
            }
        else:
            return {
                'success': False,
                'message': f'Failed to add {ticker} to watchlist'
            }

    def remove_from_watchlist(self, ticker: str) -> Dict[str, Any]:
        """Remove ticker from watchlist."""
        ticker = ticker.strip().upper()

        if self.watchlist_repo.remove_from_watchlist(ticker):
            return {
                'success': True,
                'message': f'{ticker} removed from watchlist'
            }
        else:
            return {
                'success': False,
                'message': f'{ticker} not found in watchlist'
            }

    def is_in_watchlist(self, ticker: str) -> bool:
        """Check if ticker is in watchlist."""
        return self.watchlist_repo.is_in_watchlist(ticker.strip().upper())

    def get_watchlist_tickers(self) -> List[str]:
        """Get list of tickers in watchlist."""
        return self.watchlist_repo.get_watchlist_tickers()

    def get_watchlist_count(self) -> int:
        """Get count of items in watchlist."""
        return self.watchlist_repo.get_watchlist_count()