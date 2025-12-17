#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('web_app/data/ui_cache.db')
cur = conn.cursor()

# Check for Apple entries
cur.execute('SELECT ticker, company_name FROM ui_cache WHERE company_name LIKE "%Apple%"')
apple_results = cur.fetchall()
print('Apple entries:', apple_results)

# Check total count
cur.execute('SELECT COUNT(*) FROM ui_cache')
total = cur.fetchone()[0]
print('Total entries:', total)

# Check first few entries
cur.execute('SELECT ticker, company_name FROM ui_cache LIMIT 5')
first_few = cur.fetchall()
print('First 5 entries:', first_few)

conn.close()