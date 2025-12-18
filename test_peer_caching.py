#!/usr/bin/env python3
import requests
import subprocess
import time

# Start the webapp
print('Testing improved peer caching...')
process = subprocess.Popen(['python', 'web_app/app.py'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

# Wait for it to start
time.sleep(5)

try:
    # Test with NVDA - should trigger peer finding only once
    print('Request 1: NVDA peers (should trigger finding)')
    response1 = requests.get('http://localhost:5000/api/peers/NVDA')
    print(f'  Status: {response1.status_code}')
    if response1.status_code == 202:
        data1 = response1.json()
        print(f'  Finding peers: {data1.get("finding_peers", False)}')

    # Immediately make another request - should not trigger again
    print('\nRequest 2: NVDA peers (should not trigger again)')
    response2 = requests.get('http://localhost:5000/api/peers/NVDA')
    print(f'  Status: {response2.status_code}')
    if response2.status_code == 202:
        data2 = response2.json()
        print(f'  Finding peers: {data2.get("finding_peers", False)}')
        print(f'  Message: {data2.get("message", "")}')

    # Test cached peers (AAPL)
    print('\nRequest 3: AAPL peers (should use cache)')
    response3 = requests.get('http://localhost:5000/api/peers/AAPL')
    print(f'  Status: {response3.status_code}')
    if response3.status_code == 200:
        data3 = response3.json()
        peers = data3.get('peers', [])
        print(f'  Peers found: {len(peers)} (cached)')
        print(f'  Finding peers: {data3.get("finding_peers", False)}')

except Exception as e:
    print(f'Error: {e}')
finally:
    if process.poll() is None:
        process.terminate()
        process.wait()

print('Test completed!')