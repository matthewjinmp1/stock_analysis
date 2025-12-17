#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('web_app/data/tickers.db')
cur = conn.cursor()

# Show the new schema
cur.execute('PRAGMA table_info(tickers)')
schema = cur.fetchall()
print('Updated tickers.db schema:')
for col in schema:
    print(f'  {col[1]}: {col[2]}')

# Show some examples of cleaned names
cur.execute('SELECT company_name, clean_company_name FROM tickers WHERE company_name != clean_company_name LIMIT 10')
examples = cur.fetchall()
print('\nExamples of cleaned company names:')
for original, cleaned in examples:
    print(f'  "{original}" -> "{cleaned}"')

# Statistics
cur.execute('SELECT COUNT(*) FROM tickers')
total = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM tickers WHERE clean_company_name != company_name')
cleaned = cur.fetchone()[0]

print(f'\nTotal records: {total}')
print(f'Records with cleaned names: {cleaned}')
print(f'Clean rate: {cleaned/total*100:.1f}%')

conn.close()