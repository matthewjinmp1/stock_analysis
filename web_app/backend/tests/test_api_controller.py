import pytest
from flask import Flask
from unittest.mock import MagicMock, patch
from web_app.backend.controllers.api_controller import ApiController

@pytest.fixture
def app():
    app = Flask(__name__)
    return app

@pytest.fixture
def mock_services():
    data_service = MagicMock()
    watchlist_service = MagicMock()
    return data_service, watchlist_service

@pytest.fixture
def api_controller(mock_services):
    data_service, watchlist_service = mock_services
    # Patch inside the module where it's used
    with patch('web_app.backend.controllers.api_controller.PeersRepository'), \
         patch('web_app.backend.controllers.api_controller.DataRepository'), \
         patch('web_app.backend.controllers.api_controller.PeersService'):
        return ApiController(data_service, watchlist_service)

def test_search_ticker(app, api_controller, mock_services):
    data_service, _ = mock_services
    data_service.search_ticker.return_value = {'success': True, 'data': 'result'}
    
    with app.app_context():
        response, status_code = api_controller.search_ticker("AAPL")
        assert status_code == 200
        assert response.json == {'success': True, 'data': 'result'}

def test_search_ticker_not_found(app, api_controller, mock_services):
    data_service, _ = mock_services
    data_service.search_ticker.return_value = {'success': False, 'message': 'not found'}
    
    with app.app_context():
        response, status_code = api_controller.search_ticker("INVALID")
        assert status_code == 404
        assert response.json == {'success': False, 'message': 'not found'}

def test_get_metrics(app, api_controller, mock_services):
    data_service, _ = mock_services
    data_service.get_metrics_data.return_value = {'success': True, 'metrics': []}
    
    with app.app_context():
        response, status_code = api_controller.get_metrics("AAPL")
        assert status_code == 200
        assert response.json == {'success': True, 'metrics': []}

def test_get_watchlist(app, api_controller, mock_services):
    _, watchlist_service = mock_services
    watchlist_service.get_watchlist.return_value = {'success': True, 'watchlist': []}
    
    with app.app_context():
        response = api_controller.get_watchlist()
        assert response.json == {'success': True, 'watchlist': []}

def test_add_to_watchlist(app, api_controller, mock_services):
    _, watchlist_service = mock_services
    watchlist_service.add_to_watchlist.return_value = {'success': True}
    
    with app.app_context():
        response, status_code = api_controller.add_to_watchlist("AAPL")
        assert status_code == 200
        assert response.json == {'success': True}

def test_remove_from_watchlist(app, api_controller, mock_services):
    _, watchlist_service = mock_services
    watchlist_service.remove_from_watchlist.return_value = {'success': True}
    
    with app.app_context():
        response, status_code = api_controller.remove_from_watchlist("AAPL")
        assert status_code == 200
        assert response.json == {'success': True}

def test_get_search_suggestions(app, api_controller, mock_services):
    data_service, _ = mock_services
    data_service.get_search_suggestions.return_value = {'success': True, 'suggestions': []}
    
    with app.app_context():
        response, status_code = api_controller.get_search_suggestions("AA")
        assert status_code == 200
        assert response.json == {'success': True, 'suggestions': []}

def test_get_financial_metrics(app, api_controller, mock_services):
    data_service, _ = mock_services
    data_service.get_financial_metrics_data.return_value = {'success': True, 'metrics': []}
    
    with app.app_context():
        response, status_code = api_controller.get_financial_metrics("AAPL")
        assert status_code == 200
        assert response.json == {'success': True, 'metrics': []}

def test_get_list(app, api_controller):
    with app.app_context():
        # Patch the attributes of the api_controller module
        import web_app.backend.controllers.api_controller as api_mod
        with patch.object(api_mod, 'DataRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_all_tickers.return_value = ["AAPL", "MSFT"]
            response = api_controller.get_list()
            assert response.json['success'] is True
            assert response.json['tickers'] == ["AAPL", "MSFT"]

def test_get_ai_scores(app, api_controller):
    with app.app_context():
        import web_app.backend.controllers.api_controller as api_mod
        with patch.object(api_mod, 'AIScoresRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_all_ai_scores.return_value = [{"ticker": "AAPL", "score": 90}]
            response = api_controller.get_ai_scores()
            assert response.json['success'] is True
            assert response.json['scores'] == [{"ticker": "AAPL", "score": 90}]

def test_get_adjusted_pe_success(app, api_controller):
    with app.app_context():
        import web_app.backend.controllers.api_controller as api_mod
        with patch.object(api_mod, 'AdjustedPERepository') as mock_repo_class:
            with patch.object(api_mod, 'AdjustedPEService') as mock_service_class:
                mock_repo = MagicMock()
                mock_repo_class.return_value = mock_repo
                mock_repo.get_adjusted_pe_with_breakdown.return_value = (25.5, {'ttm_operating_income': 100})
                response = api_controller.get_adjusted_pe("AAPL")
                assert response.json['success'] is True
                assert response.json['adjusted_pe_ratio'] == 25.5

def test_get_adjusted_pe_not_found(app, api_controller):
    with app.app_context():
        import web_app.backend.controllers.api_controller as api_mod
        with patch.object(api_mod, 'AdjustedPERepository') as mock_repo_class:
            with patch.object(api_mod, 'AdjustedPEService') as mock_service_class:
                mock_repo = MagicMock()
                mock_repo_class.return_value = mock_repo
                mock_service = MagicMock()
                mock_service_class.return_value = mock_service
                mock_repo.get_adjusted_pe_with_breakdown.return_value = (None, None)
                mock_service.calculate_and_store_adjusted_pe.return_value = False
                
                response = api_controller.get_adjusted_pe("AAPL")
                if isinstance(response, tuple):
                    res, status_code = response
                    assert status_code == 404
                    assert res.json['success'] is False
                else:
                    assert response.status_code == 404
                    assert response.json['success'] is False

def test_calculate_missing_adjusted_pe(app, api_controller, mock_services):
    _, watchlist_service = mock_services
    with app.app_context():
        import web_app.backend.controllers.api_controller as api_mod
        with patch.object(api_mod, 'DataRepository'):
            response = api_controller.calculate_missing_adjusted_pe()
            assert response.json['success'] is True
            assert 'Started calculating' in response.json['message']

def test_get_peers_already_in_progress(app, api_controller):
    api_controller.ongoing_peer_finding.add("AAPL")
    with app.app_context():
        api_controller.peers_service = MagicMock()
        api_controller.peers_service.get_peers.return_value = {
            'success': False, 
            'message': 'No peer analysis found'
        }
        response, status_code = api_controller.get_peers("AAPL")
        assert status_code == 202
        assert response.json['finding_peers'] is True
        assert 'already in progress' in response.json['message']

def test_get_peers_success(app, api_controller):
    api_controller.peers_service = MagicMock()
    api_controller.peers_service.get_peers.return_value = {'success': True, 'peers': []}
    
    with app.app_context():
        response, status_code = api_controller.get_peers("AAPL")
        assert status_code == 200
        assert response.json == {'success': True, 'peers': []}

def test_find_peers(app, api_controller):
    api_controller.peers_service = MagicMock()
    api_controller.peers_service.find_peers.return_value = {'success': True}
    
    with app.app_context():
        response, status_code = api_controller.find_peers("AAPL")
        assert status_code == 200
        assert response.json == {'success': True}
