#!/usr/bin/env python3
"""
QuickFS Company Name Scraper
Scrapes company names for tickers from QuickFS website

This scraper:
1. Takes a list of tickers from the QuickFS database
2. Visits QuickFS pages for each ticker to extract company names
3. Updates the database with company names
4. Includes proper rate limiting and error handling

Usage:
    python scrape_quickfs_company_names.py --limit 100  # Test with 100 tickers
    python scrape_quickfs_company_names.py --all        # Scrape all tickers
    python scrape_quickfs_company_names.py --missing    # Only scrape tickers without names
"""

import sqlite3
import requests
import time
import os
import sys
import argparse
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin
import json
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Database path
DB_PATH = os.path.join(PROJECT_ROOT, 'quickfs_tickers', 'quickfs_tickers.db')

# QuickFS base URL
QUICKFS_BASE = "https://quickfs.net/company/"

# Headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

class QuickFSCompanyScraper:
    """Scraper for extracting company names from QuickFS"""

    def __init__(self, db_path: str = DB_PATH, delay: float = 1.0):
        self.db_path = db_path
        self.delay = delay  # Delay between requests
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def get_db_connection(self):
        """Get database connection"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        return sqlite3.connect(self.db_path)

    def get_tickers_to_scrape(self, limit: Optional[int] = None, missing_only: bool = False) -> List[str]:
        """Get tickers that need company names scraped"""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            if missing_only:
                # Only get tickers without company names
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
                # Get all tickers
                if limit:
                    cursor.execute('SELECT ticker FROM tickers LIMIT ?', (limit,))
                else:
                    cursor.execute('SELECT ticker FROM tickers ORDER BY ticker')

            results = cursor.fetchall()
            return [row[0] for row in results]
        finally:
            conn.close()

    def scrape_company_name(self, ticker: str) -> Optional[str]:
        """
        Scrape company name for a single ticker from QuickFS

        QuickFS URLs follow pattern: https://quickfs.net/company/{TICKER}
        Company name is typically in the page title or meta tags
        """
        try:
            # Clean ticker (remove any country suffix if present)
            clean_ticker = ticker.replace(':US', '').replace(':CA', '').replace(':AU', '').replace(':NZ', '').replace(':LN', '').replace(':MM', '')

            url = f"{QUICKFS_BASE}{clean_ticker}"

            # Add small random delay to be respectful
            time.sleep(self.delay)

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # Try different methods to extract company name

            # Method 1: Look for JSON-LD structured data
            import re
            json_ld_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', response.text, re.DOTALL)
            if json_ld_match:
                try:
                    json_data = json.loads(json_ld_match.group(1))
                    if isinstance(json_data, dict) and 'name' in json_data:
                        return json_data['name'].strip()
                except json.JSONDecodeError:
                    pass

            # Method 2: Look for page title
            title_match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                # QuickFS titles are like "Apple Inc. (AAPL) Stock Price & News"
                # Extract company name before the ticker
                import re
                company_match = re.match(r'^(.+?)\s*\([^)]+\)', title)
                if company_match:
                    return company_match.group(1).strip()

            # Method 3: Look for meta description
            meta_match = re.search(r'<meta name="description" content="([^"]*)"', response.text, re.IGNORECASE)
            if meta_match:
                description = meta_match.group(1)
                # Extract company name from description
                # Descriptions often start with company name
                words = description.split()
                if len(words) > 0:
                    company_name = words[0]
                    # If it looks like a company name (not generic terms)
                    if not any(word in company_name.lower() for word in ['stock', 'price', 'financial', 'company']):
                        return company_name

            # Method 4: Look for h1 or company name in specific divs
            h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', response.text, re.IGNORECASE)
            if h1_match:
                h1_text = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
                if h1_text and len(h1_text) > 0:
                    return h1_text

            print(f"  WARNING: Could not extract company name for {ticker} from {url}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"  REQUEST ERROR for {ticker}: {e}")
            return None
        except Exception as e:
            print(f"  SCRAPE ERROR for {ticker}: {e}")
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

    def scrape_batch(self, tickers: List[str], batch_size: int = 10, save_progress: bool = True) -> Dict[str, int]:
        """
        Scrape company names for a batch of tickers

        Args:
            tickers: List of ticker symbols
            batch_size: How many to scrape before saving progress
            save_progress: Whether to save progress to a file

        Returns:
            Dictionary with scraping statistics
        """
        stats = {
            'total': len(tickers),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'processed': 0
        }

        progress_file = 'scraping_progress.json'

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
                        print(f"  ✅ {ticker}: {company_name}")
                    else:
                        stats['failed'] += 1
                        print(f"  ❌ Failed to update database for {ticker}")
                else:
                    stats['failed'] += 1

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
                    print(f"  PROGRESS SAVED ({i+1}/{len(tickers)})")

        except KeyboardInterrupt:
            print("\nINTERRUPTED: Scraping stopped by user")
        except Exception as e:
            print(f"\nUNEXPECTED ERROR: {e}")

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
    parser = argparse.ArgumentParser(description="Scrape company names from QuickFS")
    parser.add_argument('--limit', '-l', type=int, help='Limit number of tickers to scrape')
    parser.add_argument('--all', action='store_true', help='Scrape all tickers')
    parser.add_argument('--missing', action='store_true', help='Only scrape tickers missing company names')
    parser.add_argument('--delay', '-d', type=float, default=1.0, help='Delay between requests (seconds)')
    parser.add_argument('--batch-size', '-b', type=int, default=10, help='Save progress every N tickers')

    args = parser.parse_args()

    # Validate arguments
    if not args.all and not args.limit and not args.missing:
        print("Error: Must specify --all, --limit, or --missing")
        print("Examples:")
        print("  python scrape_quickfs_company_names.py --limit 100  # Test with 100 tickers")
        print("  python scrape_quickfs_company_names.py --all        # Scrape all tickers")
        print("  python scrape_quickfs_company_names.py --missing    # Only missing names")
        return

    scraper = QuickFSCompanyScraper(delay=args.delay)

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

    # Confirm before starting
    print(f"\nSTARTING: Ready to scrape {len(tickers)} tickers with {args.delay}s delay between requests")
    print("This will take approximately {:.1f} minutes".format(len(tickers) * args.delay / 60))

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
    print("SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total tickers processed: {stats['processed']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Success rate: {stats['successful']/stats['processed']*100:.1f}%" if stats['processed'] > 0 else "N/A")
    print(f"Time taken: {end_time - start_time:.1f} seconds")
    print(f"Average time per ticker: {(end_time - start_time)/stats['processed']:.1f} seconds" if stats['processed'] > 0 else "N/A")

if __name__ == '__main__':
    main()