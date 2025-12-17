#!/usr/bin/env python3
"""
Populate company names in the QuickFS tickers database using the API
"""

import sqlite3
import os
import sys
import time
import json
import argparse
from typing import List, Dict, Optional
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Change to project root directory
os.chdir(PROJECT_ROOT)

# Database path
DB_PATH = os.path.join(PROJECT_ROOT, 'quickfs_tickers', 'quickfs_tickers.db')

# Try to import config
try:
    from config import QUICKFS_API_KEY
    API_KEY = QUICKFS_API_KEY
except ImportError:
    API_KEY = os.environ.get('QUICKFS_API_KEY')
    if not API_KEY:
        print("Error: QuickFS API key not found.")
        sys.exit(1)

class QuickFSCompanyNamePopulator:
    """Populate company names in the QuickFS database using the API"""

    def __init__(self, db_path: str = DB_PATH, delay: float = 0.5):
        self.db_path = db_path
        self.delay = delay  # Delay between API calls
        self.client = None

    def init_client(self):
        """Initialize QuickFS client"""
        if self.client is None:
            from quickfs import QuickFS
            self.client = QuickFS(API_KEY)

    def get_db_connection(self):
        """Get database connection"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        return sqlite3.connect(self.db_path)

    def get_tickers_to_update(self, limit: Optional[int] = None, missing_only: bool = True) -> List[str]:
        """Get tickers that need company names"""
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

    def get_company_name(self, ticker: str) -> Optional[str]:
        """
        Get company name for a ticker using QuickFS API
        """
        try:
            self.init_client()

            # Format ticker for QuickFS API
            if ':' not in ticker:
                formatted_ticker = f"{ticker}:US"
            else:
                formatted_ticker = ticker

            # Get data using the API
            data = self.client.get_data_full(formatted_ticker)

            if data and 'metadata' in data:
                metadata = data['metadata']
                company_name = metadata.get('name')
                if company_name and company_name.strip():
                    return company_name.strip()

            return None

        except Exception as e:
            # Don't print errors for individual tickers unless debugging
            # print(f"API error for {ticker}: {e}")
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

    def populate_batch(self, tickers: List[str], batch_size: int = 50, save_progress: bool = True) -> Dict[str, int]:
        """
        Populate company names for a batch of tickers

        Args:
            tickers: List of ticker symbols
            batch_size: How many to process before saving progress
            save_progress: Whether to save progress to a file

        Returns:
            Dictionary with processing statistics
        """
        stats = {
            'total': len(tickers),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'processed': 0
        }

        progress_file = 'company_names_progress.json'

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

                # Get company name
                company_name = self.get_company_name(ticker)

                if company_name:
                    if self.update_company_name(ticker, company_name):
                        stats['successful'] += 1
                        print(f"[{i+1}/{len(tickers)}] SUCCESS {ticker} -> {company_name}")
                    else:
                        stats['failed'] += 1
                        print(f"[{i+1}/{len(tickers)}] FAILED Failed to update {ticker}")
                else:
                    stats['failed'] += 1
                    print(f"[{i+1}/{len(tickers)}] FAILED No company name found for {ticker}")

                stats['processed'] = i + 1
                processed_tickers.add(ticker)

                # Add delay between requests to be respectful
                time.sleep(self.delay)

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
            print("\nINTERRUPTED: Population stopped by user")
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
    parser = argparse.ArgumentParser(description="Populate company names in QuickFS tickers database")
    parser.add_argument('--limit', '-l', type=int, help='Limit number of tickers to process')
    parser.add_argument('--all', action='store_true', help='Process all tickers (overwrite existing names)')
    parser.add_argument('--missing', action='store_true', help='Only process tickers missing company names (default)')
    parser.add_argument('--delay', '-d', type=float, default=0.5, help='Delay between API calls (seconds)')
    parser.add_argument('--batch-size', '-b', type=int, default=50, help='Save progress every N tickers')

    args = parser.parse_args()

    # Validate arguments
    if not args.all and not args.limit and not args.missing:
        args.missing = True  # Default to missing only

    populator = QuickFSCompanyNamePopulator(delay=args.delay)

    # Get tickers to process
    if args.missing:
        tickers = populator.get_tickers_to_update(limit=args.limit, missing_only=True)
        print(f"Found {len(tickers)} tickers missing company names")
    else:
        tickers = populator.get_tickers_to_update(limit=args.limit, missing_only=False)
        print(f"Selected {len(tickers)} tickers to process")

    if not tickers:
        print("No tickers to process")
        return

    # Confirm before starting
    print(f"\nSTARTING: Ready to process {len(tickers)} tickers with {args.delay}s delay between requests")
    estimated_time = len(tickers) * args.delay / 60
    print(".1f")
    # Skip confirmation for automated processing
    print("Starting in 3 seconds... (Ctrl+C to cancel)")
    try:
        time.sleep(3)
    except KeyboardInterrupt:
        print("\nCancelled")
        return

    # Start processing
    start_time = time.time()
    stats = populator.populate_batch(tickers, batch_size=args.batch_size)
    end_time = time.time()

    # Print final results
    print(f"\n{'='*60}")
    print("POPULATION COMPLETE")
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
        final_stats = populator.get_db_connection().execute(
            "SELECT COUNT(*) as total, COUNT(company_name) as with_names FROM tickers"
        ).fetchone()
        print(f"\nDatabase status:")
        print(f"  Total tickers: {final_stats[0]}")
        print(f"  With company names: {final_stats[1]}")
        print(".1f")
    except Exception as e:
        print(f"Could not get final database stats: {e}")

if __name__ == '__main__':
    main()