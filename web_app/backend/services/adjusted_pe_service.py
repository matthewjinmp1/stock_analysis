#!/usr/bin/env python3
"""
Adjusted PE calculation service.
"""
import sys
import os
from typing import Optional, Dict, Any

# Add the web_app directory to the path for imports
web_app_dir = os.path.dirname(os.path.dirname(__file__))
if web_app_dir not in sys.path:
    sys.path.insert(0, web_app_dir)

try:
    from repositories.adjusted_pe_repository import AdjustedPERepository
except ImportError:
    from ..repositories.adjusted_pe_repository import AdjustedPERepository

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
            from data.quickfs_client import get_all_data, calculate_adjusted_pe_with_breakdown

            # Get financial data from QuickFS
            data = get_all_data(ticker)
            if not data:
                print(f"No financial data available for {ticker}")
                self._store_calculation_status(ticker, 'no_data')
                return False

            # Extract quarterly data
            quarterly = data.get("financials", {}).get("quarterly", {})
            if not quarterly:
                print(f"No quarterly data available for {ticker}")
                self._store_calculation_status(ticker, 'no_quarterly_data')
                return False

            # Calculate adjusted PE with full breakdown
            result = calculate_adjusted_pe_with_breakdown(quarterly, ticker=ticker, verbose=False)
            if result is None:
                print(f"Could not calculate adjusted PE for {ticker}")
                self._store_calculation_status(ticker, 'calculation_failed')
                return False

            adjusted_pe, breakdown = result

            import datetime
            timestamp = datetime.datetime.now().isoformat()

            # Store the result with breakdown
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

        except RuntimeError as e:
            if "QuickFS API key not configured" in str(e):
                print(f"QuickFS API key not configured for {ticker}")
                self._store_calculation_status(ticker, 'api_key_missing')
                return False
            else:
                print(f"Runtime error calculating adjusted PE for {ticker}: {e}")
                self._store_calculation_status(ticker, 'error')
                return False
        except Exception as e:
            print(f"Error calculating adjusted PE for {ticker}: {e}")
            # Store failure status
            try:
                self._store_calculation_status(ticker, 'error')
            except:
                pass  # Don't let status storage failure crash the function
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

    def _store_calculation_status(self, ticker: str, status: str) -> None:
        """
        Store calculation status for a ticker when calculation fails.

        Args:
            ticker: Stock ticker symbol
            status: Status indicating why calculation failed
        """
        try:
            import datetime
            timestamp = datetime.datetime.now().isoformat()

            # Store a record with null ratio but with status info
            breakdown = {
                'calculation_status': status,
                'calculation_attempted_at': timestamp,
            }

            self.adjusted_pe_repo.upsert_adjusted_pe(
                ticker=ticker,
                breakdown=breakdown,
                ratio=None,  # No ratio available
                timestamp=timestamp
            )
        except Exception as e:
            print(f"Failed to store calculation status for {ticker}: {e}")
