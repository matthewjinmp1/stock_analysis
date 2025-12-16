#!/usr/bin/env python3
"""
Unified database cache for all UI data.
Stores company name, scores, and short interest.
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
from src.scrapers.glassdoor_scraper import get_company_name_from_ticker
from src.scrapers.get_short_interest import scrape_ticker_short_interest
from web_app.score_calculator import calculate_total_score, SCORE_DEFINITIONS

# Import QuickFS for adjusted PE ratio calculation
try:
    from quickfs import QuickFS
    import statistics
    QUICKFS_AVAILABLE = True
except ImportError:
    QUICKFS_AVAILABLE = False

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
    
    # Add adjusted PE ratio
    columns.append('adjusted_pe_ratio REAL')
    
    # Create table
    create_table_sql = f'''
        CREATE TABLE IF NOT EXISTS ui_cache (
            {', '.join(columns)}
        )
    '''
    cursor.execute(create_table_sql)
    
    # Check if adjusted_pe_ratio column exists, if not add it
    cursor.execute("PRAGMA table_info(ui_cache)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    if 'adjusted_pe_ratio' not in existing_columns:
        try:
            cursor.execute('ALTER TABLE ui_cache ADD COLUMN adjusted_pe_ratio REAL')
            conn.commit()
        except Exception as e:
            print(f"Warning: Could not add adjusted_pe_ratio column: {e}")
    
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


def calculate_adjusted_pe_from_quickfs(quarterly: Dict) -> Optional[float]:
    """
    Calculate Adjusted PE Ratio from QuickFS quarterly data.
    Same logic as in web_app/get_quickfs_data.py
    
    Returns:
        Adjusted PE ratio or None if calculation not possible
    """
    if not quarterly or not QUICKFS_AVAILABLE:
        return None
    
    # Get required data arrays
    operating_income = quarterly.get("operating_income", [])
    # Try both DA fields
    da = quarterly.get("cfo_da", [])
    if not da or (isinstance(da, list) and len(da) == 0):
        da = quarterly.get("da_income_statement_supplemental", [])
    capex = quarterly.get("capex", [])
    enterprise_value = quarterly.get("enterprise_value", [])
    income_tax = quarterly.get("income_tax", [])
    pretax_income = quarterly.get("pretax_income", [])
    
    # Validate data types and minimum length
    if not all(isinstance(arr, list) for arr in [operating_income, da, capex, enterprise_value, income_tax, pretax_income]):
        return None
    
    # Need at least 4 quarters for TTM and 20 quarters for 5-year median tax rate
    min_quarters = max(4, 20)
    if len(operating_income) < min_quarters:
        return None
    
    # Find the most recent position where we have enough data
    for j in range(len(operating_income) - 1, min_quarters - 1, -1):
        # Get EV from most recent quarter
        if j >= len(enterprise_value) or enterprise_value[j] is None or enterprise_value[j] == 0:
            continue
        
        ev = enterprise_value[j]
        
        # Calculate TTM operating income (sum of last 4 quarters)
        ttm_oi = 0.0
        ttm_da = 0.0
        ttm_capex = 0.0
        valid_ttm = True
        
        for k in range(max(0, j - 3), j + 1):
            if k < len(operating_income) and operating_income[k] is not None:
                ttm_oi += float(operating_income[k])
            else:
                valid_ttm = False
                break
            
            if k < len(da) and da[k] is not None:
                ttm_da += float(da[k])
            
            if k < len(capex) and capex[k] is not None:
                ttm_capex += float(capex[k])
        
        if not valid_ttm:
            continue
        
        # Step 4: If |DA| > |capex|, add back (DA - capex) to operating income
        abs_da = abs(ttm_da)
        abs_capex = abs(ttm_capex)
        
        if abs_da > abs_capex:
            adjustment = ttm_da - ttm_capex
            adjusted_oi = ttm_oi + adjustment
        else:
            adjusted_oi = ttm_oi
        
        # Step 5: Calculate 5-year median tax rate (last 20 quarters)
        tax_rates = []
        for k in range(max(0, j - 19), j + 1):
            if k < len(income_tax) and k < len(pretax_income):
                tax = income_tax[k] if income_tax[k] is not None else None
                pretax = pretax_income[k] if pretax_income[k] is not None else None
                
                if tax is not None and pretax is not None and pretax != 0:
                    # Tax rate = income_tax / pretax_income
                    # Note: income_tax is often negative (tax benefit), so we use absolute value
                    tax_rate = abs(tax) / abs(pretax) if pretax != 0 else None
                    if tax_rate is not None and 0 <= tax_rate <= 1:  # Valid tax rate between 0 and 1
                        tax_rates.append(tax_rate)
        
        if not tax_rates:
            # If no valid tax rates, use a default (e.g., 0.21 for US corporate tax)
            median_tax_rate = 0.21
        else:
            # Calculate median tax rate
            median_tax_rate = statistics.median(tax_rates)
        
        # Step 6: Apply tax rate to adjusted operating income
        adjusted_oi_after_tax = adjusted_oi * (1 - median_tax_rate)
        
        # Step 7: Calculate Adjusted PE = EV / adjusted operating income (after tax)
        if adjusted_oi_after_tax != 0:
            adjusted_pe = ev / adjusted_oi_after_tax
            return adjusted_pe
    
    return None

def fetch_adjusted_pe_ratio(ticker: str) -> Optional[float]:
    """
    Fetch adjusted PE ratio from QuickFS API.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Adjusted PE ratio or None if not available
    """
    if not QUICKFS_AVAILABLE:
        return None
    
    try:
        # Try to import API key
        try:
            from config import QUICKFS_API_KEY
            api_key = QUICKFS_API_KEY
        except ImportError:
            api_key = os.environ.get('QUICKFS_API_KEY')
            if not api_key:
                return None
        
        # Format ticker symbol
        formatted_ticker = ticker
        if ":" not in formatted_ticker:
            formatted_ticker = f"{ticker}:US"
        
        # Fetch data from QuickFS
        client = QuickFS(api_key)
        data = client.get_data_full(formatted_ticker)
        
        if not data or "financials" not in data:
            return None
        
        quarterly = data.get("financials", {}).get("quarterly", {})
        if not quarterly:
            return None
        
        # Calculate adjusted PE ratio
        return calculate_adjusted_pe_from_quickfs(quarterly)
        
    except Exception as e:
        print(f"Error fetching adjusted PE ratio for {ticker}: {e}")
        return None

def fetch_and_cache_all_data(ticker: str, silent: bool = False) -> Optional[Dict[str, Any]]:
    """Fetch all data for a ticker and cache it in the database.
    
    This function:
    1. Gets company name from ticker
    2. Fetches score data from scores.db (if available)
    3. Fetches short interest data
    4. Fetches adjusted PE ratio from QuickFS (if not in cache)
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
    
    # 4. Fetch adjusted PE ratio from QuickFS (if not in cache)
    cached = get_cached_data(ticker)
    if not cached or cached.get('adjusted_pe_ratio') is None:
        if not silent:
            print(f"  Fetching adjusted PE ratio from QuickFS...")
        adjusted_pe = fetch_adjusted_pe_ratio(ticker)
        if adjusted_pe is not None:
            cache_data['adjusted_pe_ratio'] = adjusted_pe
            if not silent:
                print(f"  Adjusted PE Ratio: {adjusted_pe:.2f}")
    
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
    missing_adjusted_pe = cached.get('adjusted_pe_ratio') is None
    
    # If we need to refresh or are missing data, fetch
    if needs_si_refresh or missing_company or missing_adjusted_pe:
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
        
        # Adjusted PE ratio
        if missing_adjusted_pe:
            adjusted_pe = fetch_adjusted_pe_ratio(ticker)
            if adjusted_pe is not None:
                update_data['adjusted_pe_ratio'] = adjusted_pe
        
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

