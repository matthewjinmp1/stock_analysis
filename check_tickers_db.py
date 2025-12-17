#!/usr/bin/env python3
import sqlite3
import os

def check_db(db_path, table_name):
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Get tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        print(f"\n{db_path} - Tables:", tables)

        # Get schema
        cur.execute(f"PRAGMA table_info({table_name})")
        schema = cur.fetchall()
        print(f"Schema:", schema)

        # Get row count
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cur.fetchone()[0]
        print(f"Row count: {count}")

        # Get sample rows
        cur.execute(f"SELECT * FROM {table_name} LIMIT 3")
        samples = cur.fetchall()
        print("Sample rows:", samples)

        conn.close()
    else:
        print(f"Database not found at {db_path}")

# Check all databases
check_db('web_app/data/tickers.db', 'tickers')
check_db('web_app/data/ui_cache.db', 'ui_cache')
check_db('web_app/data/financial_scores.db', 'financial_scores')
check_db('web_app/data/peers.db', 'peers')

# Check ai_scores.db separately since table name might be different
db_path = 'web_app/data/ai_scores.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    print(f"\n{db_path} - Tables:", tables)
    if tables:
        table_name = tables[0][0]
        cur.execute(f"PRAGMA table_info({table_name})")
        schema = cur.fetchall()
        print(f"Schema:", schema)
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cur.fetchone()[0]
        print(f"Row count: {count}")
        cur.execute(f"SELECT * FROM {table_name} LIMIT 2")
        samples = cur.fetchall()
        print("Sample rows:", samples)
    conn.close()
else:
    print(f"Database not found at {db_path}")