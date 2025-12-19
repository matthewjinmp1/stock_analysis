import pytest
from unittest.mock import MagicMock
from web_app.backend.repositories.financial_scores_repository import FinancialScoresRepository

@pytest.fixture
def financial_scores_repo():
    repo = FinancialScoresRepository(":memory:")
    repo.execute_single = MagicMock()
    repo.execute_query = MagicMock()
    repo.execute_insert = MagicMock()
    repo.execute_update = MagicMock()
    return repo

def test_get_financial_scores_by_company_id(financial_scores_repo):
    financial_scores_repo.execute_single.return_value = {'company_id': 1, 'total_percentile': 85}
    result = financial_scores_repo.get_financial_scores_by_company_id(1)
    assert result == {'company_id': 1, 'total_percentile': 85}

def test_get_financial_scores_by_ticker(financial_scores_repo):
    financial_scores_repo.execute_single.return_value = {'company_id': 1, 'total_percentile': 85}
    result = financial_scores_repo.get_financial_scores_by_ticker("AAPL")
    assert result == {'company_id': 1, 'total_percentile': 85}

def test_create_or_update_financial_scores_insert(financial_scores_repo):
    financial_scores_repo.execute_single.return_value = None # No existing
    financial_scores_repo.execute_insert.return_value = 1
    
    result = financial_scores_repo.create_or_update_financial_scores(1, {'total_percentile': 85})
    assert result is True
    financial_scores_repo.execute_insert.assert_called()

def test_create_or_update_financial_scores_update(financial_scores_repo):
    financial_scores_repo.execute_single.return_value = {'company_id': 1} # Existing
    financial_scores_repo.execute_update.return_value = 1
    
    result = financial_scores_repo.create_or_update_financial_scores(1, {'total_percentile': 85})
    assert result is True
    financial_scores_repo.execute_update.assert_called()

def test_get_all_financial_scores(financial_scores_repo):
    financial_scores_repo.execute_query.return_value = [{'ticker': 'AAPL'}]
    result = financial_scores_repo.get_all_financial_scores(limit=10)
    assert len(result) == 1

def test_get_financial_scores_count(financial_scores_repo):
    financial_scores_repo.execute_single.return_value = {'count': 5}
    assert financial_scores_repo.get_financial_scores_count() == 5

def test_delete_financial_scores(financial_scores_repo):
    financial_scores_repo.execute_update.return_value = 1
    assert financial_scores_repo.delete_financial_scores(1) is True

def test_get_top_financial_scores(financial_scores_repo):
    financial_scores_repo.execute_query.return_value = [{'ticker': 'AAPL'}]
    result = financial_scores_repo.get_top_financial_scores(limit=1)
    assert len(result) == 1
