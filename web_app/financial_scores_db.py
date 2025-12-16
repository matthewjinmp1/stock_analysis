#!/usr/bin/env python3
"""
Database management for financial scores from quantitative scorer.
"""

import sqlite3
import os
import json
import sys

# Ensure project root is on path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import financial scorer
from web_app.financial_scorer import METRICS, load_scores_from_json, calculate_scores_for_all_stocks, load_data_from_jsonl

# Path to financial scores database
FINANCIAL_SCORES_DB = os.path.join(os.path.dirname(__file__), 'data', 'financial_scores.db')

def init_database():
    """Initialize the financial scores database with proper schema."""
    os.makedirs(os.path.dirname(FINANCIAL_SCORES_DB), exist_ok=True)
    
    conn = sqlite3.connect(FINANCIAL_SCORES_DB)
    cursor = conn.cursor()
    
    # Build column definitions
    columns = [
        'ticker TEXT PRIMARY KEY',
        'company_name TEXT',
        'exchange TEXT',
        'period TEXT',
        'market_cap REAL',
        'total_percentile REAL',
        'total_rank INTEGER',
    ]
    
    # Add all metric columns (value, rank, percentile for each)
    for metric in METRICS:
        columns.append(f'{metric.key} REAL')  # Metric value
        columns.append(f'{metric.key}_rank INTEGER')  # Rank
        columns.append(f'{metric.key}_percentile REAL')  # Percentile
    
    # Create table
    create_table_sql = f'''
        CREATE TABLE IF NOT EXISTS financial_scores (
            {', '.join(columns)}
        )
    '''
    cursor.execute(create_table_sql)
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON financial_scores(ticker)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_total_percentile ON financial_scores(total_percentile)')
    
    conn.commit()
    conn.close()

def load_scores_from_json_file(json_file: str = None):
    """Load scores from JSON file and return as list of dicts."""
    if json_file is None:
        # Try to find scores.json in various locations
        possible_paths = [
            os.path.join(PROJECT_ROOT, 'quantitative_stock_scorer', 'data', 'scores.json'),  # Most likely location
            os.path.join(PROJECT_ROOT, 'quantitative_stock_scorer', 'scores.json'),
            os.path.join(PROJECT_ROOT, 'quantitative_stock_scorer', 'scripts', 'analysis', 'scores.json'),
            os.path.join(PROJECT_ROOT, 'scores.json'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                json_file = path
                break
        
        if json_file is None:
            json_file = possible_paths[0]  # Use first path for error message
    
    if not os.path.exists(json_file):
        print(f"JSON file not found. Tried: {json_file}")
        return None
    
    print(f"Loading scores from: {json_file}")
    data = load_scores_from_json(json_file)
    if data and 'scores' in data:
        return data['scores']
    return None

def populate_database_from_json(json_file: str = None):
    """Populate database from JSON scores file."""
    scores = load_scores_from_json_file(json_file)
    if not scores:
        print(f"No scores found in JSON file")
        return False
    
    init_database()
    
    conn = sqlite3.connect(FINANCIAL_SCORES_DB)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM financial_scores')
    
    # Insert scores
    inserted = 0
    for stock in scores:
        # Build column names and values
        columns = ['ticker', 'company_name', 'exchange', 'period', 'market_cap', 'total_percentile', 'total_rank']
        values = [
            stock.get('symbol', '').upper(),
            stock.get('company_name', ''),
            stock.get('exchange', ''),
            stock.get('period', ''),
            stock.get('market_cap'),
            stock.get('total_percentile'),
            stock.get('total_rank'),
        ]
        
        # Add metric values, ranks, and percentiles
        for metric in METRICS:
            columns.append(metric.key)
            values.append(stock.get(metric.key))
            columns.append(f'{metric.key}_rank')
            values.append(stock.get(f'{metric.key}_rank'))
            columns.append(f'{metric.key}_percentile')
            values.append(stock.get(f'{metric.key}_percentile'))
        
        # Insert
        placeholders = ', '.join(['?' for _ in columns])
        insert_sql = f'''
            INSERT INTO financial_scores ({', '.join(columns)})
            VALUES ({placeholders})
        '''
        try:
            cursor.execute(insert_sql, values)
            inserted += 1
        except Exception as e:
            print(f"Error inserting {stock.get('symbol')}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"Inserted {inserted} financial scores into database")
    return True

def calculate_and_populate_database():
    """Calculate scores from source data files and populate database."""
    import time
    
    print("Calculating scores from source data files...")
    print("=" * 80)
    
    # Find data files
    possible_nyse_paths = [
        os.path.join(PROJECT_ROOT, 'quantitative_stock_scorer', 'data', 'nyse_data.jsonl'),
        os.path.join(PROJECT_ROOT, 'nyse_data.jsonl'),
    ]
    
    possible_nasdaq_paths = [
        os.path.join(PROJECT_ROOT, 'quantitative_stock_scorer', 'data', 'nasdaq_data.jsonl'),
        os.path.join(PROJECT_ROOT, 'nasdaq_data.jsonl'),
    ]
    
    nyse_file = None
    nasdaq_file = None
    
    for path in possible_nyse_paths:
        if os.path.exists(path):
            nyse_file = path
            break
    
    for path in possible_nasdaq_paths:
        if os.path.exists(path):
            nasdaq_file = path
            break
    
    if not nyse_file or not nasdaq_file:
        print("Error: Could not find data files")
        if not nyse_file:
            print(f"  NYSE file not found. Tried: {possible_nyse_paths}")
        if not nasdaq_file:
            print(f"  NASDAQ file not found. Tried: {possible_nasdaq_paths}")
        return False
    
    print(f"Loading NYSE data from: {nyse_file}")
    nyse_stocks = load_data_from_jsonl(nyse_file)
    print(f"Found {len(nyse_stocks)} NYSE stocks")
    
    print(f"\nLoading NASDAQ data from: {nasdaq_file}")
    nasdaq_stocks = load_data_from_jsonl(nasdaq_file)
    print(f"Found {len(nasdaq_stocks)} NASDAQ stocks")
    
    if not nyse_stocks and not nasdaq_stocks:
        print("Error: No stock data found in either file")
        return False
    
    # Calculate scores
    print("\nCalculating scores and percentiles...")
    start_time = time.time()
    scores_data = calculate_scores_for_all_stocks(nyse_stocks, nasdaq_stocks)
    elapsed_time = time.time() - start_time
    print(f"Score calculation completed in {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    
    if not scores_data:
        print("Error: No scores were successfully calculated")
        return False
    
    print(f"Calculated scores for {len(scores_data)} stocks")
    
    # Initialize database
    init_database()
    
    # Insert into database
    conn = sqlite3.connect(FINANCIAL_SCORES_DB)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM financial_scores')
    
    # Insert scores
    inserted = 0
    for stock in scores_data:
        # Build column names and values
        columns = ['ticker', 'company_name', 'exchange', 'period', 'market_cap', 'total_percentile', 'total_rank']
        values = [
            stock.get('symbol', '').upper(),
            stock.get('company_name', ''),
            stock.get('exchange', ''),
            stock.get('period', ''),
            stock.get('market_cap'),
            stock.get('total_percentile'),
            stock.get('total_rank'),
        ]
        
        # Add metric values, ranks, and percentiles
        for metric in METRICS:
            columns.append(metric.key)
            values.append(stock.get(metric.key))
            columns.append(f'{metric.key}_rank')
            values.append(stock.get(f'{metric.key}_rank'))
            columns.append(f'{metric.key}_percentile')
            values.append(stock.get(f'{metric.key}_percentile'))
        
        # Insert
        placeholders = ', '.join(['?' for _ in columns])
        insert_sql = f'''
            INSERT INTO financial_scores ({', '.join(columns)})
            VALUES ({placeholders})
        '''
        try:
            cursor.execute(insert_sql, values)
            inserted += 1
        except Exception as e:
            print(f"Error inserting {stock.get('symbol')}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\nInserted {inserted} financial scores into database")
    return True

def get_financial_scores(ticker: str) -> dict:
    """Get financial scores for a ticker from database."""
    if not os.path.exists(FINANCIAL_SCORES_DB):
        return None
    
    try:
        conn = sqlite3.connect(FINANCIAL_SCORES_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM financial_scores WHERE ticker = ?', (ticker.upper(),))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return dict(row)
    except Exception as e:
        print(f"Error querying financial scores database: {e}")
        return None

if __name__ == '__main__':
    # Initialize database
    init_database()
    print(f"Database initialized at {FINANCIAL_SCORES_DB}")
    
    # Try to populate from JSON if it exists
    if populate_database_from_json():
        print("Database populated from JSON file")
