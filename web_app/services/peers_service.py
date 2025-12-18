#!/usr/bin/env python3
"""
Peers service for peer-related business logic.
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(__file__))

from repositories.peers_repository import PeersRepository
from repositories.data_repository import DataRepository
from repositories.adjusted_pe_repository import AdjustedPERepository
from services.adjusted_pe_service import AdjustedPEService
from typing import Optional, Dict, Any, List
import threading

class PeersService:
    """Service for peers business logic."""

    def __init__(self, peers_repo: PeersRepository, data_repo: DataRepository):
        self.peers_repo = peers_repo
        self.data_repo = data_repo
        self.adjusted_pe_repo = AdjustedPERepository()
        self.adjusted_pe_service = AdjustedPEService(self.adjusted_pe_repo)

    def get_peers(self, ticker: str) -> Dict[str, Any]:
        """
        Get peer data for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with peer data or error information
        """
        try:
            ticker = ticker.strip().upper()

            # Get company data to validate ticker exists
            company_data = self.data_repo.get_complete_data(ticker)
            if not company_data:
                return {
                    'success': False,
                    'message': f'Ticker "{ticker}" not found'
                }

            # Get peer analysis from database
            peer_analyses = self.peers_repo.get_peer_analysis(ticker, limit=1)

            if not peer_analyses:
                return {
                    'success': False,
                    'message': f'No peer analysis found for {ticker}. Try running "Find Peers" first.'
                }

            # Return the most recent analysis
            latest_analysis = peer_analyses[0]

            # Get current data for main ticker and peers
            main_ticker_data = self._get_ticker_data(ticker)

            peers_data = []
            for peer in latest_analysis['peers']:
                peer_ticker = peer.get('ticker')
                if peer_ticker:
                    peer_data = self._get_ticker_data(peer_ticker)
                    if peer_data:
                        peers_data.append(peer_data)
                    else:
                        # Peer exists in peer analysis but not in companies table
                        # Include with basic info and trigger data fetching
                        peers_data.append({
                            'ticker': peer_ticker,
                            'company_name': peer.get('name', peer_ticker),
                            'total_score_percentile_rank': None,
                            'financial_total_percentile': None,
                            'adjusted_pe_ratio': None,  # Will be fetched automatically
                            'short_float': None  # Will be fetched automatically
                        })
                else:
                    # Peer without ticker - just include basic info
                    peers_data.append({
                        'ticker': None,
                        'company_name': peer.get('name', ''),
                        'total_score_percentile_rank': None,
                        'financial_total_percentile': None,
                        'adjusted_pe_ratio': None,
                        'short_float': None
                    })

            return {
                'success': True,
                'main_ticker': main_ticker_data,
                'peers': peers_data,
                'analysis_timestamp': latest_analysis.get('analysis_timestamp'),
                'token_usage': latest_analysis.get('token_usage'),
                'estimated_cost_cents': latest_analysis.get('estimated_cost_cents')
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving peers: {str(e)}'
            }

    def find_peers(self, ticker: str) -> Dict[str, Any]:
        """
        Find peers for a ticker using AI.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with peer analysis results or error information
        """
        try:
            ticker = ticker.strip().upper()

            # Get company data to validate ticker exists
            company_data = self.data_repo.get_complete_data(ticker)
            if not company_data:
                return {
                    'success': False,
                    'message': f'Ticker "{ticker}" not found'
                }

            company_name = company_data.get('company_name', ticker)

            # Import and use the existing AI peer finding functionality
            try:
                peer_getter_path = os.path.join(os.path.dirname(__file__), '..', 'peers', 'peer_getter.py')
                if os.path.exists(peer_getter_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("peer_getter", peer_getter_path)
                    peer_getter = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(peer_getter)

                    # Create a modified version that returns the data instead of printing
                    peers_data, error, token_usage, elapsed_time = self._find_peers_ai(ticker, company_name)

                    if error:
                        return {
                            'success': False,
                            'message': f'AI peer finding failed: {error}'
                        }

                    if peers_data:
                        # Save to database
                        saved = self.peers_repo.save_peer_analysis(
                            ticker=ticker,
                            company_name=company_name,
                            peers=peers_data,
                            token_usage=token_usage,
                            estimated_cost_cents=token_usage.get('estimated_cost_cents') if token_usage else None
                        )

                        return {
                            'success': True,
                            'ticker': ticker,
                            'company_name': company_name,
                            'peers': peers_data,
                            'elapsed_time': elapsed_time,
                            'saved_to_db': saved,
                            'token_usage': token_usage
                        }
                    else:
                        return {
                            'success': False,
                            'message': 'No peers found by AI analysis'
                        }
                else:
                    return {
                        'success': False,
                        'message': 'Peer finding functionality not available'
                    }

            except ImportError as e:
                return {
                    'success': False,
                    'message': f'AI peer finding not available: {str(e)}'
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error finding peers: {str(e)}'
            }

    def _find_peers_ai(self, ticker: str, company_name: str):
        """
        Internal method to find peers using AI.
        Based on the existing peer_getter.py functionality.
        """
        try:
            # Import required modules
            from src.clients.grok_client import GrokClient
            from src.clients.openrouter_client import OpenRouterClient
            from config import XAI_API_KEY, OPENROUTER_KEY

            def get_api_client():
                if XAI_API_KEY:
                    return GrokClient(XAI_API_KEY)
                elif OPENROUTER_KEY:
                    return OpenRouterClient(OPENROUTER_KEY)
                else:
                    raise ValueError("No API key configured")

            def get_model_for_ticker(ticker):
                return "grok-4-1-fast-reasoning" if XAI_API_KEY else "anthropic/claude-3.5-sonnet"

            # Create AI prompt
            prompt = f"""You are analyzing companies to find the 10 most comparable companies to {company_name}.

Your task is to find the 10 MOST comparable companies to {company_name}.

Consider factors such as:
1. Industry and market segment similarity (MUST be in same or very similar industry)
2. Business model similarity
3. Product/service similarity
4. Market overlap and customer base similarity
5. Competitive dynamics (direct competitors)
6. Company size and scale (if relevant)

For each company, provide both the clean company name and its stock ticker symbol (if it has one).
Return ONLY a semicolon-separated list of exactly 10 entries, starting with the most comparable company first.
Each entry should be in format: "Company Name|Ticker" or "Company Name|NONE" if no ticker exists.

CRITICAL: Use semicolons (;) to separate entries, NOT commas.
IMPORTANT: Use ONLY the core company name without generic suffixes like Inc, Corp, Co, Ltd, LLC, Group, Holdings, Corporation, Incorporated, Limited, etc.
Examples: "Microsoft|MSFT", "Alphabet|GOOG", "Apple|AAPL", "Nike|NKE", "Meta|META".
For private companies or those without tickers, use "NONE" as the ticker.

Do not include explanations, ranking numbers, or any other text - just the 10 entries separated by semicolons in order from most to least comparable.

Example format: "Microsoft|MSFT; Alphabet|GOOG; Meta|META; Amazon|AMZN; Nvidia|NVDA; Intel|INTC; Advanced Micro Devices|AMD; Salesforce|CRM; Oracle|ORCL; Adobe|ADBE"

Return exactly 10 entries in ranked order, separated by semicolons, nothing else."""

            grok = get_api_client()
            model = get_model_for_ticker(ticker)
            start_time = time.time()
            response, token_usage = grok.simple_query_with_tokens(prompt, model=model)
            elapsed_time = time.time() - start_time

            entries = [entry.strip() for entry in response.strip().split(';') if entry.strip()]
            peers_data = []

            for entry in entries[:10]:
                if '|' in entry:
                    parts = entry.split('|', 1)
                    peers_data.append({
                        'name': parts[0].strip(),
                        'ticker': parts[1].strip() if parts[1].strip() != 'NONE' else None
                    })
                else:
                    peers_data.append({'name': entry, 'ticker': None})

            return peers_data, None, token_usage, elapsed_time

        except Exception as e:
            return None, str(e), None, 0

    def _get_ticker_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get ticker data including scores and metrics.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with ticker data or None if not found
        """
        try:
            data = self.data_repo.get_complete_data(ticker)
            if not data:
                # Ticker doesn't exist in companies table, but we still want to show it
                # Try to fetch basic short interest data
                short_float = self._fetch_short_interest_for_unknown_ticker(ticker)
                return {
                    'ticker': ticker,
                    'company_name': ticker,  # Use ticker as company name since we don't have it
                    'total_score_percentile_rank': None,
                    'financial_total_percentile': None,
                    'adjusted_pe_ratio': None,  # Can't calculate without company data
                    'short_float': short_float
                }

            # Add financial scores
            financial_scores = self.data_repo.financial_scores_repo.get_financial_scores_by_ticker(ticker)

            # Ensure adjusted PE data is available - try to fetch if missing
            adjusted_pe_ratio = data.get('adjusted_pe_ratio')
            if adjusted_pe_ratio is None:
                # Try to get it from the adjusted PE repository directly
                try:
                    pe_data = self.data_repo.adjusted_pe_repo.get_adjusted_pe_by_ticker(ticker)
                    if pe_data:
                        adjusted_pe_ratio = pe_data.get('adjusted_pe_ratio')
                    else:
                        # Trigger background calculation of adjusted PE
                        # This will calculate and store the data for future requests
                        try:
                            def calculate_pe_background():
                                try:
                                    self.adjusted_pe_service.calculate_and_store_adjusted_pe(ticker)
                                except Exception:
                                    pass  # Silently fail in background

                            # Start background calculation (don't wait for it)
                            thread = threading.Thread(target=calculate_pe_background, daemon=True)
                            thread.start()
                        except Exception:
                            pass  # Silently continue if background calculation fails
                except Exception:
                    pass  # Silently continue if we can't get PE data

            # Ensure short interest data is available - try to fetch if missing
            short_float = data.get('short_float')
            if short_float is None or short_float == '':
                # Try to fetch short interest data
                try:
                    # Import the short interest scraping function
                    from src.scrapers.get_short_interest import scrape_ticker_short_interest
                    # Import the current directory changing logic (from original ui_cache_db.py)
                    import os
                    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

                    # Change to project root and scrape
                    prev_cwd = os.getcwd()
                    os.chdir(PROJECT_ROOT)
                    try:
                        si_result = scrape_ticker_short_interest(ticker)
                        if si_result and si_result.get('short_float'):
                            short_float = si_result.get('short_float')
                            # Update the database with the new data
                            try:
                                # Update the short interest table
                                short_interest_data = {
                                    'company_id': None,  # Will be set by the update logic
                                    'short_float': si_result.get('short_float'),
                                    'scraped_at': si_result.get('scraped_at')
                                }
                                # Find company_id and update
                                company_id = self.data_repo.company_repo.get_company_by_ticker(ticker)
                                if company_id:
                                    company_id = company_id['id']
                                    # Update or insert short interest data
                                    # This is a simplified approach - ideally we'd use a proper repository method
                                    self.data_repo.execute_update('''
                                        INSERT OR REPLACE INTO short_interest (company_id, short_float, scraped_at, last_updated)
                                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                                    ''', (company_id, short_float, si_result.get('scraped_at')))
                            except Exception:
                                pass  # Silently fail if database update fails
                    finally:
                        os.chdir(prev_cwd)
                except Exception:
                    pass  # Silently continue if scraping fails

            return {
                'ticker': ticker,
                'company_name': data.get('company_name'),
                'total_score_percentile_rank': data.get('total_score_percentage'),  # This might be wrong - need to check
                'financial_total_percentile': financial_scores.get('total_percentile') if financial_scores else None,
                'adjusted_pe_ratio': adjusted_pe_ratio,
                'short_float': short_float
            }
        except Exception:
            return None

    def _fetch_short_interest_for_unknown_ticker(self, ticker: str) -> Optional[str]:
        """
        Try to fetch short interest data for a ticker that doesn't exist in our companies table.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Short interest string or None if not available
        """
        try:
            # Import the short interest scraping function
            from src.scrapers.get_short_interest import scrape_ticker_short_interest
            import os

            # Change to project root and scrape
            PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            prev_cwd = os.getcwd()
            os.chdir(PROJECT_ROOT)
            try:
                si_result = scrape_ticker_short_interest(ticker)
                if si_result and si_result.get('short_float'):
                    return si_result.get('short_float')
            finally:
                os.chdir(prev_cwd)
        except Exception:
            pass  # Silently fail

        return None