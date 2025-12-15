#!/usr/bin/env python3
"""
Convert scores.json to SQLite database (scores.db).
"""

import json
import sqlite3
import os

# Paths
SCORES_JSON = os.path.join(os.path.dirname(__file__), 'data', 'scores.json')
SCORES_DB = os.path.join(os.path.dirname(__file__), 'data', 'scores.db')

def convert_json_to_db():
    """Convert scores.json to SQLite database."""
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
    
    # Create table
    # Store all score data as JSON for flexibility
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            ticker TEXT PRIMARY KEY,
            scores_json TEXT NOT NULL
        )
    ''')
    
    # Create index for faster lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON scores(ticker)')
    
    # Insert data
    print("Inserting data into database...")
    inserted = 0
    for ticker, scores in companies.items():
        # Store all scores as JSON string
        scores_json = json.dumps(scores)
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO scores (ticker, scores_json)
                VALUES (?, ?)
            ''', (ticker.upper(), scores_json))
            inserted += 1
        except Exception as e:
            print(f"Error inserting {ticker}: {e}")
    
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
