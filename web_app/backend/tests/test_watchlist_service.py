import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
from web_app.backend.services.watchlist_service import WatchlistService

@pytest.fixture
def mock_repos():
    watchlist_repo = MagicMock()
    data_repo = MagicMock()
    return watchlist_repo, data_repo

@pytest.fixture
def watchlist_service(mock_repos):
    watchlist_repo, data_repo = mock_repos
    return WatchlistService(watchlist_repo, data_repo)

def test_get_watchlist_enriched(watchlist_service, mock_repos):
    watchlist_repo, data_repo = mock_repos
    mock_data = [
        {
            'ticker': 'AAPL',
            'current_year_growth': 10.0,
            'next_year_growth': 10.0,
            'adjusted_pe_ratio': 20.0,
            'short_float': '1.5%',
            'adjusted_oi_after_tax': 100.0,
            'updated_ev': 2000.0
        }
    ]
    watchlist_repo.get_watchlist.return_value = mock_data
    data_repo.calculate_two_year_annualized_growth.return_value = 10.0
    
    result = watchlist_service.get_watchlist()
    
    assert result['success'] is True
    item = result['watchlist'][0]
    assert item['two_year_annualized_growth'] == 10.0
    assert item['two_year_forward_pe'] is not None
    # growth_multiplier = (1 + 0.1)^2 = 1.21
    # forward_PE = 20 / 1.21 = 16.5289...
    assert abs(item['two_year_forward_pe'] - 16.5289) < 0.001

def test_forward_pe_can_use_quickfs_fallback(watchlist_service, mock_repos):
    watchlist_repo, data_repo = mock_repos
    mock_data = [
        {
            'ticker': 'FDS',
            'current_year_growth': 5.2,
            'next_year_growth': 5.3,
            'adjusted_pe_ratio': 16.0,
            'adjusted_oi_after_tax': None,
            'updated_ev': None,
            'quickfs_ev': 4800.0,
            'growth_status': 'success'
        }
    ]
    watchlist_repo.get_watchlist.return_value = mock_data
    data_repo.calculate_two_year_annualized_growth.return_value = 5.2

    result = watchlist_service.get_watchlist()
    item = result['watchlist'][0]

    assert item['two_year_forward_pe'] is not None
    assert isinstance(item['two_year_forward_pe'], float)

def test_growth_retry_triggered_for_stale_error(watchlist_service, mock_repos):
    watchlist_repo, _ = mock_repos
    stale_timestamp = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    watchlist_repo.get_watchlist.return_value = [
        {
            'ticker': 'FDS',
            'current_year_growth': None,
            'next_year_growth': None,
            'growth_status': 'error',
            'growth_last_updated': stale_timestamp
        }
    ]

    with patch.object(watchlist_service, '_trigger_growth_fetch') as mock_growth:
        result = watchlist_service.get_watchlist()
        item = result['watchlist'][0]
        mock_growth.assert_called_once_with('FDS')
        assert item['growth_loading'] is True

def test_growth_no_retry_for_recent_error(watchlist_service, mock_repos):
    watchlist_repo, _ = mock_repos
    recent_timestamp = datetime.now(timezone.utc).isoformat()
    watchlist_repo.get_watchlist.return_value = [
        {
            'ticker': 'FDS',
            'current_year_growth': None,
            'next_year_growth': None,
            'growth_status': 'error',
            'growth_last_updated': recent_timestamp
        }
    ]

    with patch.object(watchlist_service, '_trigger_growth_fetch') as mock_growth:
        result = watchlist_service.get_watchlist()
        item = result['watchlist'][0]
        mock_growth.assert_not_called()
        assert item['growth_loading'] is False

def test_add_to_watchlist_success(watchlist_service, mock_repos):
    watchlist_repo, data_repo = mock_repos
    data_repo.get_complete_data.return_value = {'symbol': 'AAPL'}
    watchlist_repo.is_in_watchlist.return_value = False
    watchlist_repo.add_to_watchlist.return_value = True
    
    with patch.object(watchlist_service, '_trigger_pe_calculation') as mock_pe, \
         patch.object(watchlist_service, '_trigger_growth_fetch') as mock_growth, \
         patch.object(watchlist_service, '_trigger_short_interest_fetch') as mock_si:
        
        result = watchlist_service.add_to_watchlist("AAPL")
        
        assert result['success'] is True
        assert 'added to watchlist' in result['message']
        mock_pe.assert_called_once_with("AAPL")
        mock_growth.assert_called_once_with("AAPL")
        mock_si.assert_called_once_with("AAPL")

def test_add_to_watchlist_already_exists(watchlist_service, mock_repos):
    watchlist_repo, data_repo = mock_repos
    data_repo.get_complete_data.return_value = {'symbol': 'AAPL'}
    watchlist_repo.is_in_watchlist.return_value = True
    
    result = watchlist_service.add_to_watchlist("AAPL")
    
    assert result['success'] is False
    assert 'already in watchlist' in result['message']

def test_remove_from_watchlist(watchlist_service, mock_repos):
    watchlist_repo, _ = mock_repos
    watchlist_repo.remove_from_watchlist.return_value = True
    
    result = watchlist_service.remove_from_watchlist("AAPL")
    assert result['success'] is True
    
    watchlist_repo.remove_from_watchlist.return_value = False
    result = watchlist_service.remove_from_watchlist("INVALID")
    assert result['success'] is False

def test_calculate_missing_adjusted_pe_for_all(watchlist_service, mock_repos):
    watchlist_repo, _ = mock_repos
    watchlist_service.get_watchlist_tickers = MagicMock(return_value=["AAPL", "MSFT"])
    watchlist_service.adjusted_pe_repo.get_adjusted_pe_by_ticker = MagicMock(side_effect=[
        {'adjusted_pe_ratio': 25.0}, # AAPL has it
        None # MSFT missing
    ])
    
    with patch('threading.Thread') as mock_thread:
        watchlist_service.calculate_missing_adjusted_pe_for_all()
        # Should only trigger for MSFT
        assert mock_thread.call_count == 1
