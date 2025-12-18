#!/usr/bin/env python3
import sqlite3

# Check what's in the peers results database
db_path = 'web_app/peers/peers_results.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if table exists and what data is in it
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print(f'Tables in peers_results.db: {[t[0] for t in tables]}')

# Check peer_results table
cursor.execute('SELECT COUNT(*) FROM peer_results')
count = cursor.fetchone()[0]
print(f'Total peer results: {count}')

# Check what tickers have peer analyses
cursor.execute('SELECT DISTINCT ticker, COUNT(*) as analysis_count FROM peer_results GROUP BY ticker')
ticker_counts = cursor.fetchall()
print('\nTickers with peer analyses:')
for ticker, count in ticker_counts:
    print(f'  {ticker}: {count} peer records')

# Check most recent analysis for AAPL
cursor.execute('SELECT analysis_timestamp FROM peer_results WHERE ticker = "AAPL" ORDER BY analysis_timestamp DESC LIMIT 1')
latest_aapl = cursor.fetchone()
if latest_aapl:
    print(f'\nLatest AAPL analysis: {latest_aapl[0]}')
else:
    print('\nNo AAPL analysis found')

# Check the actual peer data for AAPL
cursor.execute('SELECT peer_name, peer_ticker, analysis_timestamp FROM peer_results WHERE ticker = "AAPL" ORDER BY peer_rank')
aapl_peers = cursor.fetchall()
if aapl_peers:
    print(f'\nAAPL peers ({len(aapl_peers)}):')
    for name, ticker, timestamp in aapl_peers:
        print(f'  {ticker or name} - {timestamp}')

conn.close()