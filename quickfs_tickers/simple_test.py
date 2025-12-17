#!/usr/bin/env python3
"""
Simple test to check if we can access QuickFS website
"""

import requests

# Simple test
url = "https://quickfs.net/company/AAPL"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print(f"Testing access to: {url}")

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status code: {response.status_code}")
    print(f"Response size: {len(response.text)} characters")

    if "Apple" in response.text:
        print("SUCCESS: Found Apple in response")
    else:
        print("INFO: Apple not found in response")

    # Show first 500 characters
    print("\nFirst 500 characters:")
    print(response.text[:500])

except Exception as e:
    print(f"Error: {e}")