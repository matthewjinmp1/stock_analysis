import pytest
from unittest.mock import MagicMock, patch
from web_app.backend.repositories.company_repository import CompanyRepository

@pytest.fixture
def company_repo():
    repo = CompanyRepository(":memory:")
    repo.execute_single = MagicMock()
    repo.execute_query = MagicMock()
    repo.execute_insert = MagicMock()
    repo.execute_update = MagicMock()
    return repo

def test_get_company_by_ticker(company_repo):
    company_repo.execute_single.return_value = {'id': 1, 'ticker': 'AAPL'}
    result = company_repo.get_company_by_ticker("AAPL")
    assert result == {'id': 1, 'ticker': 'AAPL'}
    company_repo.execute_single.assert_called()

def test_get_company_by_id(company_repo):
    company_repo.execute_single.return_value = {'id': 1, 'ticker': 'AAPL'}
    result = company_repo.get_company_by_id(1)
    assert result == {'id': 1, 'ticker': 'AAPL'}
    company_repo.execute_single.assert_called()

def test_get_all_companies(company_repo):
    company_repo.execute_query.return_value = [{'ticker': 'AAPL'}, {'ticker': 'MSFT'}]
    result = company_repo.get_all_companies(limit=10)
    assert len(result) == 2
    company_repo.execute_query.assert_called()

def test_search_companies(company_repo):
    company_repo.execute_query.return_value = [{'ticker': 'AAPL'}]
    result = company_repo.search_companies("AA")
    assert result == [{'ticker': 'AAPL'}]
    company_repo.execute_query.assert_called()

def test_create_company(company_repo):
    company_repo.execute_insert.return_value = 1
    result = company_repo.create_company("AAPL", "Apple Inc")
    assert result == 1
    company_repo.execute_insert.assert_called()
    company_repo.execute_update.assert_called() # For ticker alias

def test_update_company(company_repo):
    company_repo.execute_update.return_value = 1
    result = company_repo.update_company(1, company_name="Apple")
    assert result is True
    company_repo.execute_update.assert_called()

def test_get_company_tickers(company_repo):
    company_repo.execute_query.return_value = [{'ticker': 'AAPL'}, {'ticker': 'AAPL.US'}]
    result = company_repo.get_company_tickers(1)
    assert result == ['AAPL', 'AAPL.US']
