#!/usr/bin/env python3
"""
Repository for adjusted PE data access.
"""
from typing import Optional, Dict, Any, Tuple
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from base_repository import BaseRepository, DB_PATH

class AdjustedPERepository(BaseRepository):
    """Repository for adjusted PE calculations database operations."""

    def __init__(self, db_path: str = DB_PATH):
        super().__init__(db_path)

    def get_adjusted_pe_by_company_id(self, company_id: int) -> Optional[Dict[str, Any]]:
        """Get adjusted PE data for a company."""
        query = "SELECT * FROM adjusted_pe_calculations WHERE company_id = ?"
        return self.execute_single(query, (company_id,))

    def get_adjusted_pe_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get adjusted PE data for a ticker."""
        query = """
            SELECT ap.* FROM adjusted_pe_calculations ap
            JOIN companies c ON ap.company_id = c.id
            WHERE c.ticker = ?
        """
        return self.execute_single(query, (ticker.upper(),))

    def upsert_adjusted_pe(self, ticker: str, breakdown: Dict[str, Any], ratio: float, timestamp: str) -> bool:
        """Insert or update adjusted PE data."""
        # Get company_id
        query = "SELECT id FROM companies WHERE ticker = ?"
        company = self.execute_single(query, (ticker.upper(),))
        if not company:
            return False

        company_id = company['id']

        # Get existing columns in the table to filter the breakdown dictionary
        col_query = "PRAGMA table_info(adjusted_pe_calculations)"
        columns_info = self.execute_query(col_query)
        table_columns = [col['name'] for col in columns_info if col['name'] != 'company_id']

        # Prepare data for insert/update
        data = {}
        import json
        for key, value in breakdown.items():
            if key in table_columns:
                if isinstance(value, list):
                    data[key] = json.dumps(value)
                else:
                    data[key] = value
        
        data['adjusted_pe_ratio'] = ratio
        data['last_updated'] = timestamp

        # Check if exists
        existing = self.get_adjusted_pe_by_company_id(company_id)

        if existing:
            # Update
            set_clauses = [f"{key} = ?" for key in data.keys()]
            values = list(data.values()) + [company_id]

            query = f"""
                UPDATE adjusted_pe_calculations
                SET {', '.join(set_clauses)}
                WHERE company_id = ?
            """
            return self.execute_update(query, tuple(values)) > 0
        else:
            # Insert
            columns = list(data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            values = list(data.values())

            query = f"""
                INSERT INTO adjusted_pe_calculations (company_id, {', '.join(columns)})
                VALUES (?, {placeholders})
            """
            return self.execute_insert(query, [company_id] + values) > 0

    def get_adjusted_pe_ratio_only(self, ticker: str) -> Optional[float]:
        """Get just the adjusted PE ratio for a ticker."""
        result = self.get_adjusted_pe_by_ticker(ticker)
        return result['adjusted_pe_ratio'] if result else None

    def get_adjusted_pe_with_breakdown(self, ticker: str) -> Tuple[Optional[float], Optional[Dict[str, Any]]]:
        """Get adjusted PE ratio and full breakdown."""
        result = self.get_adjusted_pe_by_ticker(ticker)
        if result:
            ratio = result.pop('adjusted_pe_ratio')
            return ratio, result
        return None, None

    def delete_adjusted_pe(self, company_id: int) -> bool:
        """Delete adjusted PE data for a company."""
        query = "DELETE FROM adjusted_pe_calculations WHERE company_id = ?"
        return self.execute_update(query, (company_id,)) > 0