#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('web_app/data/tickers.db')
cur = conn.cursor()

# Find Netflix-related tickers
cur.execute('SELECT ticker, company_name FROM tickers WHERE company_name LIKE "%Netflix%"')
results = cur.fetchall()
print('Netflix-related entries:')
for ticker, company in results:
    print(f'  {ticker}: {company}')

conn.close()