#!/usr/bin/env python3
import sqlite3

# Check what peers AAPL has in the peers_results database
peers_db_path = 'web_app/peers/peers_results.db'
conn = sqlite3.connect(peers_db_path)
cursor = conn.cursor()

cursor.execute("SELECT peer_name, peer_ticker FROM peer_results WHERE ticker = 'AAPL' ORDER BY peer_rank")
aapl_peers = cursor.fetchall()
conn.close()

print(f'AAPL has {len(aapl_peers)} peers in database:')
for name, ticker in aapl_peers:
    print(f'  {ticker or name}')

# Now check which of these peers have short interest data
main_db_path = 'web_app/data/consolidated.db'
conn2 = sqlite3.connect(main_db_path)
cursor2 = conn2.cursor()

print('\nChecking short interest data for AAPL peers:')
for name, ticker in aapl_peers:
    if ticker:
        cursor2.execute('SELECT si.short_float FROM companies c LEFT JOIN short_interest si ON c.id = si.company_id WHERE c.ticker = ?', (ticker,))
        result = cursor2.fetchone()
        short_float = result[0] if result else None
        status = 'HAS DATA' if short_float else 'NO DATA'
        print(f'  {ticker}: {status} ({short_float})')

conn2.close()