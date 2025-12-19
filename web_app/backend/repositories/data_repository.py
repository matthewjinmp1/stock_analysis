#!/usr/bin/env python3
"""
Combined data repository for complete company data access.
"""
from typing import Optional, Dict, Any, List
from .base_repository import BaseRepository
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from base_repository import DB_PATH
from company_repository import CompanyRepository
from ai_scores_repository import AIScoresRepository
from financial_scores_repository import FinancialScoresRepository
from adjusted_pe_repository import AdjustedPERepository

class DataRepository(BaseRepository):
    """Repository for accessing complete company data across all tables."""

    def __init__(self, db_path: str = DB_PATH):
        super().__init__(db_path)
        self.company_repo = CompanyRepository(db_path)
        self.ai_scores_repo = AIScoresRepository(db_path)
        self.financial_scores_repo = FinancialScoresRepository(db_path)
        self.adjusted_pe_repo = AdjustedPERepository(db_path)
        self.watchlist_repo = None  # Will be set by service layer

    def get_complete_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get complete data for a ticker (equivalent to old get_complete_data function)."""
        # Get company info
        company = self.company_repo.get_company_by_ticker(ticker)
        if not company:
            return None

        company_id = company['id']

        # Get AI scores
        ai_scores = self.ai_scores_repo.get_ai_scores_by_company_id(company_id)

        # Get financial scores
        financial_scores = self.financial_scores_repo.get_financial_scores_by_company_id(company_id)

        # Get adjusted PE
        adjusted_pe = self.adjusted_pe_repo.get_adjusted_pe_by_company_id(company_id)

        # Get growth estimates
        growth_query = "SELECT * FROM growth_estimates WHERE company_id = ?"
        growth_data = self.execute_single(growth_query, (company_id,))

        # Get short interest
        short_interest_query = "SELECT * FROM short_interest WHERE company_id = ?"
        short_interest_data = self.execute_single(short_interest_query, (company_id,))

        # Combine all data
        result = {
            'ticker': company['ticker'],
            'company_name': company['company_name'],
            'exchange': company.get('exchange'),
            'sector': company.get('sector'),
            'industry': company.get('industry'),
            'last_updated': company.get('updated_at') or ai_scores.get('last_updated') if ai_scores else None,
        }

        # Add AI scores
        if ai_scores:
            result.update(ai_scores)
            result.pop('company_id', None)
            result.pop('last_updated', None)

        # Add financial scores
        if financial_scores:
            result['financial_total_percentile'] = financial_scores.get('total_percentile')
            result['financial_total_rank'] = financial_scores.get('total_rank')

        # Add adjusted PE
        if adjusted_pe:
            result['adjusted_pe_ratio'] = adjusted_pe.get('adjusted_pe_ratio')
            result['current_year_growth'] = growth_data.get('current_year_growth') if growth_data else None
            result['next_year_growth'] = growth_data.get('next_year_growth') if growth_data else None

        # Add short interest
        if short_interest_data:
            result['short_float'] = short_interest_data.get('short_float')
            result['short_interest_scraped_at'] = short_interest_data.get('scraped_at')

        return result

    def get_ui_cache_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get data in the format expected by the UI cache view."""
        query = "SELECT * FROM ui_cache WHERE ticker = ?"
        return self.execute_single(query, (ticker.upper(),))

    def get_scores_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get data in the format expected by the scores view."""
        query = "SELECT * FROM scores WHERE ticker = ?"
        return self.execute_single(query, (ticker.upper(),))

    def get_all_tickers(self) -> List[str]:
        """Get all available tickers."""
        query = "SELECT ticker FROM companies ORDER BY ticker"
        results = self.execute_query(query)
        return [row['ticker'] for row in results]

    def search_tickers(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search tickers and company names using prefix matching."""
        search_pattern = f"{query.upper()}%"
        sql_query = """
            SELECT
                c.ticker,
                c.company_name,
                CASE WHEN c.ticker LIKE ? THEN 'ticker' ELSE 'company' END as match_type,
                CASE WHEN c.ticker LIKE ? THEN 1 ELSE 2 END as priority
            FROM companies c
            WHERE c.ticker LIKE ? OR UPPER(c.company_name) LIKE ?
            ORDER BY priority, c.ticker
            LIMIT ?
        """
        return self.execute_query(sql_query, (search_pattern, search_pattern, search_pattern, search_pattern, limit))

    def get_all_scores(self) -> List[Dict[str, Any]]:
        """Get all AI scores with company info."""
        return self.ai_scores_repo.get_all_ai_scores()

    def upsert_growth_estimates(self, ticker: str, current_year: Optional[float], next_year: Optional[float], status: Optional[str] = None) -> bool:
        """Insert or update growth estimates for a ticker."""
        company = self.company_repo.get_company_by_ticker(ticker)
        if not company:
            return False

        company_id = company['id']
        from datetime import datetime
        timestamp = datetime.now().isoformat()

        # Check if exists
        query = "SELECT company_id FROM growth_estimates WHERE company_id = ?"
        existing = self.execute_single(query, (company_id,))

        if existing:
            query = """
                UPDATE growth_estimates 
                SET current_year_growth = ?, next_year_growth = ?, last_updated = ?, calculation_status = ?
                WHERE company_id = ?
            """
            return self.execute_update(query, (current_year, next_year, timestamp, status, company_id)) > 0
        else:
            query = """
                INSERT INTO growth_estimates (company_id, current_year_growth, next_year_growth, last_updated, calculation_status)
                VALUES (?, ?, ?, ?, ?)
            """
            return self.execute_insert(query, (company_id, current_year, next_year, timestamp, status)) > 0

    def upsert_short_interest(self, ticker: str, short_float: Optional[str], status: Optional[str] = None) -> bool:
        """Insert or update short interest for a ticker."""
        company = self.company_repo.get_company_by_ticker(ticker)
        if not company:
            return False

        company_id = company['id']
        from datetime import datetime
        timestamp = datetime.now().isoformat()

        # Check if exists
        query = "SELECT company_id FROM short_interest WHERE company_id = ?"
        existing = self.execute_single(query, (company_id,))

        if existing:
            query = """
                UPDATE short_interest 
                SET short_float = ?, scraped_at = ?, last_updated = ?, calculation_status = ?
                WHERE company_id = ?
            """
            return self.execute_update(query, (short_float, timestamp, timestamp, status, company_id)) > 0
        else:
            query = """
                INSERT INTO short_interest (company_id, short_float, scraped_at, last_updated, calculation_status)
                VALUES (?, ?, ?, ?, ?)
            """
            return self.execute_insert(query, (company_id, short_float, timestamp, timestamp, status)) > 0

    def calculate_two_year_annualized_growth(self, current_year_growth: float, next_year_growth: float) -> Optional[float]:
        """Calculate 2-year annualized growth rate."""
        try:
            if current_year_growth is None or next_year_growth is None:
                return None

            # Convert percentages to decimal multipliers
            current_multiplier = 1 + (current_year_growth / 100)
            next_multiplier = 1 + (next_year_growth / 100)

            # Calculate compound growth over 2 years
            total_growth = current_multiplier * next_multiplier

            # Calculate annualized growth rate (CAGR)
            cagr = (total_growth ** 0.5) - 1

            # Convert back to percentage
            return cagr * 100

        except (TypeError, ValueError, ZeroDivisionError):
            return None