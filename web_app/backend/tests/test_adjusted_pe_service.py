import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add the project root to the path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Add web_app to path
WEB_APP_ROOT = os.path.join(PROJECT_ROOT, 'web_app')
if WEB_APP_ROOT not in sys.path:
    sys.path.insert(0, WEB_APP_ROOT)

from web_app.backend.services.adjusted_pe_service import AdjustedPEService

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def service(mock_repo):
    return AdjustedPEService(mock_repo)

def test_calculate_and_store_adjusted_pe_success(service, mock_repo):
    ticker = "AAPL"
    mock_data = {"financials": {"quarterly": {"some": "data"}}}
    mock_result = (15.0, {"ttm_oi": 100})
    
    with patch('data.quickfs_client.get_all_data') as mock_get_all:
        with patch('data.quickfs_client.calculate_adjusted_pe_with_breakdown') as mock_calc:
            mock_get_all.return_value = mock_data
            mock_calc.return_value = mock_result
            mock_repo.upsert_adjusted_pe.return_value = True
            
            result = service.calculate_and_store_adjusted_pe(ticker)
            
            assert result is True
            mock_get_all.assert_called_once_with(ticker)
            mock_calc.assert_called_once()
            mock_repo.upsert_adjusted_pe.assert_called_once()

def test_calculate_and_store_adjusted_pe_no_data(service, mock_repo):
    ticker = "INVALID"
    
    with patch('data.quickfs_client.get_all_data') as mock_get_all:
        mock_get_all.return_value = None
        
        result = service.calculate_and_store_adjusted_pe(ticker)
        
        assert result is False
        mock_repo.upsert_adjusted_pe.assert_called_once()
        # Check that status was stored
        args, kwargs = mock_repo.upsert_adjusted_pe.call_args
        assert kwargs['breakdown']['calculation_status'] == 'no_data'

def test_ensure_adjusted_pe_exists_already_there(service, mock_repo):
    ticker = "AAPL"
    mock_repo.get_adjusted_pe_by_ticker.return_value = {'adjusted_pe_ratio': 15.0}
    
    result = service.ensure_adjusted_pe_exists(ticker)
    
    assert result == 15.0
    mock_repo.get_adjusted_pe_by_ticker.assert_called_once_with(ticker)
    # Should not call calculate_and_store_adjusted_pe
    with patch.object(AdjustedPEService, 'calculate_and_store_adjusted_pe') as mock_calc_method:
        service.ensure_adjusted_pe_exists(ticker)
        mock_calc_method.assert_not_called()

def test_calculate_and_store_adjusted_pe_runtime_error(service, mock_repo):
    ticker = "AAPL"
    
    with patch('data.quickfs_client.get_all_data') as mock_get_all:
        mock_get_all.side_effect = RuntimeError("QuickFS API key not configured")
        
        result = service.calculate_and_store_adjusted_pe(ticker)
        
        assert result is False
        # Check that status was stored correctly
        args, kwargs = mock_repo.upsert_adjusted_pe.call_args
        assert kwargs['breakdown']['calculation_status'] == 'api_key_missing'
