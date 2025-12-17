#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('web_app/data/tickers.db')
cur = conn.cursor()

# Check for NFLX ticker
cur.execute('SELECT ticker, company_name FROM tickers WHERE ticker = "NFLX"')
result = cur.fetchone()
if result:
    print(f'NFLX found: {result[0]}: {result[1]}')
else:
    print('NFLX not found in tickers.db')

# Check for any company with 'flix' in the name
cur.execute('SELECT ticker, company_name FROM tickers WHERE company_name LIKE "%flix%"')
results = cur.fetchall()
print('flix-related entries:')
for ticker, company in results:
    print(f'  {ticker}: {company}')

conn.close()