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
        # Try to find scores.json in quantitative_stock_scorer directory
        json_file = os.path.join(PROJECT_ROOT, 'quantitative_stock_scorer', 'scores.json')
        if not os.path.exists(json_file):
            # Try scripts/analysis directory
            json_file = os.path.join(PROJECT_ROOT, 'quantitative_stock_scorer', 'scripts', 'analysis', 'scores.json')
        if not os.path.exists(json_file):
            # Try current directory
            json_file = os.path.join(PROJECT_ROOT, 'scores.json')
    
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
