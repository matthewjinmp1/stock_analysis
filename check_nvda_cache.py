#!/usr/bin/env python3
import sqlite3

# Check NVDA cached peers
db_path = 'web_app/peers/peers_results.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('SELECT DISTINCT ticker FROM peer_results WHERE ticker = "NVDA"')
nvda_results = cursor.fetchall()

print(f'NVDA cached results: {len(nvda_results)}')
if nvda_results:
    print('NVDA has cached peers!')

    # Get the peer details
    cursor.execute('SELECT peer_name, peer_ticker FROM peer_results WHERE ticker = "NVDA" ORDER BY peer_rank')
    peers = cursor.fetchall()
    print('NVDA peers:')
    for name, ticker in peers:
        print(f'  {ticker or name}')

else:
    print('NVDA has no cached peers')

conn.close()