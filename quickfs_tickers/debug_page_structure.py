#!/usr/bin/env python3
"""
Debug QuickFS page structure to understand how to extract company names
"""

import requests
import re
import json

# Headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def find_working_url(ticker):
    """Find a URL format that works for QuickFS"""
    urls_to_try = [
        f"https://quickfs.net/company/{ticker}",
        f"https://quickfs.net/company/{ticker}:US",
        f"https://quickfs.net/symbol/{ticker}",
        f"https://quickfs.net/stocks/{ticker}",
    ]

    for url in urls_to_try:
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()

            html = response.text

            # Check title
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                # If title is not generic and contains the ticker, this might be a company page
                if ticker.upper() in title and "QuickFS" not in title and len(title) > len(ticker) + 10:
                    return url, html

            # If we get a non-generic page, use it
            if len(html) > 10000:  # Company pages are usually larger
                return url, html

        except Exception:
            continue

    # Return first URL as fallback
    return urls_to_try[0], ""

def analyze_page(ticker):
    """Analyze the HTML structure of a QuickFS page"""
    print(f"Analyzing QuickFS page for {ticker}")
    print("=" * 60)

    url, html = find_working_url(ticker)

    if not html:
        print(f"Could not retrieve page for {ticker}")
        return

    print(f"Using URL: {url}")
    print(f"Page size: {len(html)} characters")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        html = response.text

        # Check title
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        if title_match:
            print(f"TITLE: {title_match.group(1)}")

        # Check for JSON-LD
        json_ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        print(f"\nFound {len(json_ld_matches)} JSON-LD scripts:")
        for i, json_ld in enumerate(json_ld_matches):
            try:
                data = json.loads(json_ld)
                print(f"  JSON-LD {i+1}: {data}")
            except:
                print(f"  JSON-LD {i+1}: Invalid JSON")

        # Check for meta tags
        meta_matches = re.findall(r'<meta[^>]*name="([^"]*)"[^>]*content="([^"]*)"[^>]*>', html, re.IGNORECASE)
        print(f"\nMeta tags ({len(meta_matches)}):")
        for name, content in meta_matches:
            if 'title' in name.lower() or 'description' in name.lower():
                print(f"  {name}: {content}")

        # Check for h1 tags
        h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE)
        print(f"\nH1 tags ({len(h1_matches)}):")
        for i, h1 in enumerate(h1_matches):
            clean_h1 = re.sub(r'<[^>]+>', '', h1).strip()
            print(f"  H1 {i+1}: {clean_h1}")

        # Look for company name patterns
        print("\nLooking for company name patterns...")

        # Check if there's a company name in a specific div or class
        company_patterns = [
            r'<div[^>]*class="[^"]*company[^"]*"[^>]*>(.*?)</div>',
            r'<span[^>]*class="[^"]*company[^"]*"[^>]*>(.*?)</span>',
            r'<h2[^>]*class="[^"]*company[^"]*"[^>]*>(.*?)</h2>',
            r'<p[^>]*class="[^"]*company[^"]*"[^>]*>(.*?)</p>',
        ]

        for pattern in company_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                print(f"  Found company pattern matches: {matches}")

        # Look for the main company header - might be in a specific structure
        # QuickFS might have the company name in a specific location
        header_patterns = [
            r'<div[^>]*class="[^"]*header[^"]*"[^>]*>.*?<h1[^>]*>(.*?)</h1>.*?</div>',
            r'<header[^>]*>.*?<h1[^>]*>(.*?)</h1>.*?</header>',
        ]

        for pattern in header_patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            if matches:
                for match in matches:
                    clean_match = re.sub(r'<[^>]+>', '', match).strip()
                    print(f"  Header pattern match: {clean_match}")

        print(f"\nPage size: {len(html)} characters")
        print("Analysis complete.")

    except Exception as e:
        print(f"Error: {e}")

def main():
    """Test with known tickers"""
    tickers = ['AAPL', 'MSFT']

    for ticker in tickers:
        analyze_page(ticker)
        print("\n" + "="*80 + "\n")
        # Small delay between requests
        import time
        time.sleep(2)

if __name__ == '__main__':
    main()