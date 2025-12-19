#!/usr/bin/env python3
"""
Watchlist service for watchlist-related business logic.
"""
from typing import List, Dict, Any
import sys
import os
import threading
from datetime import datetime, timedelta, timezone

# Add the web_app directory to the path for imports
web_app_dir = os.path.dirname(os.path.dirname(__file__))
if web_app_dir not in sys.path:
    sys.path.insert(0, web_app_dir)

# Import from the absolute path relative to web_app
try:
    from repositories.watchlist_repository import WatchlistRepository
    from repositories.data_repository import DataRepository
    from repositories.adjusted_pe_repository import AdjustedPERepository
    from services.adjusted_pe_service import AdjustedPEService
except ImportError:
    # Fallback for different environments
    from ..repositories.watchlist_repository import WatchlistRepository
    from ..repositories.data_repository import DataRepository
    from ..repositories.adjusted_pe_repository import AdjustedPERepository
    from .adjusted_pe_service import AdjustedPEService

class WatchlistService:
    """Service for watchlist business logic."""
    GROWTH_RETRY_DELAY = timedelta(hours=1)

    def __init__(self, watchlist_repo: WatchlistRepository, data_repo: DataRepository):
        self.watchlist_repo = watchlist_repo
        self.data_repo = data_repo
        # Initialize adjusted PE components
        self.adjusted_pe_repo = AdjustedPERepository()
        self.adjusted_pe_service = AdjustedPEService(self.adjusted_pe_repo)
        # Track ongoing fetches to prevent duplicate triggers
        self.ongoing_fetches = {
            'pe': set(),
            'growth': set(),
            'short_interest': set()
        }

    def get_watchlist(self) -> Dict[str, Any]:
        """Get complete watchlist with enriched data."""
        watchlist_data = self.watchlist_repo.get_watchlist()

        # Enrich with additional calculated fields
        for item in watchlist_data:
            ticker = item.get('ticker')
            if not ticker:
                continue

            # 1. Handle Growth and 2y Annualized Growth
            current_growth = item.get('current_year_growth')
            next_growth = item.get('next_year_growth')
            growth_status = item.get('growth_status')
            growth_last_updated = item.get('growth_last_updated')
            item['growth_loading'] = False
            item['two_year_annualized_growth'] = None # Default
            
            if current_growth is not None and next_growth is not None:
                item['two_year_annualized_growth'] = self.data_repo.calculate_two_year_annualized_growth(
                    current_growth, next_growth
                )
            elif ticker in self.ongoing_fetches['growth']:
                item['growth_loading'] = True
            else:
                if self._should_retry_growth_fetch(growth_status, growth_last_updated):
                    item['growth_loading'] = True
                    self._trigger_growth_fetch(ticker)
                else:
                    item['growth_loading'] = False

            # 2. Handle Adjusted PE
            adjusted_pe_ratio = item.get('adjusted_pe_ratio')
            pe_status = item.get('pe_status')
            item['adjusted_pe_loading'] = False
            
            if adjusted_pe_ratio is not None:
                item['adjusted_pe_loading'] = False
            elif ticker in self.ongoing_fetches['pe']:
                item['adjusted_pe_loading'] = True
            elif pe_status in ['no_data', 'error', 'api_key_missing', 'no_quarterly_data', 'calculation_failed']:
                item['adjusted_pe_loading'] = False
            else:
                # Missing and not already fetching or failed - trigger calculation
                item['adjusted_pe_loading'] = True
                self._trigger_pe_calculation(ticker)

            # 3. Handle Short Interest
            short_float = item.get('short_float')
            si_status = item.get('short_interest_status')
            item['short_interest_loading'] = False
            
            if short_float is not None:
                item['short_interest_loading'] = False
            elif ticker in self.ongoing_fetches['short_interest']:
                item['short_interest_loading'] = True
            elif si_status in ['no_data', 'error']:
                item['short_interest_loading'] = False
            else:
                item['short_interest_loading'] = True
                self._trigger_short_interest_fetch(ticker)

            # 4. Handle Financial Scores loading (placeholder)
            item['financial_loading'] = False

            # 5. Calculate 2y Forward PE (Derived)
            adjusted_pe_ratio = item.get('adjusted_pe_ratio')
            two_year_growth = item.get('two_year_annualized_growth')

            if adjusted_pe_ratio is not None and two_year_growth is not None:
                try:
                    growth_multiplier = (1 + (two_year_growth / 100)) ** 2
                    if growth_multiplier != 0:
                        item['two_year_forward_pe'] = adjusted_pe_ratio / growth_multiplier
                    else:
                        item['two_year_forward_pe'] = None
                except (TypeError, ValueError, ZeroDivisionError):
                    item['two_year_forward_pe'] = None
            else:
                item['two_year_forward_pe'] = None

        return {
            'success': True,
            'watchlist': watchlist_data
        }

    def _should_retry_growth_fetch(self, growth_status: str, growth_last_updated: str) -> bool:
        """Determine whether we should attempt to re-fetch growth data."""
        if growth_status == 'no_data':
            return False
        if growth_status == 'error':
            if not growth_last_updated:
                return True
            try:
                last_updated_dt = datetime.fromisoformat(growth_last_updated)
            except ValueError:
                return True
            if last_updated_dt.tzinfo is None:
                last_updated_dt = last_updated_dt.replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) - last_updated_dt > self.GROWTH_RETRY_DELAY
        return True

    def _trigger_pe_calculation(self, ticker: str) -> None:
        """Trigger background calculation of adjusted PE."""
        if ticker in self.ongoing_fetches['pe']:
            return
            
        self.ongoing_fetches['pe'].add(ticker)
        try:
            def calculate_pe_background():
                try:
                    self.adjusted_pe_service.calculate_and_store_adjusted_pe(ticker)
                except Exception:
                    pass
                finally:
                    self.ongoing_fetches['pe'].discard(ticker)
            thread = threading.Thread(target=calculate_pe_background, daemon=True)
            thread.start()
        except Exception:
            self.ongoing_fetches['pe'].discard(ticker)

    def _trigger_growth_fetch(self, ticker: str) -> None:
        """Trigger background fetch of growth data."""
        if ticker in self.ongoing_fetches['growth']:
            return
            
        self.ongoing_fetches['growth'].add(ticker)
        try:
            from utils.yfinance.yfinance_revenue_growth import get_revenue_growth_estimates
            def fetch_growth_background():
                try:
                    data, error = get_revenue_growth_estimates(ticker)
                    if data:
                        self.data_repo.upsert_growth_estimates(
                            ticker, 
                            data.get('current_year_growth'), 
                            data.get('next_year_growth'),
                            status='success'
                        )
                    else:
                        self.data_repo.upsert_growth_estimates(ticker, None, None, status='no_data')
                except Exception:
                    self.data_repo.upsert_growth_estimates(ticker, None, None, status='error')
                finally:
                    self.ongoing_fetches['growth'].discard(ticker)
            thread = threading.Thread(target=fetch_growth_background, daemon=True)
            thread.start()
        except Exception:
            self.ongoing_fetches['growth'].discard(ticker)

    def _trigger_short_interest_fetch(self, ticker: str) -> None:
        """Trigger background fetch of short interest data."""
        if ticker in self.ongoing_fetches['short_interest']:
            return
            
        self.ongoing_fetches['short_interest'].add(ticker)
        try:
            from data.short_interest_client import get_short_interest_for_ticker
            def fetch_short_interest_background():
                try:
                    result = get_short_interest_for_ticker(ticker)
                    if result:
                        self.data_repo.upsert_short_interest(ticker, result.get('short_float'), status='success')
                    else:
                        self.data_repo.upsert_short_interest(ticker, None, status='no_data')
                except Exception:
                    self.data_repo.upsert_short_interest(ticker, None, status='error')
                finally:
                    self.ongoing_fetches['short_interest'].discard(ticker)
            thread = threading.Thread(target=fetch_short_interest_background, daemon=True)
            thread.start()
        except Exception:
            self.ongoing_fetches['short_interest'].discard(ticker)

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
            # Trigger background fetches for all missing metrics immediately
            self._trigger_pe_calculation(ticker)
            self._trigger_growth_fetch(ticker)
            self._trigger_short_interest_fetch(ticker)
            
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

    def calculate_missing_adjusted_pe_for_all(self) -> None:
        """Calculate adjusted PE for all watchlist stocks that don't have it."""
        watchlist_tickers = self.get_watchlist_tickers()

        for ticker in watchlist_tickers:
            try:
                # Check if we already have data
                existing = self.adjusted_pe_repo.get_adjusted_pe_by_ticker(ticker)
                if existing and existing.get('adjusted_pe_ratio') is not None:
                    continue  # Already have data

                # Check if it previously failed permanently
                if existing and existing.get('calculation_status') in ['no_data', 'error', 'api_key_missing']:
                    continue  # Don't retry permanent failures

                # Calculate in background
                def calculate_pe_background(ticker=ticker):
                    try:
                        self.adjusted_pe_service.calculate_and_store_adjusted_pe(ticker)
                        print(f"Calculated adjusted PE for {ticker}")
                    except Exception as e:
                        print(f"Failed to calculate adjusted PE for {ticker}: {e}")

                thread = threading.Thread(target=calculate_pe_background, daemon=True)
                thread.start()

            except Exception as e:
                print(f"Error checking/calculating adjusted PE for {ticker}: {e}")
