#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('web_app/data/tickers.db')
cur = conn.cursor()

# Find companies with 'Meta' in their name
cur.execute('SELECT ticker, company_name FROM tickers WHERE company_name LIKE "%Meta%" LIMIT 10')
results = cur.fetchall()
print('Companies with Meta in name:')
for ticker, company in results:
    print(f'  {ticker}: {company}')

conn.close()