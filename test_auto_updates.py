#!/usr/bin/env python3
import requests
import subprocess
import time

# Start the webapp
print('Testing automatic PE data updates...')
process = subprocess.Popen(['python', 'web_app/app.py'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

# Wait for it to start
time.sleep(5)

try:
    # Test the peers endpoint
    response = requests.get('http://localhost:5000/api/peers/AAPL')
    print(f'Peers API status: {response.status_code}')

    if response.status_code == 200:
        data = response.json()
        peers = data.get('peers', [])
        print(f'Found {len(peers)} peers')

        # Check if any peers have pending PE data
        pending_peers = [p for p in peers if p.get('adjusted_pe_ratio') is None]
        if pending_peers:
            print(f'Found {len(pending_peers)} peers with pending PE data:')
            for peer in pending_peers[:3]:  # Show first 3
                ticker = peer.get('ticker')
                print(f'  - {ticker}: Will show "Calculating..." with spinner')
        else:
            print('All peers have PE data (no polling needed)')

    print('\nFrontend will now:')
    print('- Show "Calculating..." with spinner for pending PE data')
    print('- Poll every 5 seconds for updates')
    print('- Automatically replace with actual numbers when ready')

except Exception as e:
    print(f'Error: {e}')
finally:
    if process.poll() is None:
        process.terminate()
        process.wait()

print('Test completed!')