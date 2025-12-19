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

from web_app.backend.data.short_interest_client import get_short_interest_for_ticker, process_ticker

def test_get_short_interest_for_ticker():
    """Test the short interest retrieval with mocks."""
    ticker = "AAPL"
    mock_result = {
        "ticker": "AAPL",
        "short_float": "0.85%",
        "scraped_at": "2023-12-18T10:00:00",
        "success": True
    }
    
    with patch('web_app.backend.data.short_interest_client.scrape_ticker_short_interest') as mock_scrape:
        mock_scrape.return_value = mock_result
        
        result = get_short_interest_for_ticker(ticker)
        
        assert result == mock_result
        mock_scrape.assert_called_once_with(ticker)

def test_process_ticker_success(capsys):
    """Test process_ticker with a successful mock retrieval."""
    ticker = "AAPL"
    mock_result = {
        "ticker": "AAPL",
        "short_float": "0.85%",
        "scraped_at": "2023-12-18T10:00:00",
        "success": True
    }
    
    with patch('web_app.backend.data.short_interest_client.get_short_interest_for_ticker') as mock_get:
        mock_get.return_value = mock_result
        
        # We need to mock json.dumps because it's called in process_ticker
        with patch('json.dumps') as mock_json:
            mock_json.return_value = "{}"
            
            success = process_ticker(ticker)
            
            assert success is True
            captured = capsys.readouterr()
            assert "Fetching short interest" in captured.out
            assert "Ticker: AAPL" in captured.out
            assert "Short Float: 0.85%" in captured.out

def test_process_ticker_failure(capsys):
    """Test process_ticker with a failed mock retrieval."""
    ticker = "INVALID"
    
    with patch('web_app.backend.data.short_interest_client.get_short_interest_for_ticker') as mock_get:
        mock_get.return_value = None
        
        success = process_ticker(ticker)
        
        assert success is False
        captured = capsys.readouterr()
        assert "Error: Could not fetch short interest" in captured.out

def test_process_ticker_no_ticker():
    """Test process_ticker with empty ticker."""
    assert process_ticker("") is False
    assert process_ticker("   ") is False
