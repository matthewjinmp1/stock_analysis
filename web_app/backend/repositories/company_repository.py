#!/usr/bin/env python3
"""
Repository for company data access.
"""
from typing import Optional, Dict, Any, List
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from base_repository import BaseRepository, DB_PATH

class CompanyRepository(BaseRepository):
    """Repository for company-related database operations."""

    def __init__(self, db_path: str = DB_PATH):
        super().__init__(db_path)

    def get_company_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get company by ticker symbol."""
        query = """
            SELECT c.*, ta.ticker as primary_ticker
            FROM companies c
            LEFT JOIN ticker_aliases ta ON c.id = ta.company_id AND ta.is_primary = 1
            WHERE c.ticker = ?
        """
        return self.execute_single(query, (ticker.upper(),))

    def get_company_by_id(self, company_id: int) -> Optional[Dict[str, Any]]:
        """Get company by ID."""
        query = """
            SELECT c.*, ta.ticker as primary_ticker
            FROM companies c
            LEFT JOIN ticker_aliases ta ON c.id = ta.company_id AND ta.is_primary = 1
            WHERE c.id = ?
        """
        return self.execute_single(query, (company_id,))

    def get_all_companies(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all companies with optional pagination."""
        query = """
            SELECT c.*, ta.ticker as primary_ticker
            FROM companies c
            LEFT JOIN ticker_aliases ta ON c.id = ta.company_id AND ta.is_primary = 1
            ORDER BY c.ticker
        """
        if limit:
            query += " LIMIT ? OFFSET ?"
            return self.execute_query(query, (limit, offset))
        return self.execute_query(query)

    def search_companies(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search companies by ticker or company name using prefix matching."""
        query = """
            SELECT c.*, ta.ticker as primary_ticker
            FROM companies c
            LEFT JOIN ticker_aliases ta ON c.id = ta.company_id AND ta.is_primary = 1
            WHERE c.ticker LIKE ? OR UPPER(c.company_name) LIKE ?
            ORDER BY c.ticker
            LIMIT ?
        """
        search_pattern = f"{search_term.upper()}%"
        return self.execute_query(query, (search_pattern, search_pattern, limit))

    def create_company(self, ticker: str, company_name: str, exchange: str = None,
                      sector: str = None, industry: str = None) -> int:
        """Create a new company."""
        query = """
            INSERT INTO companies (ticker, company_name, exchange, sector, industry)
            VALUES (?, ?, ?, ?, ?)
        """
        company_id = self.execute_insert(query, (ticker.upper(), company_name, exchange, sector, industry))

        # Create primary ticker alias
        self.execute_update("""
            INSERT INTO ticker_aliases (company_id, ticker, is_primary)
            VALUES (?, ?, ?)
        """, (company_id, ticker.upper(), True))

        return company_id

    def update_company(self, company_id: int, **updates) -> bool:
        """Update company information."""
        if not updates:
            return False

        set_clauses = [f"{key} = ?" for key in updates.keys()]
        values = list(updates.values()) + [company_id]

        query = f"""
            UPDATE companies
            SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        return self.execute_update(query, tuple(values)) > 0

    def get_company_tickers(self, company_id: int) -> List[str]:
        """Get all ticker aliases for a company."""
        query = "SELECT ticker FROM ticker_aliases WHERE company_id = ? ORDER BY is_primary DESC"
        results = self.execute_query(query, (company_id,))
        return [row['ticker'] for row in results]

    def add_ticker_alias(self, company_id: int, ticker: str, is_primary: bool = False) -> bool:
        """Add a ticker alias for a company."""
        # If this is primary, unset other primaries first
        if is_primary:
            self.execute_update("""
                UPDATE ticker_aliases SET is_primary = 0 WHERE company_id = ?
            """, (company_id,))

        query = """
            INSERT INTO ticker_aliases (company_id, ticker, is_primary)
            VALUES (?, ?, ?)
        """
        return self.execute_insert(query, (company_id, ticker.upper(), is_primary)) > 0