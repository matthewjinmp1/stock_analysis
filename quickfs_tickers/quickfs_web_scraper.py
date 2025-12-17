#!/usr/bin/env python3
"""
QuickFS Web Scraper for Company Names
Scrapes company names from QuickFS website without using API credits

WARNING: Web scraping may violate QuickFS terms of service.
Use at your own risk and consider rate limiting to be respectful.
"""

import requests
import time
import random
import json
import sqlite3
import os
import sys
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Change to project root directory
os.chdir(PROJECT_ROOT)

# Database path
DB_PATH = os.path.join(PROJECT_ROOT, 'quickfs_tickers', 'quickfs_tickers.db')

class QuickFSWebScraper:
    """Web scraper for QuickFS company names"""

    def __init__(self, db_path: str = DB_PATH, delay: float = 2.0, user_agent: str = None):
        self.db_path = db_path
        self.delay = delay
        self.session = requests.Session()

        # Set a realistic user agent
        if user_agent is None:
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en-US;q=0.8,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })

    def get_db_connection(self):
        """Get database connection"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        return sqlite3.connect(self.db_path)

    def get_tickers_to_scrape(self, limit: int = None, missing_only: bool = True) -> list:
        """Get tickers that need company names scraped"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            if missing_only:
                if limit:
                    cursor.execute(
                        'SELECT ticker FROM tickers WHERE company_name IS NULL OR company_name = "" LIMIT ?',
                        (limit,)
                    )
                else:
                    cursor.execute(
                        'SELECT ticker FROM tickers WHERE company_name IS NULL OR company_name = ""'
                    )
            else:
                if limit:
                    cursor.execute('SELECT ticker FROM tickers LIMIT ?', (limit,))
                else:
                    cursor.execute('SELECT ticker FROM tickers ORDER BY ticker')

            results = cursor.fetchall()
            return [row[0] for row in results]
        finally:
            conn.close()

    def scrape_company_name(self, ticker: str) -> str:
        """
        Scrape company name for a ticker from QuickFS website

        Try multiple URL patterns and extraction methods
        """
        try:
            # Clean ticker (remove any country suffix if present)
            clean_ticker = ticker.replace(':US', '').replace(':CA', '').replace(':AU', '').replace(':NZ', '').replace(':LN', '').replace(':MM', '')

            # Try different URL patterns
            url_patterns = [
                f"https://quickfs.net/company/{clean_ticker}",
                f"https://quickfs.net/company/{clean_ticker}:US",
                f"https://quickfs.net/symbol/{clean_ticker}",
                f"https://quickfs.net/stocks/{clean_ticker}",
            ]

            for url in url_patterns:
                try:
                    # Add random delay to be respectful
                    time.sleep(self.delay + random.uniform(0.5, 1.5))

                    response = self.session.get(url, timeout=15)
                    response.raise_for_status()

                    # Check if we got a real company page (not a generic page)
                    if self._is_company_page(response.text, clean_ticker):
                        company_name = self._extract_company_name(response.text, clean_ticker)
                        if company_name:
                            return company_name

                except requests.exceptions.RequestException as e:
                    print(f"  Network error for {url}: {e}")
                    continue

            return None

        except Exception as e:
            print(f"  Error scraping {ticker}: {e}")
            return None

    def _is_company_page(self, html: str, ticker: str) -> bool:
        """
        Check if the page is actually a company page (not generic/404)
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Check for company-specific indicators
        indicators = [
            f">{ticker}<",  # Ticker in content
            "company",      # Company-related content
            "financial",    # Financial data
            "stock",        # Stock-related content
        ]

        # Avoid generic pages
        if "Export Fundamental Data" in html and "over 35,000" in html:
            return False  # This is the generic landing page

        # Check for 404 or error pages
        if soup.find('title') and ('404' in soup.find('title').text or 'Not Found' in soup.find('title').text):
            return False

        return True

    def _extract_company_name(self, html: str, ticker: str) -> str:
        """
        Extract company name from HTML using multiple methods
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Method 1: JSON-LD structured data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'name' in data:
                    name = data['name'].strip()
                    if name and len(name) > 1 and ticker.lower() not in name.lower():
                        return name
            except (json.JSONDecodeError, AttributeError):
                continue

        # Method 2: Meta tags
        meta_description = soup.find('meta', attrs={'name': 'description'})
        if meta_description and meta_description.get('content'):
            content = meta_description['content']
            # Try to extract company name from description
            # Look for patterns like "Company Name stock price" or "Company Name financial data"
            patterns = [
                r'^([^|]+?)(?:\s+(?:stock|financial|company|price))',
                r'^([^|]+?)(?:\s*\|)',
            ]
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    if len(name) > 2 and ticker.lower() not in name.lower():
                        return name

        # Method 3: Page title
        title_tag = soup.find('title')
        if title_tag and title_tag.text:
            title = title_tag.text.strip()
            # QuickFS titles often follow patterns like:
            # "Apple Inc. (AAPL) Stock Price & News"
            # "Microsoft Corporation Common Stock (MSFT) Quote"
            patterns = [
                r'^(.+?)\s*\([^)]*\)\s*$',  # "Company Name (TICKER)"
                r'^(.+?)\s+Common Stock\s*\([^)]*\)',  # "Company Name Common Stock (TICKER)"
                r'^(.+?)\s+Stock\s*\([^)]*\)',  # "Company Name Stock (TICKER)"
            ]
            for pattern in patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    if len(name) > 2 and ticker.lower() not in name.lower():
                        return name

        # Method 4: H1 tags
        h1_tags = soup.find_all('h1')
        for h1 in h1_tags:
            text = h1.get_text().strip()
            if len(text) > 3 and len(text) < 100 and ticker.lower() not in text.lower():
                # Check if it looks like a company name (not generic)
                if not any(word in text.lower() for word in ['stock', 'price', 'financial', 'quote', 'news']):
                    return text

        # Method 5: Look for company name in specific divs/classes
        company_selectors = [
            '.company-name',
            '.company-title',
            '.stock-name',
            '.ticker-company',
            '[data-company]',
            '.header h1',
            '.company-header',
        ]

        for selector in company_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if len(text) > 2 and len(text) < 100 and ticker.lower() not in text.lower():
                    return text

        # Method 6: Look for breadcrumb or navigation that might contain company name
        breadcrumbs = soup.select('.breadcrumb, .breadcrumbs, nav')
        for breadcrumb in breadcrumbs:
            text = breadcrumb.get_text().strip()
            if ticker in text:
                # Try to extract company name from breadcrumb
                parts = text.split('>')
                for part in parts:
                    part = part.strip()
                    if len(part) > 3 and ticker.lower() not in part.lower():
                        return part

        return None

    def update_company_name(self, ticker: str, company_name: str) -> bool:
        """Update company name in database"""
        if not company_name or not company_name.strip():
            return False

        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                'UPDATE tickers SET company_name = ? WHERE ticker = ?',
                (company_name.strip(), ticker.upper())
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def scrape_batch(self, tickers: list, batch_size: int = 10, save_progress: bool = True) -> dict:
        """
        Scrape company names for a batch of tickers
        """
        stats = {
            'total': len(tickers),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'processed': 0
        }

        progress_file = 'web_scraping_progress.json'

        # Load existing progress if available
        processed_tickers = set()
        if save_progress and os.path.exists(progress_file):
            try:
                with open(progress_file, 'r') as f:
                    progress_data = json.load(f)
                    processed_tickers = set(progress_data.get('processed_tickers', []))
                    stats.update(progress_data.get('stats', {}))
                print(f"Resumed from previous session ({len(processed_tickers)} already processed)")
            except Exception as e:
                print(f"Could not load progress file: {e}")

        try:
            for i, ticker in enumerate(tickers):
                if ticker in processed_tickers:
                    stats['skipped'] += 1
                    continue

                print(f"[{i+1}/{len(tickers)}] Scraping {ticker}...")

                company_name = self.scrape_company_name(ticker)

                if company_name:
                    if self.update_company_name(ticker, company_name):
                        stats['successful'] += 1
                        print(f"  SUCCESS: {ticker} -> {company_name}")
                    else:
                        stats['failed'] += 1
                        print(f"  FAILED: Could not update database for {ticker}")
                else:
                    stats['failed'] += 1
                    print(f"  FAILED: No company name found for {ticker}")

                stats['processed'] = i + 1
                processed_tickers.add(ticker)

                # Save progress every batch_size tickers
                if save_progress and (i + 1) % batch_size == 0:
                    progress_data = {
                        'stats': stats,
                        'processed_tickers': list(processed_tickers),
                        'last_updated': datetime.now().isoformat()
                    }
                    with open(progress_file, 'w') as f:
                        json.dump(progress_data, f, indent=2)
                    print(f"PROGRESS SAVED ({i+1}/{len(tickers)})")

        except KeyboardInterrupt:
            print("\nINTERRUPTED: Scraping stopped by user")
        except Exception as e:
            print(f"\nERROR: Unexpected error: {e}")

        # Final progress save
        if save_progress:
            progress_data = {
                'stats': stats,
                'processed_tickers': list(processed_tickers),
                'last_updated': datetime.now().isoformat()
            }
            with open(progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)

        return stats

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape company names from QuickFS website")
    parser.add_argument('--limit', '-l', type=int, help='Limit number of tickers to scrape')
    parser.add_argument('--all', action='store_true', help='Scrape all tickers (overwrite existing names)')
    parser.add_argument('--missing', action='store_true', help='Only scrape tickers missing company names (default)')
    parser.add_argument('--delay', '-d', type=float, default=2.0, help='Delay between requests (seconds)')
    parser.add_argument('--batch-size', '-b', type=int, default=10, help='Save progress every N tickers')
    parser.add_argument('--user-agent', help='Custom User-Agent string')

    args = parser.parse_args()

    # Validate arguments
    if not args.all and not args.limit and not args.missing:
        args.missing = True  # Default to missing only

    scraper = QuickFSWebScraper(delay=args.delay, user_agent=args.user_agent)

    # Get tickers to scrape
    if args.missing:
        tickers = scraper.get_tickers_to_scrape(limit=args.limit, missing_only=True)
        print(f"Found {len(tickers)} tickers missing company names")
    else:
        tickers = scraper.get_tickers_to_scrape(limit=args.limit, missing_only=False)
        print(f"Selected {len(tickers)} tickers to scrape")

    if not tickers:
        print("No tickers to scrape")
        return

    # Warning about web scraping
    print("\n" + "="*70)
    print("WEB SCRAPING WARNING")
    print("="*70)
    print("This script scrapes QuickFS website without using their API.")
    print("This may violate their Terms of Service.")
    print("Use at your own risk and be respectful with request frequency.")
    print("="*70)

    # Confirm before starting
    print(f"\nReady to scrape {len(tickers)} tickers with {args.delay}s delay between requests")
    estimated_time = len(tickers) * args.delay / 60
    print(".1f")
    try:
        input("Press Enter to start scraping (Ctrl+C to cancel)...")
    except KeyboardInterrupt:
        print("\nCancelled")
        return

    # Start scraping
    start_time = time.time()
    stats = scraper.scrape_batch(tickers, batch_size=args.batch_size)
    end_time = time.time()

    # Print final results
    print(f"\n{'='*60}")
    print("WEB SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total tickers processed: {stats['processed']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Skipped: {stats['skipped']}")
    print(".1f")
    print(".1f")
    print(".1f")

    # Show database stats
    try:
        conn = scraper.get_db_connection()
        cursor = conn.execute("SELECT COUNT(*) as total, COUNT(company_name) as with_names FROM tickers")
        final_stats = cursor.fetchone()
        print(f"\nDatabase status:")
        print(f"  Total tickers: {final_stats[0]}")
        print(f"  With company names: {final_stats[1]}")
        print(".1f")
        conn.close()
    except Exception as e:
        print(f"Could not get final database stats: {e}")

if __name__ == '__main__':
    main()