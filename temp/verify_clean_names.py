#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('web_app/data/tickers.db')
cur = conn.cursor()

# Show some examples of the cleaning
cur.execute('''
SELECT company_name, clean_company_name
FROM tickers
WHERE company_name != clean_company_name
LIMIT 20
''')

examples = cur.fetchall()
print("Examples of cleaned company names:")
for original, cleaned in examples:
    print(f'  "{original}" -> "{cleaned}"')

# Show some that didn't change
cur.execute('''
SELECT company_name, clean_company_name
FROM tickers
WHERE company_name = clean_company_name
LIMIT 10
''')

unchanged = cur.fetchall()
print("\nExamples of unchanged company names:")
for original, cleaned in unchanged:
    print(f'  "{original}"')

# Statistics
cur.execute('SELECT COUNT(*) FROM tickers WHERE clean_company_name != company_name')
changed_count = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM tickers')
total_count = cur.fetchone()[0]

print("\nStatistics:")
print(f"  Total records: {total_count}")
print(f"  Records with cleaned names: {changed_count}")
print(f"  Records unchanged: {total_count - changed_count}")

conn.close()