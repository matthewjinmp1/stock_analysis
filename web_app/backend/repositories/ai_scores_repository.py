#!/usr/bin/env python3
"""
Repository for AI scores data access.
"""
from typing import Optional, Dict, Any, List
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from base_repository import BaseRepository, DB_PATH

class AIScoresRepository(BaseRepository):
    """Repository for AI scores database operations."""

    def __init__(self, db_path: str = DB_PATH):
        super().__init__(db_path)

    def get_ai_scores_by_company_id(self, company_id: int) -> Optional[Dict[str, Any]]:
        """Get AI scores for a company."""
        query = "SELECT * FROM ai_scores WHERE company_id = ?"
        return self.execute_single(query, (company_id,))

    def get_ai_scores_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get AI scores for a ticker."""
        query = """
            SELECT ais.* FROM ai_scores ais
            JOIN companies c ON ais.company_id = c.id
            WHERE c.ticker = ?
        """
        return self.execute_single(query, (ticker.upper(),))

    def create_or_update_ai_scores(self, company_id: int, scores: Dict[str, Any]) -> bool:
        """Create or update AI scores for a company."""
        # Check if scores exist
        existing = self.get_ai_scores_by_company_id(company_id)

        if existing:
            # Update existing
            set_clauses = [f"{key} = ?" for key in scores.keys()]
            values = list(scores.values()) + [company_id]

            query = f"""
                UPDATE ai_scores
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
                INSERT INTO ai_scores (company_id, {', '.join(columns)}, last_updated)
                VALUES (?, {placeholders}, CURRENT_TIMESTAMP)
            """
            return self.execute_insert(query, [company_id] + values) > 0

    def get_all_ai_scores(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all AI scores with company information."""
        query = """
            SELECT ais.*, c.ticker, c.company_name
            FROM ai_scores ais
            JOIN companies c ON ais.company_id = c.id
            ORDER BY ais.total_score_percentile_rank DESC
        """
        if limit:
            query += " LIMIT ? OFFSET ?"
            return self.execute_query(query, (limit, offset))
        return self.execute_query(query)

    def get_ai_scores_count(self) -> int:
        """Get total count of companies with AI scores."""
        query = "SELECT COUNT(*) as count FROM ai_scores"
        result = self.execute_single(query)
        return result['count'] if result else 0

    def delete_ai_scores(self, company_id: int) -> bool:
        """Delete AI scores for a company."""
        query = "DELETE FROM ai_scores WHERE company_id = ?"
        return self.execute_update(query, (company_id,)) > 0