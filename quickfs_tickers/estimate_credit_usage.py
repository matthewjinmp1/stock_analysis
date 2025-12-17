#!/usr/bin/env python3
"""
Estimate QuickFS credit usage for company name population
"""

import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Change to project root directory
os.chdir(PROJECT_ROOT)

def estimate_credits_needed():
    """Estimate credits needed for company name population"""

    # Database path
    DB_PATH = os.path.join(PROJECT_ROOT, 'quickfs_tickers', 'quickfs_tickers.db')

    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get total tickers
        cursor.execute('SELECT COUNT(*) FROM tickers')
        total_tickers = cursor.fetchone()[0]

        # Get tickers without company names
        cursor.execute('SELECT COUNT(*) FROM tickers WHERE company_name IS NULL OR company_name = ""')
        missing_names = cursor.fetchone()[0]

        # Get tickers with company names
        cursor.execute('SELECT COUNT(*) FROM tickers WHERE company_name IS NOT NULL AND company_name != ""')
        with_names = cursor.fetchone()[0]

        conn.close()

        print("QuickFS Credit Usage Estimation")
        print("=" * 60)
        print(f"Total tickers in database: {total_tickers}")
        print(f"Tickers with company names: {with_names}")
        print(f"Tickers missing company names: {missing_names}")
        print()

        if missing_names > 0:
            print("Credit Cost Analysis:")
            print(f"  Each missing company name costs: 1 credit")
            print(f"  Total credits needed: {missing_names} credits")
            print()

            # Estimate time
            print("Time Estimation (at 0.5s delay between calls):")
            total_seconds = missing_names * 0.5
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            print(f"  Estimated time: {hours}h {minutes}m {seconds}s")
            print()

            # Daily limits (assuming standard limits)
            print("Daily Credit Limits (typical):")
            print("  QuickFS typically allows 1,000-5,000 credits per day")
            print("  Check your plan at https://quickfs.net/")
            print()

            print("Batch Processing Recommendations:")
            batch_sizes = [100, 500, 1000, 5000]
            for batch in batch_sizes:
                batches_needed = (missing_names + batch - 1) // batch  # Ceiling division
                print(f"  {batch} tickers per day: {batches_needed} days needed")

        else:
            print("✅ All tickers already have company names!")
            print("No additional credits needed.")

        print("\n" + "=" * 60)
        print("IMPORTANT: Check your actual credit balance at https://quickfs.net/")
        print("Different plans have different daily/monthly limits.")
        print("=" * 60)

    except Exception as e:
        print(f"Error: {e}")
        print("Could not access database. Make sure quickfs_tickers.db exists.")

if __name__ == '__main__':
    estimate_credits_needed()