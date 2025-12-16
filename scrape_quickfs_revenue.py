#!/usr/bin/env python3
"""
Script to scrape revenue data from quickfs.net for a given ticker.

Note: QuickFS.net is a JavaScript-based SPA, so this script attempts to:
1. Find and call API endpoints directly
2. Parse any embedded data in the page
3. Provide instructions for using the QuickFS API/SDK

Usage:
    python scrape_quickfs_revenue.py <TICKER>
    python scrape_quickfs_revenue.py AAPL
"""

import requests
from bs4 import BeautifulSoup
import sys
import json
import re
from typing import Optional, Dict, List
import time

# Try to import Selenium for JavaScript rendering
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Note: Selenium not available. Install with: pip install selenium")
    print("For JavaScript-rendered pages, Selenium is recommended.")

def get_quickfs_url(ticker: str) -> str:
    """Get the QuickFS URL for a ticker."""
    return f"https://quickfs.net/company/{ticker.upper()}"

def try_api_endpoint(ticker: str) -> Optional[Dict]:
    """
    Try to access QuickFS API endpoints directly.
    Note: This may require authentication/API key.
    """
    ticker_upper = ticker.upper()
    
    # Common API endpoint patterns
    api_endpoints = [
        f"https://api.quickfs.net/v1/data/{ticker_upper}/revenue",
        f"https://quickfs.net/api/v1/data/{ticker_upper}/revenue",
        f"https://api.quickfs.net/v1/companies/{ticker_upper}/revenue",
        f"https://quickfs.net/api/companies/{ticker_upper}/revenue",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    for endpoint in api_endpoints:
        try:
            print(f"Trying API endpoint: {endpoint}")
            response = requests.get(endpoint, headers=headers, timeout=5)
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Successfully retrieved data from API!")
                    return data
                except json.JSONDecodeError:
                    pass
        except requests.exceptions.RequestException:
            continue
    
    return None

def scrape_with_selenium(ticker: str) -> Optional[Dict]:
    """
    Scrape revenue data using Selenium to render JavaScript.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with revenue data or None if not found
    """
    if not SELENIUM_AVAILABLE:
        return None
    
    ticker_upper = ticker.upper()
    url = get_quickfs_url(ticker_upper)
    
    print(f"Using Selenium to render JavaScript page...")
    
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        print(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for page to load (look for common elements)
        try:
            # Wait for content to load (adjust selector based on actual page)
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            # Give extra time for JavaScript to load data
            time.sleep(3)
        except TimeoutException:
            print("Warning: Page load timeout, but continuing...")
        
        # Get page source after JavaScript execution
        page_source = driver.page_source
        driver.quit()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        
        revenue_data = {
            'ticker': ticker_upper,
            'url': url,
            'revenue': None,
            'revenue_history': [],
            'source': 'selenium'
        }
        
        # Look for revenue in the rendered page
        # Try multiple selectors that might contain revenue data
        revenue_patterns = [
            r'revenue[:\s]*\$?([\d,]+\.?\d*[BMK]?)',
            r'sales[:\s]*\$?([\d,]+\.?\d*[BMK]?)',
            r'total\s+revenue[:\s]*\$?([\d,]+\.?\d*[BMK]?)',
        ]
        
        page_text = soup.get_text()
        for pattern in revenue_patterns:
            matches = re.finditer(pattern, page_text, re.IGNORECASE)
            for match in matches:
                try:
                    value_str = match.group(1).upper().replace(',', '')
                    multiplier = 1
                    if value_str.endswith('B'):
                        multiplier = 1_000_000_000
                        value_str = value_str[:-1]
                    elif value_str.endswith('M'):
                        multiplier = 1_000_000
                        value_str = value_str[:-1]
                    elif value_str.endswith('K'):
                        multiplier = 1_000
                        value_str = value_str[:-1]
                    
                    revenue_value = float(value_str) * multiplier
                    if revenue_data['revenue'] is None or revenue_value > revenue_data['revenue']:
                        revenue_data['revenue'] = revenue_value
                        print(f"Found revenue: ${revenue_value:,.2f}")
                except ValueError:
                    continue
        
        # Also look in tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    if 'revenue' in label or 'sales' in label:
                        value = cells[1].get_text(strip=True)
                        numbers = re.findall(r'[\d,]+\.?\d*[BMK]?', value.replace(',', ''), re.I)
                        if numbers:
                            try:
                                num_str = numbers[0].upper().replace(',', '')
                                multiplier = 1
                                if num_str.endswith('B'):
                                    multiplier = 1_000_000_000
                                    num_str = num_str[:-1]
                                elif num_str.endswith('M'):
                                    multiplier = 1_000_000
                                    num_str = num_str[:-1]
                                elif num_str.endswith('K'):
                                    multiplier = 1_000
                                    num_str = num_str[:-1]
                                
                                revenue_value = float(num_str) * multiplier
                                if revenue_data['revenue'] is None or revenue_value > revenue_data['revenue']:
                                    revenue_data['revenue'] = revenue_value
                                    print(f"Found revenue in table: ${revenue_value:,.2f}")
                            except ValueError:
                                pass
        
        if revenue_data['revenue'] is not None:
            return revenue_data
        
        return None
        
    except WebDriverException as e:
        print(f"Selenium error: {e}")
        print("Make sure ChromeDriver is installed and in PATH")
        return None
    except Exception as e:
        print(f"Error with Selenium: {e}")
        import traceback
        traceback.print_exc()
        return None

def scrape_revenue_data(ticker: str) -> Optional[Dict]:
    """
    Scrape revenue data from quickfs.net for a given ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with revenue data or None if not found
    """
    ticker_upper = ticker.upper()
    url = get_quickfs_url(ticker_upper)
    
    print(f"Fetching data from: {url}")
    
    # First, try API endpoints
    api_data = try_api_endpoint(ticker_upper)
    if api_data:
        return {
            'ticker': ticker_upper,
            'url': url,
            'source': 'api',
            'data': api_data
        }
    
    # Try Selenium if available
    if SELENIUM_AVAILABLE:
        selenium_data = scrape_with_selenium(ticker_upper)
        if selenium_data and selenium_data.get('revenue') is not None:
            return selenium_data
    
    try:
        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find revenue data in the page
        # QuickFS may structure data in different ways, so we'll try multiple approaches
        
        revenue_data = {
            'ticker': ticker_upper,
            'url': url,
            'revenue': None,
            'revenue_history': [],
            'raw_html_snippet': None
        }
        
        # Method 1: Look for revenue in tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    if 'revenue' in label or 'sales' in label:
                        value = cells[1].get_text(strip=True)
                        # Try to extract numeric value
                        numbers = re.findall(r'[\d,]+\.?\d*', value.replace(',', ''))
                        if numbers:
                            try:
                                revenue_value = float(numbers[0].replace(',', ''))
                                revenue_data['revenue'] = revenue_value
                                revenue_data['raw_html_snippet'] = str(row)[:500]
                                print(f"Found revenue in table: {value}")
                            except ValueError:
                                pass
        
        # Method 2: Look for revenue in divs/spans with common class names
        revenue_elements = soup.find_all(string=re.compile(r'revenue|sales', re.I))
        for element in revenue_elements[:10]:  # Limit search
            parent = element.parent
            if parent:
                # Look for numbers nearby
                text = parent.get_text()
                numbers = re.findall(r'[\d,]+\.?\d*[BMK]?', text)
                if numbers and revenue_data['revenue'] is None:
                    try:
                        # Parse number with B (billion), M (million), K (thousand)
                        num_str = numbers[0].upper().replace(',', '')
                        multiplier = 1
                        if num_str.endswith('B'):
                            multiplier = 1_000_000_000
                            num_str = num_str[:-1]
                        elif num_str.endswith('M'):
                            multiplier = 1_000_000
                            num_str = num_str[:-1]
                        elif num_str.endswith('K'):
                            multiplier = 1_000
                            num_str = num_str[:-1]
                        
                        revenue_value = float(num_str) * multiplier
                        revenue_data['revenue'] = revenue_value
                        revenue_data['raw_html_snippet'] = text[:500]
                        print(f"Found revenue in text: {text[:100]}")
                        break
                    except ValueError:
                        pass
        
        # Method 3: Look for JSON data embedded in the page
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for revenue in JSON-like structures
                if 'revenue' in script.string.lower() or 'sales' in script.string.lower():
                    # Try to extract JSON
                    json_matches = re.findall(r'\{[^{}]*"revenue"[^{}]*\}', script.string, re.I)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            if 'revenue' in data:
                                revenue_data['revenue'] = data['revenue']
                                print(f"Found revenue in JSON: {data}")
                        except json.JSONDecodeError:
                            pass
        
        # If we found revenue, return it
        if revenue_data['revenue'] is not None:
            return revenue_data
        
        # If no revenue found, return the page structure for debugging
        print("\nCould not find revenue data. Page structure:")
        print(f"Title: {soup.title.string if soup.title else 'No title'}")
        print(f"Tables found: {len(tables)}")
        print("\nNote: QuickFS.net is a JavaScript-based application.")
        print("The page loads data dynamically via API calls after initial page load.")
        print("\nOptions:")
        if not SELENIUM_AVAILABLE:
            print("1. Install Selenium: pip install selenium")
            print("   Then install ChromeDriver: https://chromedriver.chromium.org/")
        print("2. Use QuickFS API directly (requires API key)")
        print("3. Use QuickFS Python SDK: pip install quickfs")
        
        # Save HTML for inspection
        with open(f'quickfs_{ticker_upper}_debug.html', 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"\nSaved page HTML to: quickfs_{ticker_upper}_debug.html")
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
        return None
    except Exception as e:
        print(f"Error parsing page: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python scrape_quickfs_revenue.py <TICKER>")
        print("Example: python scrape_quickfs_revenue.py AAPL")
        sys.exit(1)
    
    ticker = sys.argv[1].strip().upper()
    
    print(f"\n{'='*80}")
    print(f"Scraping revenue data for {ticker} from quickfs.net")
    print(f"{'='*80}\n")
    
    revenue_data = scrape_revenue_data(ticker)
    
    if revenue_data:
        if revenue_data.get('source') == 'api':
            print(f"\n{'='*80}")
            print("API DATA RETRIEVED")
            print(f"{'='*80}")
            print(f"Ticker: {revenue_data['ticker']}")
            print("Data from API:")
            print(json.dumps(revenue_data.get('data', {}), indent=2))
            print(f"{'='*80}\n")
        elif revenue_data.get('revenue') is not None:
            print(f"\n{'='*80}")
            print("REVENUE DATA FOUND")
            print(f"{'='*80}")
            print(f"Ticker: {revenue_data['ticker']}")
            print(f"Revenue: ${revenue_data['revenue']:,.2f}")
            print(f"URL: {revenue_data['url']}")
            print(f"{'='*80}\n")
            
            # Print as JSON for easy parsing
            print("JSON output:")
            print(json.dumps(revenue_data, indent=2))
        else:
            print(f"\n{'='*80}")
            print("REVENUE DATA NOT FOUND")
            print(f"{'='*80}")
            print(f"Could not find revenue data for {ticker} on quickfs.net")
            print(f"URL: {get_quickfs_url(ticker)}")
            print("\nPossible reasons:")
            print("  1. Ticker not found on QuickFS")
            print("  2. Page structure changed")
            print("  3. Revenue data is loaded via JavaScript (requires browser automation)")
            print("  4. API requires authentication/API key")
            print(f"\nCheck the debug HTML file: quickfs_{ticker}_debug.html")
            print(f"{'='*80}\n")
            sys.exit(1)
    else:
        print(f"\n{'='*80}")
        print("REVENUE DATA NOT FOUND")
        print(f"{'='*80}")
        print(f"Could not find revenue data for {ticker} on quickfs.net")
        print(f"URL: {get_quickfs_url(ticker)}")
        print("\nPossible reasons:")
        print("  1. Ticker not found on QuickFS")
        print("  2. Page structure changed")
        print("  3. Revenue data is in a different format")
        print(f"\nCheck the debug HTML file: quickfs_{ticker}_debug.html")
        print(f"{'='*80}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
