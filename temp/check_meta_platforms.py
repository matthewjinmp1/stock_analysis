#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('web_app/data/tickers.db')
cur = conn.cursor()

# Find Meta Platforms specifically
cur.execute('SELECT ticker, company_name FROM tickers WHERE company_name LIKE "%Meta Platforms%"')
results = cur.fetchall()
print('Meta Platforms entries:')
for ticker, company in results:
    print(f'  {ticker}: {company}')

# Check what META ticker is
cur.execute('SELECT ticker, company_name FROM tickers WHERE ticker = "META"')
results2 = cur.fetchall()
print('META ticker entries:')
for ticker, company in results2:
    print(f'  {ticker}: {company}')

conn.close()