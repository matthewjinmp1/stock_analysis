import sys
import os
import pytest
import sqlite3
import tempfile

# Add the project root to the path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Add web_app to path
WEB_APP_ROOT = os.path.join(PROJECT_ROOT, 'web_app')
if WEB_APP_ROOT not in sys.path:
    sys.path.insert(0, WEB_APP_ROOT)

from web_app.backend.repositories.watchlist_repository import WatchlistRepository

@pytest.fixture
def temp_db():
    """Create a temporary database with necessary tables for testing."""
    fd, path = tempfile.mkstemp()
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE companies (
            id INTEGER PRIMARY KEY,
            ticker TEXT UNIQUE,
            company_name TEXT,
            exchange TEXT,
            sector TEXT,
            industry TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE watchlist (
            id INTEGER PRIMARY KEY,
            company_id INTEGER UNIQUE,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )
    """)
    
    # Optional tables for get_watchlist query
    cursor.execute("CREATE TABLE ai_scores (company_id INTEGER PRIMARY KEY, total_score_percentage REAL, total_score_percentile_rank REAL)")
    cursor.execute("CREATE TABLE financial_scores (company_id INTEGER PRIMARY KEY, total_percentile REAL)")
    cursor.execute("CREATE TABLE adjusted_pe_calculations (company_id INTEGER PRIMARY KEY, adjusted_pe_ratio REAL, adjusted_oi_after_tax REAL, updated_ev REAL, calculation_status TEXT)")
    cursor.execute("CREATE TABLE growth_estimates (company_id INTEGER PRIMARY KEY, current_year_growth REAL, next_year_growth REAL, last_updated TEXT, calculation_status TEXT)")
    cursor.execute("CREATE TABLE short_interest (company_id INTEGER PRIMARY KEY, short_float TEXT, calculation_status TEXT)")
    
    # Insert sample data
    cursor.execute("INSERT INTO companies (ticker, company_name) VALUES ('AAPL', 'Apple Inc.')")
    cursor.execute("INSERT INTO companies (ticker, company_name) VALUES ('MSFT', 'Microsoft')")
    
    conn.commit()
    conn.close()
    
    yield path
    
    os.close(fd)
    os.unlink(path)

def test_watchlist_operations(temp_db):
    repo = WatchlistRepository(db_path=temp_db)
    
    # Test count initially 0
    assert repo.get_watchlist_count() == 0
    
    # Test add to watchlist
    assert repo.add_to_watchlist('AAPL') is True
    assert repo.get_watchlist_count() == 1
    assert repo.is_in_watchlist('AAPL') is True
    
    # Test adding duplicate
    assert repo.add_to_watchlist('AAPL') is False
    assert repo.get_watchlist_count() == 1
    
    # Test adding non-existent company
    assert repo.add_to_watchlist('NONEXISTENT') is False
    
    # Test get watchlist tickers
    assert repo.get_watchlist_tickers() == ['AAPL']
    
    # Test get full watchlist data
    watchlist = repo.get_watchlist()
    assert len(watchlist) == 1
    assert watchlist[0]['ticker'] == 'AAPL'
    
    # Test remove from watchlist
    assert repo.remove_from_watchlist('AAPL') is True
    assert repo.get_watchlist_count() == 0
    assert repo.is_in_watchlist('AAPL') is False
    
    # Test removing non-existent
    assert repo.remove_from_watchlist('MSFT') is False # Company exists but not in watchlist
