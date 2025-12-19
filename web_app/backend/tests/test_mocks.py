import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add the project root to the path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from web_app.backend.data.quickfs_client import calculate_adjusted_pe_with_breakdown

def test_calculate_adjusted_pe_with_mocks():
    """Test adjusted PE calculation by mocking yfinance."""
    # Mock quarterly data - needs 20 quarters for median tax rate calculation
    # We provide 21 quarters to satisfy the range(len-1, min_quarters-1, -1) loop
    sample_quarterly = {
        'operating_income': [100] * 21,
        'cfo_da': [10] * 21,
        'capex': [20] * 21,
        'income_tax': [20] * 21,
        'pretax_income': [100] * 21,
        'enterprise_value': [4000] * 21,
        'market_cap': [3000] * 21,
        'period': ['2023Q1'] * 21,
        'shares_basic': [100] * 21
    }
    
    # Mock get_updated_enterprise_value_with_breakdown to avoid yfinance call
    with patch('web_app.backend.data.quickfs_client.get_updated_enterprise_value_with_breakdown') as mock_ev:
        mock_ev.return_value = {
            'updated_ev': 5000,
            'quickfs_ev': 4000,
            'quickfs_market_cap': 3000,
            'updated_market_cap': 4000,
            'ev_difference': 1000,
            'share_count': 100,
            'current_price': 40
        }
        
        ratio, breakdown = calculate_adjusted_pe_with_breakdown(sample_quarterly, ticker="AAPL")
        
        # Calculation:
        # TTM OI = 400
        # TTM D&A = 40
        # TTM CapEx = 80
        # Adjustment: Since |DA| (40) is NOT > |CapEx| (80), adjustment = 0
        # Adjusted OI = 400 + 0 = 400
        # Tax Rate = 20 / 100 = 20%
        # Adjusted OI After Tax = 400 * (1 - 0.2) = 320
        # Updated EV = 5000 (from mock)
        # Ratio = 5000 / 320 = 15.625
        
        assert round(ratio, 2) == 15.62
        assert breakdown['ttm_operating_income'] == 400
        assert breakdown['adjustment'] == 0
        assert breakdown['adjusted_oi_after_tax'] == 320
        assert breakdown['updated_ev'] == 5000

def test_calculate_adjusted_pe_no_data():
    """Test handling of missing data."""
    # Missing operating_income
    sample_incomplete = {
        'depreciation_and_amortization': [10, 10, 10, 10],
        'period': ['2023Q1', '2023Q2', '2023Q3', '2023Q4']
    }
    
    result = calculate_adjusted_pe_with_breakdown(sample_incomplete, ticker="TEST")
    assert result is None
