#!/usr/bin/env python3
import requests
import subprocess
import time

# Start the webapp
print('Testing updated peers functionality...')
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
        peers = data.get('peers', [])
        print(f'Success: {success}')
        print(f'Number of peers: {len(peers)}')

        if peers:
            first_peer = peers[0]
            ticker = first_peer.get('ticker')
            company_name = first_peer.get('company_name')
            adjusted_pe = first_peer.get('adjusted_pe_ratio')

            print(f'First peer: {ticker or company_name}')
            print(f'Adjusted PE: {adjusted_pe}')
            print('✓ Peers API working correctly')
        else:
            print('No peers returned')
    else:
        print(f'API Error: {response.text}')

except Exception as e:
    print(f'Error: {e}')
finally:
    if process.poll() is None:
        process.terminate()
        process.wait()

print('Test completed!')