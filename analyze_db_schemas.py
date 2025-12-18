#!/usr/bin/env python3
"""
Analyze database schemas for refactoring
"""
import sqlite3
import os

data_dir = 'web_app/data'
dbs = ['ui_cache.db', 'ai_scores.db', 'financial_scores.db', 'adjusted_pe.db', 'watchlist.db', 'peers.db', 'tickers.db']

for db_name in dbs:
    db_path = os.path.join(data_dir, db_name)
    if os.path.exists(db_path):
        print(f'\n=== {db_name} ===')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            table_name = table[0]
            print(f'Table: {table_name}')
            cursor.execute(f'PRAGMA table_info({table_name})')
            columns = cursor.fetchall()
            for col in columns:
                print(f'  {col[1]} {col[2]}')
        conn.close()