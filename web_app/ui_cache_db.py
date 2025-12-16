#!/usr/bin/env python3
"""
Unified database cache for all UI data.
Stores company name, scores, short interest, and Glassdoor ratings.
"""

import sqlite3
import os
import sys
from datetime import datetime, date
from typing import Optional, Dict, Any

# Ensure project root is on path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import data fetching functions
from src.scrapers.glassdoor_scraper import get_company_name_from_ticker, get_glassdoor_rating_with_direct_grok
from src.scrapers.get_short_interest import scrape_ticker_short_interest
from web_app.score_calculator import calculate_total_score, SCORE_DEFINITIONS

# Path to unified cache database
CACHE_DB = os.path.join(os.path.dirname(__file__), 'data', 'ui_cache.db')

# All metric columns (from convert_scores_to_db.py)
METRIC_COLUMNS = [
    'ai_knowledge_score',
    'ambition_score',
    'bargaining_power_of_customers',
    'bargaining_power_of_suppliers',
    'barriers_score',
    'brand_strength',
    'competition_intensity',
    'culture_employee_satisfaction_score',
    'disruption_risk',
    'ethical_healthy_environmental_score',
    'growth_opportunity',
    'innovativeness_score',
    'long_term_orientation_score',
    'management_quality_score',
    'moat_score',
    'model',
    'network_effect',
    'pricing_power',
    'product_differentiation',
    'product_quality_score',
    'riskiness_score',
    'size_well_known_score',
    'switching_cost',
    'trailblazer_score',
]


def init_database():
    """Initialize the unified cache database with proper schema."""
    os.makedirs(os.path.dirname(CACHE_DB), exist_ok=True)
    
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    # Build column definitions
    columns = [
        'ticker TEXT PRIMARY KEY',
        'company_name TEXT',
        'last_updated TEXT',  # ISO format timestamp
    ]
    
    # Add all metric columns
    for metric in METRIC_COLUMNS:
        columns.append(f'{metric} TEXT')
    
    # Add calculated scores
    columns.append('total_score_percentage REAL')
    columns.append('total_score_percentile_rank INTEGER')
    
    # Add short interest data
    columns.append('short_float TEXT')
    columns.append('short_interest_scraped_at TEXT')
    
    # Add Glassdoor data
    columns.append('glassdoor_rating REAL')
    columns.append('glassdoor_num_reviews INTEGER')
    columns.append('glassdoor_url TEXT')
    columns.append('glassdoor_snippet TEXT')
    columns.append('glassdoor_fetched_at TEXT')
    
    # Create table
    create_table_sql = f'''
        CREATE TABLE IF NOT EXISTS ui_cache (
            {', '.join(columns)}
        )
    '''
    cursor.execute(create_table_sql)
    
    # Create index for faster lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON ui_cache(ticker)')
    
    conn.commit()
    conn.close()


def get_cached_data(ticker: str) -> Optional[Dict[str, Any]]:
    """Get all cached data for a ticker from the database.
    
    Args:
        ticker: Stock ticker symbol (uppercase)
        
    Returns:
        dict: All cached data for the ticker, or None if not found
    """
    if not os.path.exists(CACHE_DB):
        return None
    
    try:
        conn = sqlite3.connect(CACHE_DB)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM ui_cache WHERE ticker = ?', (ticker.upper(),))
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            return None
        
        # Convert row to dictionary
        return dict(row)
    except Exception as e:
        print(f"Error querying cache database: {e}")
        return None


def update_cache(ticker: str, data: Dict[str, Any]) -> bool:
    """Update cache database with new data for a ticker.
    
    Args:
        ticker: Stock ticker symbol (uppercase)
        data: Dictionary of data to update (only provided keys will be updated)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not os.path.exists(CACHE_DB):
        init_database()
    
    try:
        conn = sqlite3.connect(CACHE_DB)
        cursor = conn.cursor()
        
        # Check if record exists
        cursor.execute('SELECT ticker FROM ui_cache WHERE ticker = ?', (ticker.upper(),))
        exists = cursor.fetchone() is not None
        
        # Add last_updated timestamp
        data['last_updated'] = datetime.now().isoformat()
        data['ticker'] = ticker.upper()
        
        if exists:
            # Update existing record
            set_clauses = [f'{key} = ?' for key in data.keys() if key != 'ticker']
            values = [data[key] for key in data.keys() if key != 'ticker']
            values.append(ticker.upper())
            
            update_sql = f'''
                UPDATE ui_cache
                SET {', '.join(set_clauses)}
                WHERE ticker = ?
            '''
            cursor.execute(update_sql, values)
        else:
            # Insert new record
            # Get all column names
            cursor.execute('PRAGMA table_info(ui_cache)')
            columns = [row[1] for row in cursor.fetchall()]
            
            # Build INSERT with all columns, using NULL for missing ones
            placeholders = ['?' for _ in columns]
            insert_sql = f'''
                INSERT INTO ui_cache ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            '''
            
            # Build values list, using data if available, otherwise None
            values = []
            for col in columns:
                values.append(data.get(col))
            
            cursor.execute(insert_sql, values)
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating cache database: {e}")
        import traceback
        traceback.print_exc()
        return False


def fetch_and_cache_all_data(ticker: str, silent: bool = False) -> Optional[Dict[str, Any]]:
    """Fetch all data for a ticker and cache it in the database.
    
    This function:
    1. Gets company name from ticker
    2. Fetches score data from scores.db (if available)
    3. Fetches short interest data
    4. Fetches Glassdoor rating
    5. Stores everything in the unified cache
    
    Args:
        ticker: Stock ticker symbol
        silent: If True, suppress output messages
        
    Returns:
        dict: Complete data for the ticker, or None if error
    """
    ticker = ticker.strip().upper()
    
    if not silent:
        print(f"Fetching all data for {ticker}...")
    
    # Initialize cache data dictionary
    cache_data = {}
    
    # 1. Get company name
    if not silent:
        print(f"  Getting company name...")
    company_name = get_company_name_from_ticker(ticker)
    if company_name:
        cache_data['company_name'] = company_name
        if not silent:
            print(f"  Company: {company_name}")
    
    # 2. Get score data from scores.db (if it exists)
    scores_db_path = os.path.join(os.path.dirname(__file__), 'data', 'scores.db')
    if os.path.exists(scores_db_path):
        if not silent:
            print(f"  Loading scores from scores.db...")
        try:
            conn = sqlite3.connect(scores_db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM scores WHERE ticker = ?', (ticker,))
            row = cursor.fetchone()
            if row:
                column_names = [description[0] for description in cursor.description]
                for i, value in enumerate(row):
                    col_name = column_names[i]
                    if col_name != 'ticker' and value is not None:
                        cache_data[col_name] = value
            conn.close()
        except Exception as e:
            if not silent:
                print(f"  Warning: Could not load scores: {e}")
    
    # 3. Fetch short interest
    if not silent:
        print(f"  Fetching short interest...")
    try:
        prev_cwd = os.getcwd()
        os.chdir(PROJECT_ROOT)
        si_result = scrape_ticker_short_interest(ticker)
        os.chdir(prev_cwd)
        
        if si_result:
            cache_data['short_float'] = si_result.get('short_float')
            cache_data['short_interest_scraped_at'] = si_result.get('scraped_at')
            if not silent:
                print(f"  Short float: {si_result.get('short_float')}")
    except Exception as e:
        if not silent:
            print(f"  Warning: Could not fetch short interest: {e}")
    
    # 4. Fetch Glassdoor rating
    if company_name:
        if not silent:
            print(f"  Fetching Glassdoor rating...")
        try:
            glassdoor_data = get_glassdoor_rating_with_direct_grok(company_name, ticker, silent=True)
            if glassdoor_data:
                cache_data['glassdoor_rating'] = glassdoor_data.get('rating')
                cache_data['glassdoor_num_reviews'] = glassdoor_data.get('num_reviews')
                cache_data['glassdoor_url'] = glassdoor_data.get('url')
                cache_data['glassdoor_snippet'] = glassdoor_data.get('snippet')
                cache_data['glassdoor_fetched_at'] = datetime.now().isoformat()
                if not silent:
                    print(f"  Glassdoor rating: {glassdoor_data.get('rating')}")
        except Exception as e:
            if not silent:
                print(f"  Warning: Could not fetch Glassdoor rating: {e}")
    
    # 5. Store in cache
    if cache_data:
        update_cache(ticker, cache_data)
        if not silent:
            print(f"  Cached all data for {ticker}")
    
    return cache_data if cache_data else None


def get_or_fetch_data(ticker: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
    """Get data for a ticker from cache, or fetch if not available.
    
    Args:
        ticker: Stock ticker symbol
        force_refresh: If True, always fetch fresh data
        
    Returns:
        dict: Complete data for the ticker, or None if error
    """
    ticker = ticker.strip().upper()
    
    # Check cache first (unless force refresh)
    if not force_refresh:
        cached = get_cached_data(ticker)
        if cached:
            # Check if we have all essential data
            has_company_name = cached.get('company_name')
            # If we have at least company name, return cached data
            if has_company_name:
                return cached
    
    # Fetch fresh data
    return fetch_and_cache_all_data(ticker, silent=True)


def should_refresh_short_interest(cached_data: Dict[str, Any]) -> bool:
    """Check if short interest data should be refreshed (if older than today)."""
    scraped_at = cached_data.get('short_interest_scraped_at')
    if not scraped_at:
        return True
    
    try:
        scraped_date = datetime.fromisoformat(scraped_at).date()
        today = date.today()
        return scraped_date < today
    except (ValueError, AttributeError):
        return True


def get_complete_data(ticker: str) -> Optional[Dict[str, Any]]:
    """Get complete data for a ticker, refreshing short interest if needed.
    
    This is the main function to use in the web app.
    It checks cache, refreshes short interest if stale, and fetches missing data.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        dict: Complete data for the ticker
    """
    ticker = ticker.strip().upper()
    
    # Get cached data
    cached = get_cached_data(ticker)
    
    # If no cache, fetch everything
    if not cached:
        return fetch_and_cache_all_data(ticker, silent=True)
    
    # Check if short interest needs refresh
    needs_si_refresh = should_refresh_short_interest(cached)
    
    # Check if we're missing essential data
    missing_company = not cached.get('company_name')
    missing_scores = not any(cached.get(col) for col in METRIC_COLUMNS)
    missing_glassdoor = cached.get('glassdoor_rating') is None
    
    # If we need to refresh or are missing data, fetch
    if needs_si_refresh or missing_company or missing_glassdoor:
        # Fetch only what's missing
        update_data = {}
        
        # Company name
        if missing_company:
            company_name = get_company_name_from_ticker(ticker)
            if company_name:
                update_data['company_name'] = company_name
        
        # Short interest
        if needs_si_refresh:
            try:
                prev_cwd = os.getcwd()
                os.chdir(PROJECT_ROOT)
                si_result = scrape_ticker_short_interest(ticker)
                os.chdir(prev_cwd)
                if si_result:
                    update_data['short_float'] = si_result.get('short_float')
                    update_data['short_interest_scraped_at'] = si_result.get('scraped_at')
            except Exception as e:
                print(f"Warning: Could not refresh short interest: {e}")
        
        # Glassdoor rating
        if missing_glassdoor:
            company_name = cached.get('company_name') or update_data.get('company_name')
            if company_name:
                try:
                    glassdoor_data = get_glassdoor_rating_with_direct_grok(company_name, ticker, silent=True)
                    if glassdoor_data:
                        update_data['glassdoor_rating'] = glassdoor_data.get('rating')
                        update_data['glassdoor_num_reviews'] = glassdoor_data.get('num_reviews')
                        update_data['glassdoor_url'] = glassdoor_data.get('url')
                        update_data['glassdoor_snippet'] = glassdoor_data.get('snippet')
                        update_data['glassdoor_fetched_at'] = datetime.now().isoformat()
                except Exception as e:
                    print(f"Warning: Could not fetch Glassdoor rating: {e}")
        
        # Update cache with new data
        if update_data:
            update_cache(ticker, update_data)
            # Merge into cached data
            cached.update(update_data)
    
    return cached


if __name__ == '__main__':
    # Initialize database
    init_database()
    print(f"Database initialized at {CACHE_DB}")

