#!/usr/bin/env python3
"""
Repository for financial scores data access.
"""
from typing import Optional, Dict, Any, List
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from base_repository import BaseRepository, DB_PATH

class FinancialScoresRepository(BaseRepository):
    """Repository for financial scores database operations."""

    def __init__(self, db_path: str = DB_PATH):
        super().__init__(db_path)

    def get_financial_scores_by_company_id(self, company_id: int) -> Optional[Dict[str, Any]]:
        """Get financial scores for a company."""
        query = "SELECT * FROM financial_scores WHERE company_id = ?"
        return self.execute_single(query, (company_id,))

    def get_financial_scores_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get financial scores for a ticker."""
        query = """
            SELECT fs.* FROM financial_scores fs
            JOIN companies c ON fs.company_id = c.id
            WHERE c.ticker = ?
        """
        return self.execute_single(query, (ticker.upper(),))

    def create_or_update_financial_scores(self, company_id: int, scores: Dict[str, Any]) -> bool:
        """Create or update financial scores for a company."""
        # Check if scores exist
        existing = self.get_financial_scores_by_company_id(company_id)

        if existing:
            # Update existing
            set_clauses = [f"{key} = ?" for key in scores.keys()]
            values = list(scores.values()) + [company_id]

            query = f"""
                UPDATE financial_scores
                SET {', '.join(set_clauses)}, last_updated = CURRENT_TIMESTAMP
                WHERE company_id = ?
            """
            return self.execute_update(query, tuple(values)) > 0
        else:
            # Insert new
            columns = list(scores.keys())
            placeholders = ', '.join(['?' for _ in columns])
            values = list(scores.values())

            query = f"""
                INSERT INTO financial_scores (company_id, {', '.join(columns)}, last_updated)
                VALUES (?, {placeholders}, CURRENT_TIMESTAMP)
            """
            return self.execute_insert(query, [company_id] + values) > 0

    def get_all_financial_scores(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all financial scores with company information."""
        query = """
            SELECT fs.*, c.ticker, c.company_name
            FROM financial_scores fs
            JOIN companies c ON fs.company_id = c.id
            ORDER BY fs.total_percentile DESC
        """
        if limit:
            query += " LIMIT ? OFFSET ?"
            return self.execute_query(query, (limit, offset))
        return self.execute_query(query)

    def get_financial_scores_count(self) -> int:
        """Get total count of companies with financial scores."""
        query = "SELECT COUNT(*) as count FROM financial_scores"
        result = self.execute_single(query)
        return result['count'] if result else 0

    def delete_financial_scores(self, company_id: int) -> bool:
        """Delete financial scores for a company."""
        query = "DELETE FROM financial_scores WHERE company_id = ?"
        return self.execute_update(query, (company_id,)) > 0

    def get_top_financial_scores(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top companies by financial score percentile."""
        query = """
            SELECT fs.*, c.ticker, c.company_name
            FROM financial_scores fs
            JOIN companies c ON fs.company_id = c.id
            ORDER BY fs.total_percentile DESC
            LIMIT ?
        """
        return self.execute_query(query, (limit,))