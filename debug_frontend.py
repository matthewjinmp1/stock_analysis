#!/usr/bin/env python3
import requests
import subprocess
import time

# Start the webapp
print('Starting webapp server...')
process = subprocess.Popen(['python', 'web_app/app.py'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          cwd='c:\\Users\\matth\\stock_analysis')

# Wait for it to start
time.sleep(3)

try:
    # Test the AI scores endpoint
    response = requests.get('http://localhost:5000/api/ai_scores')
    print(f'API Status: {response.status_code}')

    if response.status_code == 200:
        data = response.json()
        success = data.get('success', False)
        scores = data.get('scores', [])

        print(f'API Success: {success}')
        print(f'Number of scores: {len(scores)}')

        if scores:
            first_score = scores[0]
            print(f'First score ticker: {first_score.get("ticker")}')
            print(f'First score company: {first_score.get("company_name")}')
            print(f'First score percentile: {first_score.get("total_score_percentile_rank")}')
            print(f'Available keys: {list(first_score.keys())[:10]}...')
        else:
            print('WARNING: No scores returned from API!')
    else:
        print(f'API Error: {response.text}')

except Exception as e:
    print(f'Error: {e}')
finally:
    # Kill the process
    if process.poll() is None:
        process.terminate()
        process.wait()