#!/usr/bin/env python3
"""
Data service for business logic related to stock data.
"""
from typing import Optional, Dict, Any, List, Tuple
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from repositories.data_repository import DataRepository
from repositories.watchlist_repository import WatchlistRepository
import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from score_calculator import calculate_total_score, SCORE_DEFINITIONS, SCORE_WEIGHTS
from datetime import datetime

class DataService:
    """Service for stock data business logic."""

    def __init__(self, data_repo: DataRepository, watchlist_repo: WatchlistRepository):
        self.data_repo = data_repo
        self.watchlist_repo = watchlist_repo

    def get_complete_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get complete data for a ticker with business logic applied."""
        data = self.data_repo.get_complete_data(ticker)
        if not data:
            return None

        # Add watchlist status
        data['in_watchlist'] = self.watchlist_repo.is_in_watchlist(ticker)

        # Calculate two-year annualized growth if growth data exists
        current_year_growth = data.get('current_year_growth')
        next_year_growth = data.get('next_year_growth')
        if current_year_growth is not None and next_year_growth is not None:
            data['two_year_annualized_growth'] = self.data_repo.calculate_two_year_annualized_growth(
                current_year_growth, next_year_growth
            )

        return data

    def search_ticker(self, query: str) -> Dict[str, Any]:
        """Search for ticker with validation and business logic."""
        ticker, match_type = self._find_best_match(query)

        if not ticker:
            return {
                'success': False,
                'query': query,
                'message': f'No tickers found starting with "{query}". Please enter a valid ticker prefix (e.g., AAPL).'
            }

        try:
            data = self.get_complete_data(ticker)
            if not data:
                return {
                    'success': False,
                    'query': query,
                    'message': f'Could not fetch data for "{ticker}". Please check that the ticker is valid.'
                }

            # Add financial scores summary
            financial_scores = self.data_repo.financial_scores_repo.get_financial_scores_by_ticker(ticker)
            if financial_scores:
                data['financial_total_percentile'] = financial_scores.get('total_percentile')
                data['financial_total_rank'] = financial_scores.get('total_rank')

            return {
                'success': True,
                'ticker': ticker,
                'query': query,
                'match_type': match_type,
                'data': data,
                'in_watchlist': data.get('in_watchlist', False)
            }
        except Exception as e:
            return {
                'success': False,
                'query': query,
                'message': f'Error fetching data for "{ticker}": {str(e)}'
            }

    def get_search_suggestions(self, query: str) -> Dict[str, Any]:
        """Get search suggestions with business logic."""
        if not query or len(query.strip()) < 1:
            return {'success': False, 'message': 'Query too short'}

        query_upper = query.strip().upper()
        suggestions = self.data_repo.search_tickers(query_upper, limit=10)

        return {
            'success': True,
            'query': query,
            'suggestions': suggestions,
            'count': len(suggestions)
        }

    def get_metrics_data(self, ticker: str) -> Dict[str, Any]:
        """Get detailed metrics breakdown for a ticker."""
        data = self.data_repo.get_complete_data(ticker)
        if not data:
            return {'success': False, 'message': f'No data found for "{ticker}"'}

        # Get score data for detailed breakdown
        score_data = {k: v for k, v in data.items() if k in SCORE_DEFINITIONS}
        if not score_data or not any(score_data.values()):
            return {'success': False, 'message': f'No score data found for "{ticker}"'}

        metrics_detail = []
        total_score = 0.0
        max_score = sum(SCORE_WEIGHTS.get(key, 1.0) for key in SCORE_DEFINITIONS) * 10

        for score_key in SCORE_DEFINITIONS:
            score_def = SCORE_DEFINITIONS[score_key]
            weight = SCORE_WEIGHTS.get(score_key, 1.0)
            try:
                score_value = float(score_data.get(score_key, 0) or 0)
                adjusted_value = 10 - score_value if score_def['is_reverse'] else score_value
                contribution = adjusted_value * weight
                total_score += contribution

                # Get display name
                display_name = self._get_metric_display_name(score_key)

                metrics_detail.append({
                    'key': score_key,
                    'name': display_name,
                    'raw_score': score_value,
                    'adjusted_score': adjusted_value,
                    'weight': weight,
                    'contribution': contribution,
                    'is_reverse': score_def['is_reverse'],
                    'percentage': (contribution / max_score) * 100 if max_score > 0 else 0
                })
            except (ValueError, TypeError):
                continue

        metrics_detail.sort(key=lambda x: x['contribution'], reverse=True)

        return {
            'success': True,
            'ticker': ticker,
            'company_name': data.get('company_name'),
            'metrics': metrics_detail,
            'total_score_percentage': data.get('total_score_percentage'),
            'total_score_percentile_rank': data.get('total_score_percentile_rank'),
            'max_score': max_score
        }

    def get_financial_metrics_data(self, ticker: str) -> Dict[str, Any]:
        """Get financial metrics data for a ticker."""
        financial_scores = self.data_repo.financial_scores_repo.get_financial_scores_by_ticker(ticker)
        if not financial_scores:
            data = self.data_repo.get_complete_data(ticker)
            return {
                'success': False,
                'company_name': data.get('company_name') if data else None,
                'message': f'No financial score data found for "{ticker}"'
            }

        from ..financial_scorer import METRICS

        metrics_detail = []
        for metric in METRICS:
            value = financial_scores.get(metric.key)
            if value is not None:
                metrics_detail.append({
                    'key': metric.key,
                    'name': metric.display_name,
                    'description': metric.description,
                    'value': value,
                    'rank': financial_scores.get(f'{metric.key}_rank'),
                    'percentile': financial_scores.get(f'{metric.key}_percentile'),
                    'sort_descending': metric.sort_descending,
                })

        metrics_detail.sort(key=lambda x: x['percentile'] if x['percentile'] is not None else 0, reverse=True)

        return {
            'success': True,
            'ticker': ticker,
            'company_name': financial_scores.get('company_name'),
            'metrics': metrics_detail,
            'total_percentile': financial_scores.get('total_percentile'),
            'total_rank': financial_scores.get('total_rank')
        }

    def _find_best_match(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """Find best ticker match using prefix matching."""
        query_upper = query.strip().upper()

        # First try exact ticker match
        company = self.data_repo.company_repo.get_company_by_ticker(query_upper)
        if company:
            # Check if we have cached data for this ticker
            data = self.data_repo.get_complete_data(query_upper)
            if data:
                return query_upper, 'ticker'
            else:
                return query_upper, 'ticker_not_cached'

        # Try company name prefix match
        companies = self.data_repo.company_repo.search_companies(query_upper, limit=1)
        if companies:
            ticker = companies[0]['ticker']
            data = self.data_repo.get_complete_data(ticker)
            if data:
                return ticker, 'company'
            else:
                return ticker, 'ticker_not_cached'

        return None, None

    def _get_metric_display_name(self, key: str) -> str:
        """Get display name for a metric key."""
        display_names = {
            'moat_score': 'Economic Moat',
            'barriers_score': 'Barriers to Entry',
            'disruption_risk': 'Disruption Risk',
            'switching_cost': 'Switching Cost',
            'brand_strength': 'Brand Strength',
            'competition_intensity': 'Competition Intensity',
            'network_effect': 'Network Effect',
            'product_differentiation': 'Product Differentiation',
            'innovativeness_score': 'Innovativeness',
            'growth_opportunity': 'Growth Opportunity',
            'riskiness_score': 'Business Risk',
            'pricing_power': 'Pricing Power',
            'ambition_score': 'Ambition',
            'bargaining_power_of_customers': 'Customer Bargaining Power',
            'bargaining_power_of_suppliers': 'Supplier Bargaining Power',
            'product_quality_score': 'Product Quality',
            'culture_employee_satisfaction_score': 'Employee Satisfaction',
            'trailblazer_score': 'Market Leadership',
            'management_quality_score': 'Management Quality',
            'ai_knowledge_score': 'AI Scoring Confidence',
            'size_well_known_score': 'Size',
            'ethical_healthy_environmental_score': 'Ethical, Healthy, Environmental',
            'long_term_orientation_score': 'Long Term Focus',
        }
        return display_names.get(key, key.replace('_', ' ').title())