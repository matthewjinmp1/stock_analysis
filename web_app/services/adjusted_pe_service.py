#!/usr/bin/env python3
"""
Adjusted PE calculation service.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from repositories.adjusted_pe_repository import AdjustedPERepository
from typing import Optional, Dict, Any

class AdjustedPEService:
    """Service for adjusted PE calculations."""

    def __init__(self, adjusted_pe_repo: AdjustedPERepository):
        self.adjusted_pe_repo = adjusted_pe_repo

    def calculate_and_store_adjusted_pe(self, ticker: str) -> bool:
        """
        Calculate adjusted PE for a ticker and store the results.

        Args:
            ticker: Stock ticker symbol

        Returns:
            bool: True if calculation and storage successful, False otherwise
        """
        try:
            # Import the calculation function
            from web_app.get_quickfs_data import get_all_data, calculate_adjusted_pe_ratio

            # Get financial data from QuickFS
            data = get_all_data(ticker)
            if not data:
                print(f"No financial data available for {ticker}")
                return False

            # Extract quarterly data
            quarterly = data.get("financials", {}).get("quarterly", {})
            if not quarterly:
                print(f"No quarterly data available for {ticker}")
                return False

            # Calculate adjusted PE
            adjusted_pe = calculate_adjusted_pe_ratio(quarterly, ticker=ticker, verbose=False)
            if adjusted_pe is None:
                print(f"Could not calculate adjusted PE for {ticker}")
                return False

            # Store the result (we'll store minimal breakdown data for now)
            breakdown = {
                'ttm_operating_income': None,  # We don't have detailed breakdown without more work
                'ttm_da': None,
                'ttm_capex': None,
                'adjustment': None,
                'adjusted_operating_income': None,
                'median_tax_rate': None,
                'adjusted_oi_after_tax': None,
                'quickfs_ev': None,
                'quickfs_market_cap': None,
                'updated_ev': None,
                'share_count': None,
                'current_price': None,
                'ev_difference': None,
                'updated_market_cap': None,
            }

            import datetime
            timestamp = datetime.datetime.now().isoformat()

            success = self.adjusted_pe_repo.upsert_adjusted_pe(
                ticker=ticker,
                breakdown=breakdown,
                ratio=float(adjusted_pe),
                timestamp=timestamp
            )

            if success:
                print(f"Successfully calculated and stored adjusted PE for {ticker}: {adjusted_pe:.2f}")
                return True
            else:
                print(f"Failed to store adjusted PE for {ticker}")
                return False

        except Exception as e:
            print(f"Error calculating adjusted PE for {ticker}: {e}")
            return False

    def ensure_adjusted_pe_exists(self, ticker: str) -> Optional[float]:
        """
        Ensure adjusted PE data exists for a ticker, calculating it if necessary.

        Args:
            ticker: Stock ticker symbol

        Returns:
            float: The adjusted PE ratio, or None if unavailable
        """
        # Check if we already have the data
        existing = self.adjusted_pe_repo.get_adjusted_pe_by_ticker(ticker)
        if existing and existing.get('adjusted_pe_ratio') is not None:
            return existing['adjusted_pe_ratio']

        # Calculate and store it
        if self.calculate_and_store_adjusted_pe(ticker):
            # Try to get it again
            updated = self.adjusted_pe_repo.get_adjusted_pe_by_ticker(ticker)
            if updated:
                return updated.get('adjusted_pe_ratio')

        return None