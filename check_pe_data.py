#!/usr/bin/env python3
import sqlite3
import os

# Check what stocks have adjusted PE data
db_path = 'web_app/data/consolidated.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all companies
cursor.execute('SELECT ticker FROM companies LIMIT 10')
companies = [row[0] for row in cursor.fetchall()]

print('Checking adjusted PE data for first 10 companies:')
for ticker in companies:
    cursor.execute('''
        SELECT ap.adjusted_pe_ratio
        FROM companies c
        LEFT JOIN adjusted_pe_calculations ap ON c.id = ap.company_id
        WHERE c.ticker = ?
    ''', (ticker,))
    result = cursor.fetchone()
    pe_ratio = result[0] if result else None
    status = 'HAS DATA' if pe_ratio else 'NO DATA'
    print(f'  {ticker}: {status} ({pe_ratio if pe_ratio else "None"})')

conn.close()