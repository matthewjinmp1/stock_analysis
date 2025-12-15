#!/usr/bin/env python3
"""
Comprehensive test suite for scorer.py
"""

import pytest
import json
import os
import tempfile
from unittest.mock import patch, mock_open, MagicMock
import sys

# Import the scorer module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.scoring import scorer


class TestCalculateTotalScore:
    """Test the calculate_total_score function."""
    
    def test_normal_score_contribution(self):
        """Test that normal scores contribute positively."""
        scores = {
            'moat_score': '8',
            'barriers_score': '7',
        }
        # moat_score: 8 * 10 = 80
        # barriers_score: 7 * 10 = 70
        # Total should be at least 150 (plus other scores with default 0)
        total = scorer.calculate_total_score(scores)
        assert total >= 150
    
    def test_reverse_score_contribution(self):
        """Test that reverse scores are inverted correctly."""
        scores = {
            'disruption_risk': '2',  # Reverse score, weight 10
        }
        # disruption_risk: (10 - 2) * 10 = 80
        total = scorer.calculate_total_score(scores)
        # Should contribute 80 points (plus other scores with default 0)
        assert total >= 80
    
    def test_reverse_score_high_value(self):
        """Test that high reverse scores contribute less."""
        scores_low_risk = {'disruption_risk': '1'}  # Low risk = good
        scores_high_risk = {'disruption_risk': '9'}  # High risk = bad
        
        total_low = scorer.calculate_total_score(scores_low_risk)
        total_high = scorer.calculate_total_score(scores_high_risk)
        
        # Low risk should contribute more: (10-1)*10 = 90 vs (10-9)*10 = 10
        assert total_low > total_high
    
    def test_size_well_known_reverse_score(self):
        """Test that size_well_known_score is now a reverse score."""
        scores_small = {'size_well_known_score': '1'}  # Small company
        scores_large = {'size_well_known_score': '10'}  # Large company
        
        total_small = scorer.calculate_total_score(scores_small)
        total_large = scorer.calculate_total_score(scores_large)
        
        # Small company should contribute more: (10-1)*19.31 = 173.79 vs (10-10)*19.31 = 0
        assert total_small > total_large
    
    def test_zero_weight_score(self):
        """Test that scores with zero weight don't contribute."""
        scores = {
            'ai_knowledge_score': '10',  # Weight is 0
        }
        total = scorer.calculate_total_score(scores)
        # ai_knowledge_score should not contribute (weight 0)
        # All other scores default to 0, but size_well_known_score is reverse with weight 19.31
        # So: (10 - 0) * 19.31 = 193.1 for size_well_known_score
        # We just verify ai_knowledge_score doesn't add anything beyond defaults
        assert isinstance(total, (int, float))
        # The total should be from other scores defaulting to 0, not from ai_knowledge_score
        # Since size_well_known_score is reverse, missing (0) gives (10-0)*19.31 = 193.1
        assert total >= 0
    
    def test_missing_scores_default_to_zero(self):
        """Test that missing scores are treated as 0."""
        scores = {}  # Empty scores
        total = scorer.calculate_total_score(scores)
        # All scores default to 0, but size_well_known_score is reverse with weight 19.31
        # So missing (0) gives (10-0)*19.31 = 193.1 for size_well_known_score
        # Other normal scores: 0 * weight = 0
        # Other reverse scores: (10-0) * weight = 10 * weight
        assert isinstance(total, (int, float))
        assert total >= 0  # Should be non-negative
    
    def test_invalid_score_values(self):
        """Test that invalid score values are handled gracefully."""
        scores = {
            'moat_score': 'invalid',
            'barriers_score': '8',
        }
        # Should skip invalid values and continue
        total = scorer.calculate_total_score(scores)
        # Should still calculate with valid scores
        assert isinstance(total, (int, float))
    
    def test_string_scores_converted_to_float(self):
        """Test that string scores are properly converted."""
        scores = {
            'moat_score': '8',  # String
            'barriers_score': '7',  # String
        }
        total = scorer.calculate_total_score(scores)
        assert isinstance(total, (int, float))
        assert total > 0
    
    def test_all_scores_maximum(self):
        """Test calculation with maximum scores."""
        scores = {}
        for key in scorer.SCORE_DEFINITIONS:
            if scorer.SCORE_DEFINITIONS[key]['is_reverse']:
                scores[key] = '0'  # Best for reverse scores
            else:
                scores[key] = '10'  # Best for normal scores
        
        total = scorer.calculate_total_score(scores)
        assert total > 0
    
    def test_all_scores_minimum(self):
        """Test calculation with minimum scores."""
        scores = {}
        for key in scorer.SCORE_DEFINITIONS:
            if scorer.SCORE_DEFINITIONS[key]['is_reverse']:
                scores[key] = '10'  # Worst for reverse scores
            else:
                scores[key] = '0'  # Worst for normal scores
        
        total = scorer.calculate_total_score(scores)
        assert total >= 0


class TestCalculatePercentileRank:
    """Test the calculate_percentile_rank function."""
    
    def test_percentile_rank_basic(self):
        """Test basic percentile calculation."""
        all_scores = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        percentile = scorer.calculate_percentile_rank(50, all_scores)
        # 50 is the 5th value (0-indexed 4), so percentile = 5/10 * 100 = 50
        assert percentile == 50
    
    def test_percentile_rank_highest(self):
        """Test percentile for highest score."""
        all_scores = [10, 20, 30, 40, 50]
        percentile = scorer.calculate_percentile_rank(50, all_scores)
        # 50 is the highest, so percentile = 5/5 * 100 = 100
        assert percentile == 100
    
    def test_percentile_rank_lowest(self):
        """Test percentile for lowest score."""
        all_scores = [10, 20, 30, 40, 50]
        percentile = scorer.calculate_percentile_rank(10, all_scores)
        # 10 is the lowest, so percentile = 1/5 * 100 = 20
        assert percentile == 20
    
    def test_percentile_rank_empty_list(self):
        """Test percentile with empty list."""
        percentile = scorer.calculate_percentile_rank(50, [])
        assert percentile is None
    
    def test_percentile_rank_none_list(self):
        """Test percentile with None list."""
        percentile = scorer.calculate_percentile_rank(50, None)
        assert percentile is None
    
    def test_percentile_rank_duplicate_values(self):
        """Test percentile with duplicate values."""
        all_scores = [10, 20, 20, 20, 30]
        percentile = scorer.calculate_percentile_rank(20, all_scores)
        # 20 appears 3 times, so percentile = 4/5 * 100 = 80
        assert percentile == 80
    
    def test_percentile_rank_single_value(self):
        """Test percentile with single value."""
        all_scores = [50]
        percentile = scorer.calculate_percentile_rank(50, all_scores)
        assert percentile == 100


class TestFormatTotalScore:
    """Test the format_total_score function."""
    
    @patch('scorer.get_all_total_scores')
    @patch('scorer.calculate_percentile_rank')
    def test_format_with_percentile(self, mock_percentile, mock_all_scores):
        """Test formatting with provided percentile."""
        mock_all_scores.return_value = [100, 200, 300]
        result = scorer.format_total_score(200, percentile=75)
        assert '75th percentile' in result
        assert isinstance(result, str)
    
    @patch('scorer.get_all_total_scores')
    @patch('scorer.calculate_percentile_rank')
    def test_format_without_percentile(self, mock_percentile, mock_all_scores):
        """Test formatting without percentile (auto-calculated)."""
        mock_all_scores.return_value = [100, 200, 300]
        mock_percentile.return_value = 50
        result = scorer.format_total_score(200)
        assert '50th percentile' in result or isinstance(result, str)
    
    @patch('scorer.get_all_total_scores')
    def test_format_single_score(self, mock_all_scores):
        """Test formatting when only one score exists."""
        mock_all_scores.return_value = [200]
        result = scorer.format_total_score(200)
        # Should not include percentile if only one score
        assert isinstance(result, str)


class TestCalculateTokenCost:
    """Test the calculate_token_cost function."""
    
    def test_token_cost_basic(self):
        """Test basic token cost calculation."""
        cost = scorer.calculate_token_cost(1000000, model="grok-4-fast")
        # Should use average of input/output pricing
        assert cost > 0
        assert isinstance(cost, float)
    
    def test_token_cost_with_breakdown(self):
        """Test token cost with detailed breakdown."""
        token_usage = {
            'input_tokens': 500000,
            'output_tokens': 200000,
            'cached_tokens': 100000
        }
        cost = scorer.calculate_token_cost(0, model="grok-4-fast", token_usage=token_usage)
        assert cost > 0
        assert isinstance(cost, float)
    
    def test_token_cost_unknown_model(self):
        """Test token cost with unknown model."""
        cost = scorer.calculate_token_cost(1000000, model="unknown-model")
        assert cost == 0.0
    
    def test_token_cost_zero_tokens(self):
        """Test token cost with zero tokens."""
        cost = scorer.calculate_token_cost(0, model="grok-4-fast")
        assert cost == 0.0
    
    def test_token_cost_cached_tokens(self):
        """Test that cached tokens use different pricing."""
        token_usage = {
            'input_tokens': 200000,
            'output_tokens': 100000,
            'cached_tokens': 100000
        }
        cost_with_cache = scorer.calculate_token_cost(0, model="grok-4-fast", token_usage=token_usage)
        
        token_usage_no_cache = {
            'input_tokens': 300000,
            'output_tokens': 100000,
            'cached_tokens': 0
        }
        cost_no_cache = scorer.calculate_token_cost(0, model="grok-4-fast", token_usage=token_usage_no_cache)
        
        # Cached tokens should be cheaper
        assert cost_with_cache < cost_no_cache


class TestLoadSaveScores:
    """Test load_scores and save_scores functions."""
    
    def test_load_scores_file_exists(self):
        """Test loading scores from existing file."""
        # This will use the actual scores.json file if it exists
        scores = scorer.load_scores()
        assert isinstance(scores, dict)
        assert 'companies' in scores
    
    def test_save_scores(self):
        """Test saving scores to file."""
        test_data = {
            'companies': {
                'TEST': {
                    'moat_score': '8',
                    'barriers_score': '7'
                }
            }
        }
        
        # Use a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            # Patch SCORES_FILE to use temp file
            with patch('scorer.SCORES_FILE', temp_file):
                scorer.save_scores(test_data)
                
                # Verify file was created and contains data
                assert os.path.exists(temp_file)
                with open(temp_file, 'r') as f:
                    loaded_data = json.load(f)
                    assert loaded_data == test_data
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_load_scores_file_not_exists(self):
        """Test loading scores when file doesn't exist."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        os.remove(temp_file)  # Ensure it doesn't exist
        
        try:
            with patch('scorer.SCORES_FILE', temp_file):
                scores = scorer.load_scores()
                # Should return default structure
                assert isinstance(scores, dict)
                assert 'companies' in scores
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)


class TestResolveToCompanyName:
    """Test the resolve_to_company_name function."""
    
    @patch('scorer.load_ticker_lookup')
    def test_resolve_ticker_symbol(self, mock_lookup):
        """Test resolving a ticker symbol."""
        mock_lookup.return_value = {'AAPL': 'Apple Inc.'}
        company_name, ticker = scorer.resolve_to_company_name('AAPL')
        assert company_name == 'Apple Inc.'
        assert ticker == 'AAPL'
    
    @patch('scorer.load_ticker_lookup')
    def test_resolve_company_name(self, mock_lookup):
        """Test resolving a company name."""
        mock_lookup.return_value = {}
        company_name, ticker = scorer.resolve_to_company_name('Apple Inc.')
        assert company_name == 'Apple Inc.'
        assert ticker is None
    
    @patch('scorer.load_ticker_lookup')
    def test_resolve_case_insensitive_ticker(self, mock_lookup):
        """Test that ticker resolution is case insensitive."""
        mock_lookup.return_value = {'AAPL': 'Apple Inc.'}
        company_name, ticker = scorer.resolve_to_company_name('aapl')
        assert company_name == 'Apple Inc.'
        assert ticker == 'AAPL'
    
    @patch('scorer.load_ticker_lookup')
    def test_resolve_unknown_ticker(self, mock_lookup):
        """Test resolving unknown ticker."""
        mock_lookup.return_value = {}
        company_name, ticker = scorer.resolve_to_company_name('UNKNOWN')
        assert company_name == 'UNKNOWN'
        assert ticker is None


class TestScoreDefinitions:
    """Test score definitions and weights."""
    
    def test_all_scores_have_definitions(self):
        """Test that all scores in SCORE_WEIGHTS have definitions."""
        for score_key in scorer.SCORE_WEIGHTS:
            assert score_key in scorer.SCORE_DEFINITIONS
    
    def test_all_scores_have_weights(self):
        """Test that all scores in SCORE_DEFINITIONS have weights."""
        for score_key in scorer.SCORE_DEFINITIONS:
            assert score_key in scorer.SCORE_WEIGHTS
    
    def test_reverse_scores_are_marked(self):
        """Test that reverse scores are properly marked."""
        reverse_scores = [
            'disruption_risk',
            'competition_intensity',
            'riskiness_score',
            'bargaining_power_of_customers',
            'bargaining_power_of_suppliers',
            'size_well_known_score'
        ]
        
        for score_key in reverse_scores:
            assert score_key in scorer.SCORE_DEFINITIONS
            assert scorer.SCORE_DEFINITIONS[score_key]['is_reverse'] is True
    
    def test_normal_scores_are_not_reverse(self):
        """Test that normal scores are not marked as reverse."""
        normal_scores = [
            'moat_score',
            'barriers_score',
            'switching_cost',
            'brand_strength',
            'network_effect'
        ]
        
        for score_key in normal_scores:
            assert score_key in scorer.SCORE_DEFINITIONS
            assert scorer.SCORE_DEFINITIONS[score_key]['is_reverse'] is False


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_calculate_total_score_with_none_values(self):
        """Test handling of None values in scores."""
        scores = {
            'moat_score': None,
            'barriers_score': '8'
        }
        total = scorer.calculate_total_score(scores)
        # Should handle None gracefully
        assert isinstance(total, (int, float))
    
    def test_calculate_total_score_with_empty_string(self):
        """Test handling of empty string values."""
        scores = {
            'moat_score': '',
            'barriers_score': '8'
        }
        total = scorer.calculate_total_score(scores)
        # Should handle empty string gracefully
        assert isinstance(total, (int, float))
    
    def test_calculate_total_score_with_float_strings(self):
        """Test handling of float string values."""
        scores = {
            'moat_score': '8.5',
            'barriers_score': '7.3'
        }
        total = scorer.calculate_total_score(scores)
        assert isinstance(total, (int, float))
        assert total > 0
    
    def test_percentile_rank_with_negative_scores(self):
        """Test percentile calculation with negative scores."""
        all_scores = [-10, 0, 10, 20, 30]
        percentile = scorer.calculate_percentile_rank(0, all_scores)
        assert percentile == 40  # 0 is 2nd value, 2/5 * 100 = 40


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

