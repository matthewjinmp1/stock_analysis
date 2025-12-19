import pytest
from unittest.mock import MagicMock, patch
from web_app.backend.services.peers_service import PeersService

@pytest.fixture
def mock_repos():
    peers_repo = MagicMock()
    data_repo = MagicMock()
    # Mock repos within data_repo
    data_repo.financial_scores_repo = MagicMock()
    data_repo.company_repo = MagicMock()
    data_repo.adjusted_pe_repo = MagicMock()
    return peers_repo, data_repo

@pytest.fixture
def peers_service(mock_repos):
    peers_repo, data_repo = mock_repos
    # Patch AdjustedPERepository and AdjustedPEService during init
    with patch('web_app.backend.services.peers_service.AdjustedPERepository'), \
         patch('web_app.backend.services.peers_service.AdjustedPEService'):
        return PeersService(peers_repo, data_repo)

def test_get_peers_ticker_not_found(peers_service, mock_repos):
    peers_repo, data_repo = mock_repos
    data_repo.get_complete_data.return_value = None
    
    result = peers_service.get_peers("INVALID")
    
    assert result['success'] is False
    assert 'not found' in result['message']
    data_repo.get_complete_data.assert_called_with("INVALID")

def test_get_peers_no_analysis(peers_service, mock_repos):
    peers_repo, data_repo = mock_repos
    data_repo.get_complete_data.return_value = {'symbol': 'AAPL'}
    peers_repo.get_peer_analysis.return_value = []
    
    result = peers_service.get_peers("AAPL")
    
    assert result['success'] is False
    assert 'No peer analysis found' in result['message']

def test_get_peers_success(peers_service, mock_repos):
    peers_repo, data_repo = mock_repos
    data_repo.get_complete_data.return_value = {
        'symbol': 'AAPL',
        'company_name': 'Apple Inc',
        'total_score_percentile_rank': 90,
        'financial_total_percentile': 85,
        'short_float': 1.5
    }
    peers_repo.get_peer_analysis.return_value = [{
        'peers': [{'ticker': 'MSFT', 'name': 'Microsoft'}],
        'analysis_timestamp': '2023-01-01',
        'token_usage': {},
        'estimated_cost_cents': 0.1
    }]
    
    # Mock _get_ticker_data to avoid complex nested mocks for now
    with patch.object(peers_service, '_get_ticker_data') as mock_get_data:
        mock_get_data.side_effect = [
            {'ticker': 'AAPL', 'company_name': 'Apple Inc'},
            {'ticker': 'MSFT', 'company_name': 'Microsoft'}
        ]
        
        result = peers_service.get_peers("AAPL")
        
        assert result['success'] is True
        assert result['main_ticker']['ticker'] == 'AAPL'
        assert len(result['peers']) == 1
        assert result['peers'][0]['ticker'] == 'MSFT'

def test_find_peers_ticker_not_found(peers_service, mock_repos):
    peers_repo, data_repo = mock_repos
    data_repo.get_complete_data.return_value = None
    
    result = peers_service.find_peers("INVALID")
    
    assert result['success'] is False
    assert 'not found' in result['message']

@patch('os.path.exists')
def test_find_peers_functionality_not_available(mock_exists, peers_service, mock_repos):
    peers_repo, data_repo = mock_repos
    data_repo.get_complete_data.return_value = {'symbol': 'AAPL', 'company_name': 'Apple'}
    mock_exists.return_value = False
    
    result = peers_service.find_peers("AAPL")
    
    assert result['success'] is False
    assert 'functionality not available' in result['message']

def test_get_ticker_data_exists(peers_service, mock_repos):
    peers_repo, data_repo = mock_repos
    data_repo.get_complete_data.return_value = {
        'symbol': 'AAPL',
        'company_name': 'Apple Inc',
        'total_score_percentile_rank': 90,
        'financial_total_percentile': 85,
        'short_float': 1.5,
        'adjusted_pe_ratio': 25.0
    }
    
    data_repo.financial_scores_repo.get_financial_scores_by_ticker.return_value = {'total_percentile': 85}
    
    result = peers_service._get_ticker_data("AAPL")
    
    assert result['ticker'] == 'AAPL'
    assert result['adjusted_pe_ratio'] == 25.0
    assert result['total_score_percentile_rank'] == 90

def test_get_ticker_data_not_exists(peers_service, mock_repos):
    peers_repo, data_repo = mock_repos
    data_repo.get_complete_data.return_value = None
    
    with patch.object(peers_service, '_fetch_short_interest_for_unknown_ticker') as mock_fetch:
        mock_fetch.return_value = "2.0%"
        result = peers_service._get_ticker_data("UNKNOWN")
        
        assert result['ticker'] == 'UNKNOWN'
        assert result['short_float'] == "2.0%"
        assert result['adjusted_pe_unavailable'] is True

def test_get_ticker_data_trigger_pe_calc(peers_service, mock_repos):
    peers_repo, data_repo = mock_repos
    # Company exists but PE ratio is missing
    data_repo.get_complete_data.return_value = {
        'symbol': 'AAPL',
        'adjusted_pe_ratio': None
    }
    data_repo.adjusted_pe_repo.get_adjusted_pe_by_ticker.return_value = None
    
    with patch('threading.Thread') as mock_thread:
        result = peers_service._get_ticker_data("AAPL")
        assert result['adjusted_pe_ratio'] is None
        # Should have triggered background calculation
        assert mock_thread.called

def test_fetch_short_interest_for_unknown_ticker(peers_service):
    with patch('os.chdir'), \
         patch('os.getcwd'), \
         patch('web_app.backend.services.peers_service.scrape_ticker_short_interest') as mock_scrape:
        
        # In case it's None due to import failure in some environments
        if mock_scrape is None:
            pytest.skip("scrape_ticker_short_interest not available")
            
        mock_scrape.return_value = {'short_float': '5.0%'}
        result = peers_service._fetch_short_interest_for_unknown_ticker("AAPL")
        assert result == '5.0%'

def test_find_peers_ai_logic(peers_service):
    # This tests the _find_peers_ai internal method
    mock_grok = MagicMock()
    mock_grok.simple_query_with_tokens.return_value = ("Peer1|P1; Peer2|P2; Peer3|NONE", {'total_tokens': 50})
    
    # Patch where they are imported in the module
    with patch('web_app.backend.services.peers_service.GrokClient', return_value=mock_grok), \
         patch('web_app.backend.services.peers_service.XAI_API_KEY', 'test-key'):
        
        peers, error, tokens, elapsed = peers_service._find_peers_ai("AAPL", "Apple")
        
        assert len(peers) == 3
        assert peers[0]['ticker'] == 'P1'
        assert peers[2]['ticker'] is None
        assert tokens['total_tokens'] == 50
        assert error is None
