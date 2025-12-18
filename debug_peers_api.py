#!/usr/bin/env python3
import requests
import subprocess
import time

# Start the webapp
print('Debugging peers API response...')
process = subprocess.Popen(['python', 'web_app/app.py'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

# Wait for it to start
time.sleep(5)

try:
    # Request AAPL peers
    response = requests.get('http://localhost:5000/api/peers/AAPL')

    if response.status_code == 200:
        data = response.json()
        peers = data.get('peers', [])

        print(f'API returned {len(peers)} peers:')
        for i, peer in enumerate(peers):
            ticker = peer.get('ticker')
            company_name = peer.get('company_name')
            short_float = peer.get('short_float')
            print(f'  {i+1}. {ticker} - {company_name} - Short: {short_float}')

        # Check which peers from database are missing
        import sqlite3
        peers_db_path = 'web_app/peers/peers_results.db'
        conn = sqlite3.connect(peers_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT peer_name, peer_ticker FROM peer_results WHERE ticker = 'AAPL' ORDER BY peer_rank")
        db_peers = cursor.fetchall()
        conn.close()

        print(f'\\nDatabase has {len(db_peers)} peers:')
        api_tickers = {p.get('ticker') for p in peers}
        for name, ticker in db_peers:
            in_api = ticker in api_tickers if ticker else False
            status = 'IN API' if in_api else 'MISSING'
            print(f'  {ticker or name}: {status}')

except Exception as e:
    print(f'Error: {e}')
finally:
    if process.poll() is None:
        process.terminate()
        process.wait()

print('Debug completed!')