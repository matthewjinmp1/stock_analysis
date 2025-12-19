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

from web_app.backend.services.data_service import DataService

@pytest.fixture
def mock_data_repo():
    repo = MagicMock()
    # Mock repos within data_repo
    repo.financial_scores_repo = MagicMock()
    repo.company_repo = MagicMock()
    return repo

@pytest.fixture
def mock_watchlist_repo():
    return MagicMock()

@pytest.fixture
def service(mock_data_repo, mock_watchlist_repo):
    return DataService(mock_data_repo, mock_watchlist_repo)

def test_get_complete_data_success(service, mock_data_repo, mock_watchlist_repo):
    ticker = "AAPL"
    mock_data = {
        'ticker': 'AAPL',
        'current_year_growth': 10.0,
        'next_year_growth': 10.0
    }
    mock_data_repo.get_complete_data.return_value = mock_data
    mock_watchlist_repo.is_in_watchlist.return_value = True
    mock_data_repo.calculate_two_year_annualized_growth.return_value = 10.0
    
    result = service.get_complete_data(ticker)
    
    assert result['ticker'] == 'AAPL'
    assert result['in_watchlist'] is True
    assert result['two_year_annualized_growth'] == 10.0
    mock_data_repo.get_complete_data.assert_called_once_with(ticker)

def test_search_ticker_exact_match(service, mock_data_repo):
    query = "AAPL"
    mock_company = {'ticker': 'AAPL', 'company_name': 'Apple'}
    mock_data_repo.company_repo.get_company_by_ticker.return_value = mock_company
    mock_data_repo.get_complete_data.return_value = {'ticker': 'AAPL'}
    
    result = service.search_ticker(query)
    
    assert result['success'] is True
    assert result['ticker'] == 'AAPL'
    assert result['match_type'] == 'ticker'

def test_get_search_suggestions(service, mock_data_repo):
    query = "AA"
    mock_suggestions = [
        {'ticker': 'AA', 'company_name': 'Alcoa'},
        {'ticker': 'AAPL', 'company_name': 'Apple'}
    ]
    mock_data_repo.search_tickers.return_value = mock_suggestions
    
    result = service.get_search_suggestions(query)
    
    assert result['success'] is True
    assert len(result['suggestions']) == 2
    assert result['count'] == 2

def test_get_metrics_data_success(service, mock_data_repo):
    ticker = "AAPL"
    mock_data = {
        'ticker': 'AAPL',
        'company_name': 'Apple',
        'moat_score': 8,
        'disruption_risk': 2
    }
    mock_data_repo.get_complete_data.return_value = mock_data
    
    result = service.get_metrics_data(ticker)
    
    assert result['success'] is True
    assert result['ticker'] == 'AAPL'
    assert len(result['metrics']) > 0
    # moat_score should be in metrics
    moat_metric = next(m for m in result['metrics'] if m['key'] == 'moat_score')
    assert moat_metric['raw_score'] == 8
