import pytest
import os
from unittest.mock import MagicMock, patch
from web_app.backend.repositories.peers_repository import PeersRepository

@pytest.fixture
def peers_repo():
    return PeersRepository(":memory:")

def test_get_peer_analysis_not_exists(peers_repo):
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = False
        result = peers_repo.get_peer_analysis("AAPL")
        assert result == []

def test_save_peer_analysis_not_exists(peers_repo):
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = False
        result = peers_repo.save_peer_analysis("AAPL", "Apple", [])
        assert result is False

def test_get_peer_analysis_exists(peers_repo):
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True
        
        # Mocking the dynamic import
        mock_peers_db = MagicMock()
        mock_peers_db.get_peer_analysis.return_value = [{'ticker': 'AAPL'}]
        
        with patch('importlib.util.spec_from_file_location') as mock_spec:
            mock_spec.return_value = MagicMock()
            with patch('importlib.util.module_from_spec') as mock_module:
                mock_module.return_value = mock_peers_db
                
                result = peers_repo.get_peer_analysis("AAPL")
                assert result == [{'ticker': 'AAPL'}]
                mock_peers_db.get_peer_analysis.assert_called_with("AAPL", 10)

def test_save_peer_analysis_exists(peers_repo):
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True
        
        # Mocking the dynamic import
        mock_peers_db = MagicMock()
        mock_peers_db.save_peer_analysis.return_value = True
        
        with patch('importlib.util.spec_from_file_location') as mock_spec:
            mock_spec.return_value = MagicMock()
            with patch('importlib.util.module_from_spec') as mock_module:
                mock_module.return_value = mock_peers_db
                
                result = peers_repo.save_peer_analysis("AAPL", "Apple", [])
                assert result is True
                mock_peers_db.save_peer_analysis.assert_called()
