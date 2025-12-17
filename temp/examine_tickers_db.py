#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('web_app/data/tickers.db')
cur = conn.cursor()

# Check current schema
cur.execute('PRAGMA table_info(tickers)')
schema = cur.fetchall()
print('Current schema:')
for col in schema:
    print(f'  {col[1]}: {col[2]}')

# Sample some company names
cur.execute('SELECT company_name FROM tickers LIMIT 20')
samples = cur.fetchall()
print('\nSample company names:')
for sample in samples:
    print(f'  "{sample[0]}"')

conn.close()