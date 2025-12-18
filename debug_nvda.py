#!/usr/bin/env python3
import requests
import subprocess
import time

# Start the webapp
print('Debugging NVDA peers...')
process = subprocess.Popen(['python', 'web_app/app.py'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

# Wait for it to start
time.sleep(5)

try:
    # Test NVDA peers
    response = requests.get('http://localhost:5000/api/peers/NVDA')
    print(f'Status: {response.status_code}')

    if response.status_code == 200:
        data = response.json()
        print(f'Success: {data.get("success")}')
        print(f'Finding peers: {data.get("finding_peers")}')
        peers = data.get('peers', [])
        print(f'Peers count: {len(peers)}')
        if 'message' in data:
            print(f'Message: {data["message"]}')

except Exception as e:
    print(f'Error: {e}')
finally:
    if process.poll() is None:
        process.terminate()
        process.wait()

print('Debug completed!')