#!/usr/bin/env python3
import requests
import subprocess
import time

# Start the webapp
print('Testing automatic peer finding for new stocks...')
process = subprocess.Popen(['python', 'web_app/app.py'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

# Wait for it to start
time.sleep(5)

try:
    # Test with a stock that might not have peers (let's try a smaller/mid-cap stock)
    test_ticker = 'PLTR'  # Palantir - might not have peers stored

    print(f'Testing peer finding for {test_ticker}...')
    response = requests.get(f'http://localhost:5000/api/peers/{test_ticker}')

    print(f'Status: {response.status_code}')

    if response.status_code == 202:  # 202 Accepted - finding peers
        data = response.json()
        print('SUCCESS: Automatic peer finding triggered!')
        print(f'Message: {data.get("message")}')
        print(f'Finding peers: {data.get("finding_peers")}')
        print(f'Peers in response: {len(data.get("peers", []))}')

    elif response.status_code == 200:
        data = response.json()
        success = data.get('success')
        peers = data.get('peers', [])
        print(f'Success: {success}')
        print(f'Peers found: {len(peers)}')
        if peers:
            print('Peers already existed - no automatic finding needed')
        else:
            print('No peers found and no automatic finding triggered')

    else:
        print(f'Error: {response.text}')

except Exception as e:
    print(f'Error: {e}')
finally:
    if process.poll() is None:
        process.terminate()
        process.wait()

print('Test completed!')