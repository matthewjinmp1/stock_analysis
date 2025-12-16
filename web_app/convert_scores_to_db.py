#!/usr/bin/env python3
"""
Convert scores.json to SQLite database (scores.db).
Stores each metric as a separate column in the database.
Also calculates and stores total_score_percentage and total_score_percentile_rank.

NOTE: scores.json has been removed from web_app/data. This script should be run
with a path to scores.json from another location (e.g., AI_stock_scorer/data/scores.json).
"""

import json
import sqlite3
import os
import sys

# Add parent directory to path to import score_calculator
sys.path.insert(0, os.path.dirname(__file__))
from score_calculator import calculate_total_score

# Paths - SCORES_JSON should be provided as command line argument or updated here
SCORES_JSON = os.path.join(os.path.dirname(__file__), 'data', 'scores.json')  # Deprecated - update path
SCORES_DB = os.path.join(os.path.dirname(__file__), 'data', 'scores.db')

# All possible metric columns (discovered from the JSON data)
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

def convert_json_to_db():
    """Convert scores.json to SQLite database with individual columns for each metric."""
    # Load JSON data
    print(f"Loading {SCORES_JSON}...")
    try:
        with open(SCORES_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {SCORES_JSON} not found")
        return False
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {SCORES_JSON}: {e}")
        return False
    
    companies = data.get('companies', {})
    print(f"Found {len(companies)} companies in JSON")
    
    # Create/connect to database
    print(f"Creating database {SCORES_DB}...")
    conn = sqlite3.connect(SCORES_DB)
    cursor = conn.cursor()
    
    # Drop existing table if it exists (to recreate with new schema)
    cursor.execute('DROP TABLE IF EXISTS scores')
    
    # Create table with individual columns for each metric
    # Build CREATE TABLE statement dynamically
    columns_sql = ['ticker TEXT PRIMARY KEY']
    for metric in METRIC_COLUMNS:
        columns_sql.append(f'{metric} TEXT')
    # Add calculated score percentage and percentile rank columns
    columns_sql.append('total_score_percentage REAL')
    columns_sql.append('total_score_percentile_rank INTEGER')
    
    create_table_sql = f'''
        CREATE TABLE scores (
            {', '.join(columns_sql)}
        )
    '''
    cursor.execute(create_table_sql)
    
    # Create index for faster lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON scores(ticker)')
    
    # Insert data
    print("Inserting data into database...")
    inserted = 0
    score_percentages = []  # Store all percentages for percentile calculation
    
    for ticker, scores in companies.items():
        # Calculate total score percentage
        _, _, percentage = calculate_total_score(scores)
        score_percentages.append((ticker.upper(), percentage))
        
        # Build INSERT statement with all columns including calculated percentage
        # Note: percentile rank will be calculated after all inserts
        placeholders = ['?'] * (len(METRIC_COLUMNS) + 2)  # +1 for ticker, +1 for percentage
        insert_sql = f'''
            INSERT INTO scores (ticker, {', '.join(METRIC_COLUMNS)}, total_score_percentage, total_score_percentile_rank)
            VALUES ({', '.join(placeholders)}, NULL)
        '''
        
        # Build values tuple: ticker first, then each metric value, then percentage
        values = [ticker.upper()]
        for metric in METRIC_COLUMNS:
            values.append(scores.get(metric))  # None if not present
        # Add calculated percentage
        values.append(percentage)
        
        try:
            cursor.execute(insert_sql, values)
            inserted += 1
        except Exception as e:
            print(f"Error inserting {ticker}: {e}")
    
    # Calculate percentile ranks for all companies
    print("Calculating percentile ranks...")
    if len(score_percentages) > 0:
        # Extract all percentages for percentile calculation
        all_percentages = [pct for _, pct in score_percentages if pct is not None]
        
        if len(all_percentages) > 0:
            def calculate_percentile_rank(score, all_scores):
                """Calculate percentile rank of a score among all scores."""
                if not all_scores or len(all_scores) == 0:
                    return None
                scores_less_or_equal = sum(1 for s in all_scores if s <= score)
                percentile = int((scores_less_or_equal / len(all_scores)) * 100)
                return percentile
            
            # Update percentile rank for each company
            for ticker, percentage in score_percentages:
                if percentage is not None:
                    percentile_rank = calculate_percentile_rank(percentage, all_percentages)
                    cursor.execute(
                        'UPDATE scores SET total_score_percentile_rank = ? WHERE ticker = ?',
                        (percentile_rank, ticker)
                    )
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print(f"Successfully converted {inserted} companies to database")
    return True

if __name__ == "__main__":
    success = convert_json_to_db()
    if success:
        print("Conversion complete!")
    else:
        print("Conversion failed!")
        exit(1)