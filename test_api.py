#!/usr/bin/env python3
import requests
import subprocess
import time

# Start the app in the background
print('Starting webapp...')
process = subprocess.Popen(['python', 'web_app/app.py'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          cwd='c:\\Users\\matth\\stock_analysis')

# Wait for it to start
time.sleep(5)

try:
    # Test the AI scores endpoint
    response = requests.get('http://localhost:5000/api/ai_scores', timeout=10)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'Success: {data["success"]}')
        if 'scores' in data:
            print(f'Number of scores: {len(data["scores"])}')
            if data['scores']:
                first_score = data["scores"][0]
                print(f'First score keys: {list(first_score.keys())}')
                print(f'First score ticker: {first_score.get("ticker")}')
                print(f'First score company: {first_score.get("company_name")}')
        else:
            print('No scores key in response')
    else:
        print(f'Response: {response.text}')

except Exception as e:
    print(f'Error: {e}')
finally:
    # Kill the process
    process.terminate()
    process.wait()