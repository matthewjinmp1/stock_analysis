#!/usr/bin/env python3
import requests
import subprocess
import time

# Start the webapp
print('Testing peer functionality...')
process = subprocess.Popen(['python', 'web_app/app.py'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

# Wait for it to start
time.sleep(3)

try:
    # Test the peers endpoint
    response = requests.get('http://localhost:5000/api/peers/AAPL')
    print(f'Peers API status: {response.status_code}')

    if response.status_code == 200:
        data = response.json()
        success = data.get('success')
        print(f'Success: {success}')
        if success:
            main_ticker = data.get('main_ticker', {})
            peers = data.get('peers', [])
            print(f'Main ticker: {main_ticker.get("ticker")}')
            print(f'Number of peers: {len(peers)}')
            if peers:
                print(f'First peer: {peers[0].get("company_name") or peers[0].get("ticker")}')
        else:
            message = data.get('message')
            print(f'Message: {message}')
    else:
        print(f'Response: {response.text}')

    # Test find peers endpoint
    print('\nTesting find peers...')
    response2 = requests.get('http://localhost:5000/api/find_peers/AAPL')
    print(f'Find peers API status: {response2.status_code}')

except Exception as e:
    print(f'Error: {e}')
finally:
    if process.poll() is None:
        process.terminate()
        process.wait()

print('Test completed!')