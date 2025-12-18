#!/usr/bin/env python3
import requests
import subprocess
import time

# Start the webapp
print('Testing full application...')
process = subprocess.Popen(['python', 'web_app/app.py'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

# Wait for it to start
time.sleep(3)

try:
    # Test the main page
    response = requests.get('http://localhost:5000/')
    print(f'Main page status: {response.status_code}')

    # Test the AI scores page (should serve React app)
    response2 = requests.get('http://localhost:5000/ai-scores')
    print(f'AI scores page status: {response2.status_code}')
    content_type = response2.headers.get('content-type')
    print(f'Content type: {content_type}')

    # Test the API
    response3 = requests.get('http://localhost:5000/api/ai_scores')
    print(f'API status: {response3.status_code}')

    if response3.status_code == 200:
        data = response3.json()
        success = data.get('success')
        scores = data.get('scores', [])
        print(f'API success: {success}')
        print(f'Number of scores: {len(scores)}')

        if scores:
            first_score = scores[0]
            print(f'First score ticker: {first_score.get("ticker")}')
            print(f'First score company: {first_score.get("company_name")}')
            print(f'First score percentile: {first_score.get("total_score_percentile_rank")}')

except Exception as e:
    print(f'Error: {e}')
finally:
    if process.poll() is None:
        process.terminate()
        process.wait()

print('Test completed.')