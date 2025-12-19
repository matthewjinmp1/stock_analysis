import pytest
import sqlite3
import tempfile
import os
from unittest.mock import MagicMock
from web_app.backend.repositories.ai_scores_repository import AIScoresRepository
from web_app.backend.repositories.adjusted_pe_repository import AdjustedPERepository
from web_app.backend.repositories.data_repository import DataRepository

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp()
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE companies (id INTEGER PRIMARY KEY, ticker TEXT, company_name TEXT)")
    cursor.execute("CREATE TABLE ticker_aliases (company_id INTEGER, ticker TEXT, is_primary INTEGER)")
    cursor.execute("CREATE TABLE financial_scores (company_id INTEGER PRIMARY KEY, total_percentile REAL, total_rank INTEGER)")
    cursor.execute("""
        CREATE TABLE ai_scores (
            company_id INTEGER PRIMARY KEY, 
            moat_score REAL, 
            total_score_percentage REAL, 
            total_score_percentile_rank REAL,
            last_updated TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE adjusted_pe_calculations (
            company_id INTEGER PRIMARY KEY, 
            adjusted_pe_ratio REAL, 
            calculation_status TEXT
        )
    """)
    cursor.execute("INSERT INTO companies (id, ticker, company_name) VALUES (1, 'AAPL', 'Apple')")
    cursor.execute("INSERT INTO ai_scores (company_id, moat_score, total_score_percentage) VALUES (1, 9.0, 95.0)")
    cursor.execute("INSERT INTO adjusted_pe_calculations (company_id, adjusted_pe_ratio, calculation_status) VALUES (1, 25.5, 'success')")
    conn.commit()
    conn.close()
    yield path
    os.close(fd)
    os.unlink(path)

def test_ai_scores_repo(temp_db):
    repo = AIScoresRepository(db_path=temp_db)
    scores = repo.get_ai_scores_by_company_id(1)
    assert scores['moat_score'] == 9.0
    
    all_scores = repo.get_all_ai_scores()
    assert len(all_scores) == 1
    assert all_scores[0]['ticker'] == 'AAPL'

def test_adjusted_pe_repo(temp_db):
    repo = AdjustedPERepository(db_path=temp_db)
    pe_data = repo.get_adjusted_pe_by_company_id(1)
    assert pe_data['adjusted_pe_ratio'] == 25.5
    
    pe_by_ticker = repo.get_adjusted_pe_by_ticker('AAPL')
    assert pe_by_ticker['adjusted_pe_ratio'] == 25.5

def test_data_repo_upserts(temp_db):
    # Need more tables for data repo
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE growth_estimates (
            company_id INTEGER PRIMARY KEY, 
            current_year_growth REAL, 
            next_year_growth REAL, 
            last_updated TIMESTAMP, 
            calculation_status TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE short_interest (
            company_id INTEGER PRIMARY KEY, 
            short_float TEXT, 
            scraped_at TIMESTAMP, 
            last_updated TIMESTAMP, 
            calculation_status TEXT
        )
    """)
    conn.commit()
    conn.close()
    
    repo = DataRepository(db_path=temp_db)
    
    # Test growth upsert
    assert repo.upsert_growth_estimates('AAPL', 10.0, 12.0, 'success') is True
    
    # Test short interest upsert
    assert repo.upsert_short_interest('AAPL', '1.5%', 'success') is True
    
    # Test complete data retrieval
    data = repo.get_complete_data('AAPL')
    assert data['ticker'] == 'AAPL'
    assert data['current_year_growth'] == 10.0
    assert data['short_float'] == '1.5%'
    assert data['moat_score'] == 9.0
    assert data['adjusted_pe_ratio'] == 25.5
