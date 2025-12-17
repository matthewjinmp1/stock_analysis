#!/usr/bin/env python3
"""
Alternative Ticker Sources Collector
Collects stock tickers from various free sources (Wikipedia, APIs, etc.)
"""

import requests
import json
import time
import os
import sys
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, quote
import re

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("BeautifulSoup required. Install with: pip install beautifulsoup4")
    sys.exit(1)

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Database path
DB_PATH = os.path.join(PROJECT_ROOT, 'alternative_tickers', 'alternative_tickers.db')

class AlternativeTickerCollector:
    """Collect tickers from various alternative sources"""

    def __init__(self, db_path: str = DB_PATH, delay: float = 1.0):
        self.db_path = db_path
        self.delay = delay
        self.session = requests.Session()

        # Set headers to mimic browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en-US;q=0.8,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def get_db_connection(self):
        """Get database connection"""
        if not os.path.exists(self.db_path):
            self.init_database()
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize the database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create main tickers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickers (
                ticker TEXT PRIMARY KEY,
                company_name TEXT,
                source TEXT,
                source_url TEXT,
                collected_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_valid BOOLEAN DEFAULT 1
            )
        ''')

        # Create sources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT UNIQUE,
                description TEXT,
                url TEXT,
                ticker_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON tickers(ticker)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON tickers(source)')

        conn.commit()
        conn.close()

    def collect_wikipedia_sp500(self) -> List[Dict]:
        """Collect S&P 500 tickers from Wikipedia"""
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

        try:
            print("Collecting S&P 500 from Wikipedia...")
            time.sleep(self.delay)

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the main table
            table = soup.find('table', {'id': 'constituents'})
            if not table:
                table = soup.find('table', {'class': 'wikitable'})

            if not table:
                print("Could not find S&P 500 table on Wikipedia")
                return []

            tickers = []
            rows = table.find_all('tr')[1:]  # Skip header

            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    # Ticker is usually in the first column
                    ticker_cell = cols[0]
                    ticker_link = ticker_cell.find('a')
                    if ticker_link:
                        ticker = ticker_link.text.strip()
                    else:
                        ticker = ticker_cell.text.strip()

                    # Company name is usually in the second column
                    company_cell = cols[1]
                    company_link = company_cell.find('a')
                    if company_link:
                        company_name = company_link.text.strip()
                    else:
                        company_name = company_cell.text.strip()

                    if ticker and company_name:
                        tickers.append({
                            'ticker': ticker.upper(),
                            'company_name': company_name,
                            'source': 'wikipedia_sp500',
                            'source_url': url
                        })

            print(f"Collected {len(tickers)} S&P 500 companies from Wikipedia")
            return tickers

        except Exception as e:
            print(f"Error collecting S&P 500: {e}")
            return []

    def collect_wikipedia_nasdaq100(self) -> List[Dict]:
        """Collect NASDAQ 100 tickers from Wikipedia"""
        url = "https://en.wikipedia.org/wiki/NASDAQ-100"

        try:
            print("Collecting NASDAQ 100 from Wikipedia...")
            time.sleep(self.delay)

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for the companies table
            tables = soup.find_all('table', {'class': 'wikitable'})

            tickers = []
            for table in tables:
                # Check if this is the companies table
                headers = table.find_all('th')
                header_texts = [h.text.strip() for h in headers]

                if 'Company' in ' '.join(header_texts) or 'Symbol' in ' '.join(header_texts):
                    rows = table.find_all('tr')[1:]  # Skip header

                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            # Find ticker and company name
                            ticker = None
                            company_name = None

                            for col in cols:
                                text = col.text.strip()
                                # Look for typical ticker patterns
                                if re.match(r'^[A-Z]{1,5}(\.[A-Z])?$', text) and len(text) <= 7:
                                    ticker = text
                                elif len(text) > 3 and not any(char.isdigit() for char in text[:5]):
                                    company_name = text

                            if ticker and company_name:
                                tickers.append({
                                    'ticker': ticker.upper(),
                                    'company_name': company_name,
                                    'source': 'wikipedia_nasdaq100',
                                    'source_url': url
                                })

            print(f"Collected {len(tickers)} NASDAQ 100 companies from Wikipedia")
            return tickers

        except Exception as e:
            print(f"Error collecting NASDAQ 100: {e}")
            return []

    def collect_wikipedia_russell2000(self) -> List[Dict]:
        """Collect Russell 2000 tickers from Wikipedia sample"""
        # Russell 2000 is too large for Wikipedia, so we'll provide a sample
        # In practice, you'd need a different source for the full list

        print("Russell 2000: Providing sample (full list requires subscription service)")
        sample_russell = [
            {'ticker': 'FLWS', 'company_name': '1-800-Flowers.com'},
            {'ticker': 'TXG', 'company_name': '10x Genomics'},
            {'ticker': 'ABVC', 'company_name': 'ABVC BioPharma'},
            {'ticker': 'ACIC', 'company_name': 'American Coastal Insurance'},
            {'ticker': 'AADI', 'company_name': 'Aadi Bioscience'},
        ]

        tickers = []
        for item in sample_russell:
            tickers.append({
                'ticker': item['ticker'],
                'company_name': item['company_name'],
                'source': 'wikipedia_russell2000_sample',
                'source_url': 'https://en.wikipedia.org/wiki/Russell_2000_Index'
            })

        print(f"Collected {len(tickers)} Russell 2000 sample companies")
        return tickers

    def collect_finnhub_free_tickers(self) -> List[Dict]:
        """Try to collect tickers from Finnhub free API"""
        # Finnhub has a free tier but limited requests

        try:
            print("Checking Finnhub free API...")

            # Note: This would require a free API key from finnhub.io
            # For now, we'll skip this as it requires API key setup

            print("Finnhub requires API key - skipping for now")
            return []

        except Exception as e:
            print(f"Error with Finnhub: {e}")
            return []

    def collect_eod_historical_sample(self) -> List[Dict]:
        """Sample tickers that might be available from EOD Historical Data"""
        # EOD Historical Data has free tier but limited symbols

        print("EOD Historical Data: Free tier has limited symbols")
        sample_eod = [
            {'ticker': 'AAPL.US', 'company_name': 'Apple Inc'},
            {'ticker': 'MSFT.US', 'company_name': 'Microsoft Corporation'},
            {'ticker': 'GOOGL.US', 'company_name': 'Alphabet Inc'},
        ]

        tickers = []
        for item in sample_eod:
            tickers.append({
                'ticker': item['ticker'],
                'company_name': item['company_name'],
                'source': 'eod_historical_sample',
                'source_url': 'https://eodhistoricaldata.com/'
            })

        print(f"Collected {len(tickers)} EOD Historical Data samples")
        return tickers

    def save_tickers_to_db(self, tickers: List[Dict], source_name: str, description: str, url: str):
        """Save collected tickers to database"""

        if not tickers:
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Update source info
            cursor.execute('''
                INSERT OR REPLACE INTO sources
                (source_name, description, url, ticker_count, last_updated)
                VALUES (?, ?, ?, ?, ?)
            ''', (source_name, description, url, len(tickers), datetime.now().isoformat()))

            # Insert tickers
            for ticker in tickers:
                cursor.execute('''
                    INSERT OR IGNORE INTO tickers
                    (ticker, company_name, source, source_url, collected_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    ticker['ticker'],
                    ticker['company_name'],
                    ticker['source'],
                    ticker.get('source_url', ''),
                    datetime.now().isoformat()
                ))

            conn.commit()
            print(f"Saved {len(tickers)} tickers from {source_name} to database")

        except Exception as e:
            print(f"Error saving to database: {e}")
            conn.rollback()
        finally:
            conn.close()

    def collect_all_sources(self):
        """Collect tickers from all available sources"""

        print("Starting collection from all alternative sources...")
        print("=" * 60)

        # Collect from each source
        sources = [
            ('wikipedia_sp500', 'S&P 500 from Wikipedia', 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', self.collect_wikipedia_sp500),
            ('wikipedia_nasdaq100', 'NASDAQ 100 from Wikipedia', 'https://en.wikipedia.org/wiki/NASDAQ-100', self.collect_wikipedia_nasdaq100),
            ('wikipedia_russell2000', 'Russell 2000 sample', 'https://en.wikipedia.org/wiki/Russell_2000_Index', self.collect_wikipedia_russell2000),
            ('eod_historical', 'EOD Historical Data samples', 'https://eodhistoricaldata.com/', self.collect_eod_historical_sample),
        ]

        total_tickers = 0

        for source_name, description, url, collector_func in sources:
            print(f"\n{'='*40}")
            print(f"COLLECTING: {source_name}")
            print(f"{'='*40}")

            tickers = collector_func()

            if tickers:
                self.save_tickers_to_db(tickers, source_name, description, url)
                total_tickers += len(tickers)
            else:
                print(f"No tickers collected from {source_name}")

        print(f"\n{'='*60}")
        print("COLLECTION COMPLETE")
        print(f"{'='*60}")
        print(f"Total tickers collected: {total_tickers}")
        print(f"Database: {DB_PATH}")

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Collect tickers from alternative sources")
    parser.add_argument('--source', choices=['sp500', 'nasdaq100', 'russell2000', 'eod', 'all'],
                       default='all', help='Source to collect from')
    parser.add_argument('--delay', '-d', type=float, default=1.0,
                       help='Delay between requests (seconds)')

    args = parser.parse_args()

    collector = AlternativeTickerCollector(delay=args.delay)

    if args.source == 'all':
        collector.collect_all_sources()
    elif args.source == 'sp500':
        tickers = collector.collect_wikipedia_sp500()
        collector.save_tickers_to_db(tickers, 'wikipedia_sp500', 'S&P 500 from Wikipedia',
                                   'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    elif args.source == 'nasdaq100':
        tickers = collector.collect_wikipedia_nasdaq100()
        collector.save_tickers_to_db(tickers, 'wikipedia_nasdaq100', 'NASDAQ 100 from Wikipedia',
                                   'https://en.wikipedia.org/wiki/NASDAQ-100')
    elif args.source == 'russell2000':
        tickers = collector.collect_wikipedia_russell2000()
        collector.save_tickers_to_db(tickers, 'wikipedia_russell2000_sample', 'Russell 2000 sample',
                                   'https://en.wikipedia.org/wiki/Russell_2000_Index')
    elif args.source == 'eod':
        tickers = collector.collect_eod_historical_sample()
        collector.save_tickers_to_db(tickers, 'eod_historical_sample', 'EOD Historical Data samples',
                                   'https://eodhistoricaldata.com/')

if __name__ == '__main__':
    main()