#!/usr/bin/env python3
"""
YFinance Ticker Collector
Uses yfinance to collect and validate stock tickers from various sources

YFinance doesn't provide a direct method to get "all available tickers",
but this script demonstrates several approaches:
1. Major stock indices (S&P 500, NASDAQ 100, etc.)
2. Ticker validation and company info extraction
3. Database storage of validated tickers
"""

import yfinance as yf
import json
import sqlite3
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Optional, Set

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Database path
DB_PATH = os.path.join(PROJECT_ROOT, 'yfinance_tickers', 'yfinance_tickers.db')

class YFinanceTickerCollector:
    """Collect and validate tickers using yfinance"""

    def __init__(self, db_path: str = DB_PATH, delay: float = 0.1):
        self.db_path = db_path
        self.delay = delay  # Delay between API calls

    def get_db_connection(self):
        """Get database connection"""
        if not os.path.exists(self.db_path):
            self.init_database()
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize the database with proper schema"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create main tickers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickers (
                ticker TEXT PRIMARY KEY,
                company_name TEXT,
                sector TEXT,
                industry TEXT,
                country TEXT DEFAULT 'US',
                source TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_valid BOOLEAN DEFAULT 1
            )
        ''')

        # Create index table for different sources
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticker_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT UNIQUE,
                description TEXT,
                ticker_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON tickers(ticker)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON tickers(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sector ON tickers(sector)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_country ON tickers(country)')

        conn.commit()
        conn.close()

    def get_sp500_tickers(self) -> List[str]:
        """Get S&P 500 tickers using yfinance"""
        try:
            # yfinance has a built-in method for S&P 500
            sp500 = yf.Ticker("^GSPC")  # S&P 500 index

            # Get the holdings/components if available
            # Note: This might not work as expected with indices
            print("Note: yfinance doesn't directly provide S&P 500 constituents")
            print("Consider using wikipedia or other sources for complete lists")

            # For demonstration, return a small sample
            # In practice, you'd want to use a more comprehensive source
            sample_sp500 = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
                'BABA', 'ORCL', 'CRM', 'AMD', 'INTC', 'CSCO', 'ADBE', 'PYPL'
            ]

            return sample_sp500

        except Exception as e:
            print(f"Error getting S&P 500 tickers: {e}")
            return []

    def get_nasdaq100_tickers(self) -> List[str]:
        """Get NASDAQ 100 tickers"""
        try:
            # Similar limitation - yfinance doesn't provide constituent lists
            sample_nasdaq100 = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
                'BABA', 'ORCL', 'CRM', 'AMD', 'INTC', 'CSCO', 'ADBE', 'PYPL',
                'QCOM', 'TXN', 'AVGO', 'COST', 'TMUS', 'HON', 'LIN', 'AMGN'
            ]

            return sample_nasdaq100

        except Exception as e:
            print(f"Error getting NASDAQ 100 tickers: {e}")
            return []

    def validate_ticker(self, ticker: str) -> Optional[Dict]:
        """
        Validate a ticker and get company information using yfinance

        Returns dict with company info if valid, None if invalid
        """
        try:
            # Add delay to be respectful
            time.sleep(self.delay)

            # Create ticker object
            stock = yf.Ticker(ticker)

            # Try to get basic info
            info = stock.info

            if not info or len(info) < 5:
                # Not enough info suggests invalid ticker
                return None

            # Extract useful information
            company_info = {
                'ticker': ticker.upper(),
                'company_name': info.get('longName') or info.get('shortName'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'country': info.get('country', 'US'),
                'market_cap': info.get('marketCap'),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange'),
                'website': info.get('website'),
                'is_valid': True
            }

            # Only return if we have at least a company name
            if company_info['company_name']:
                return company_info
            else:
                return None

        except Exception as e:
            # Ticker is likely invalid
            return None

    def collect_from_list(self, tickers: List[str], source: str, description: str = "") -> Dict[str, int]:
        """
        Collect and validate tickers from a provided list

        Args:
            tickers: List of ticker symbols to validate
            source: Source identifier (e.g., 'sp500', 'nasdaq100')
            description: Human-readable description

        Returns:
            Dictionary with collection statistics
        """
        stats = {
            'total_attempted': len(tickers),
            'valid_found': 0,
            'invalid_skipped': 0,
            'errors': 0,
            'processed': 0
        }

        print(f"\nCollecting from {source} ({len(tickers)} tickers)")
        print("=" * 60)

        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            for i, ticker in enumerate(tickers):
                if ticker:
                    ticker_info = self.validate_ticker(ticker.strip().upper())

                    if ticker_info:
                        # Insert/update ticker info
                        cursor.execute('''
                            INSERT OR REPLACE INTO tickers
                            (ticker, company_name, sector, industry, country, source, last_updated, is_valid)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            ticker_info['ticker'],
                            ticker_info['company_name'],
                            ticker_info['sector'],
                            ticker_info['industry'],
                            ticker_info['country'],
                            source,
                            datetime.now().isoformat(),
                            ticker_info['is_valid']
                        ))

                        stats['valid_found'] += 1
                        print(f"[{i+1:4d}/{len(tickers)}] SUCCESS {ticker} -> {ticker_info['company_name']}")

                    else:
                        stats['invalid_skipped'] += 1
                        print(f"[{i+1:4d}/{len(tickers)}] INVALID {ticker} (invalid/not found)")

                stats['processed'] = i + 1

                # Save progress every 50 tickers
                if (i + 1) % 50 == 0:
                    conn.commit()
                    print(f"  PROGRESS SAVED ({i+1}/{len(tickers)})")

            # Update source info
            cursor.execute('''
                INSERT OR REPLACE INTO ticker_sources
                (source_name, description, ticker_count, last_updated)
                VALUES (?, ?, ?, ?)
            ''', (source, description, stats['valid_found'], datetime.now().isoformat()))

            conn.commit()

        except Exception as e:
            print(f"Error during collection: {e}")
            stats['errors'] += 1
            conn.rollback()
        finally:
            conn.close()

        return stats

    def get_popular_tickers(self) -> List[str]:
        """Get a list of popular/well-known tickers to test"""
        return [
            # Tech giants
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX',

            # Financial
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'AXP', 'V',

            # Healthcare
            'JNJ', 'PFE', 'MRK', 'ABBV', 'TMO', 'DHR', 'ABT', 'MDT',

            # Consumer
            'KO', 'PEP', 'WMT', 'HD', 'MCD', 'DIS', 'VZ', 'T',

            # Energy
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PSX', 'VLO',

            # Industrial
            'BA', 'CAT', 'GE', 'MMM', 'HON', 'LMT', 'RTX',

            # Materials
            'LIN', 'APD', 'ECL', 'PPG', 'SHW'
        ]

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Collect and validate tickers using yfinance")
    parser.add_argument('--source', choices=['sp500', 'nasdaq100', 'popular', 'all'],
                       default='popular', help='Source of tickers to collect')
    parser.add_argument('--delay', '-d', type=float, default=0.1,
                       help='Delay between API calls (seconds)')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of tickers to process')

    args = parser.parse_args()

    print("YFinance Ticker Collector")
    print("=" * 50)

    collector = YFinanceTickerCollector(delay=args.delay)

    # Get tickers based on source
    if args.source == 'sp500':
        tickers = collector.get_sp500_tickers()
        source_name = 'sp500'
        description = 'S&P 500 Index Constituents (sample)'
    elif args.source == 'nasdaq100':
        tickers = collector.get_nasdaq100_tickers()
        source_name = 'nasdaq100'
        description = 'NASDAQ 100 Index Constituents (sample)'
    elif args.source == 'popular':
        tickers = collector.get_popular_tickers()
        source_name = 'popular'
        description = 'Popular/well-known US stocks'
    else:  # 'all'
        # Combine multiple sources
        sp500 = collector.get_sp500_tickers()
        nasdaq100 = collector.get_nasdaq100_tickers()
        popular = collector.get_popular_tickers()

        # Remove duplicates
        all_tickers = list(set(sp500 + nasdaq100 + popular))
        tickers = all_tickers
        source_name = 'combined'
        description = 'Combined from multiple sources'

    # Apply limit if specified
    if args.limit and args.limit < len(tickers):
        tickers = tickers[:args.limit]

    print(f"Source: {source_name}")
    print(f"Description: {description}")
    print(f"Tickers to process: {len(tickers)}")
    print(f"Delay between calls: {args.delay}s")
    print()

    # Confirm before starting
    estimated_time = len(tickers) * args.delay / 60
    print(f"Estimated time: {estimated_time:.1f} minutes")

    # Skip confirmation for automated processing
    print("Starting in 2 seconds... (Ctrl+C to cancel)")
    try:
        time.sleep(2)
    except KeyboardInterrupt:
        print("\nCancelled")
        return

    # Start collection
    start_time = time.time()
    stats = collector.collect_from_list(tickers, source_name, description)
    end_time = time.time()

    # Print final results
    print(f"\n{'='*60}")
    print("COLLECTION COMPLETE")
    print(f"{'='*60}")
    print(f"Total attempted: {stats['total_attempted']}")
    print(f"Valid tickers: {stats['valid_found']}")
    print(f"Invalid tickers: {stats['invalid_skipped']}")
    print(f"Errors: {stats['errors']}")
    print(f"Success rate: {stats['valid_found']/stats['total_attempted']*100:.1f}%" if stats['total_attempted'] > 0 else "N/A")
    print(f"Time taken: {end_time - start_time:.1f} seconds")
    print(".1f")
    print(f"Database: {DB_PATH}")

if __name__ == '__main__':
    main()