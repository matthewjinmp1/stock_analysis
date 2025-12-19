#!/usr/bin/env python3
"""
Repository for watchlist data access.
"""
from typing import List, Dict, Any
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from base_repository import BaseRepository, DB_PATH

class WatchlistRepository(BaseRepository):
    """Repository for watchlist database operations."""

    def __init__(self, db_path: str = DB_PATH):
        super().__init__(db_path)

    def get_watchlist(self) -> List[Dict[str, Any]]:
        """Get all companies in the watchlist with their data."""
        query = """
            SELECT
                c.ticker,
                c.company_name,
                c.exchange,
                c.sector,
                c.industry,
                w.added_at,
                ais.total_score_percentage,
                ais.total_score_percentile_rank,
                fs.total_percentile as financial_total_percentile,
                ap.adjusted_pe_ratio,
                ap.adjusted_oi_after_tax,
                ap.updated_ev,
                ap.calculation_status as pe_status,
                ge.current_year_growth,
                ge.next_year_growth,
                ge.calculation_status as growth_status,
                ge.last_updated as growth_last_updated,
                si.short_float,
                si.calculation_status as short_interest_status
            FROM watchlist w
            JOIN companies c ON w.company_id = c.id
            LEFT JOIN ai_scores ais ON c.id = ais.company_id
            LEFT JOIN financial_scores fs ON c.id = fs.company_id
            LEFT JOIN adjusted_pe_calculations ap ON c.id = ap.company_id
            LEFT JOIN growth_estimates ge ON c.id = ge.company_id
            LEFT JOIN short_interest si ON c.id = si.company_id
            ORDER BY w.added_at DESC
        """
        return self.execute_query(query)

    def add_to_watchlist(self, ticker: str) -> bool:
        """Add a company to the watchlist."""
        # First get company_id
        query = "SELECT id FROM companies WHERE ticker = ?"
        company = self.execute_single(query, (ticker.upper(),))
        if not company:
            return False

        company_id = company['id']

        # Check if already in watchlist
        existing = self.execute_single(
            "SELECT id FROM watchlist WHERE company_id = ?",
            (company_id,)
        )
        if existing:
            return False

        # Add to watchlist
        query = "INSERT INTO watchlist (company_id) VALUES (?)"
        return self.execute_insert(query, (company_id,)) > 0

    def remove_from_watchlist(self, ticker: str) -> bool:
        """Remove a company from the watchlist."""
        # Get company_id
        query = "SELECT id FROM companies WHERE ticker = ?"
        company = self.execute_single(query, (ticker.upper(),))
        if not company:
            return False

        company_id = company['id']

        # Remove from watchlist
        query = "DELETE FROM watchlist WHERE company_id = ?"
        return self.execute_update(query, (company_id,)) > 0

    def is_in_watchlist(self, ticker: str) -> bool:
        """Check if a company is in the watchlist."""
        query = """
            SELECT 1 FROM watchlist w
            JOIN companies c ON w.company_id = c.id
            WHERE c.ticker = ?
        """
        result = self.execute_single(query, (ticker.upper(),))
        return result is not None

    def get_watchlist_tickers(self) -> List[str]:
        """Get list of tickers in watchlist."""
        query = """
            SELECT c.ticker FROM watchlist w
            JOIN companies c ON w.company_id = c.id
            ORDER BY w.added_at DESC
        """
        results = self.execute_query(query)
        return [row['ticker'] for row in results]

    def get_watchlist_count(self) -> int:
        """Get number of companies in watchlist."""
        query = "SELECT COUNT(*) as count FROM watchlist"
        result = self.execute_single(query)
        return result['count'] if result else 0