import sys
import os
import pytest
import json

# Add the project root to the path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from web_app.backend.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_watchlist_api(client):
    """Test the /api/watchlist endpoint returns the expected structure."""
    response = client.get('/api/watchlist')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'watchlist' in data
    assert isinstance(data['watchlist'], list)
    
    if len(data['watchlist']) > 0:
        item = data['watchlist'][0]
        # These are the fields the frontend expects
        required_fields = [
            'ticker', 
            'company_name', 
            'adjusted_pe_loading', 
            'growth_loading', 
            'short_interest_loading', 
            'financial_loading',
            'two_year_annualized_growth'
        ]
        for field in required_fields:
            assert field in item, f"Missing field '{field}' in watchlist item"

def test_search_suggestions_api(client):
    """Test the /api/search_suggestions endpoint."""
    response = client.get('/api/search_suggestions/AAPL')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'suggestions' in data
    assert isinstance(data['suggestions'], list)

def test_metrics_api(client):
    """Test the /api/metrics endpoint for a known ticker."""
    response = client.get('/api/metrics/AAPL')
    # It might return 200 or 404 depending on if data exists, 
    # but we just want to see it doesn't 500
    assert response.status_code in [200, 404]
