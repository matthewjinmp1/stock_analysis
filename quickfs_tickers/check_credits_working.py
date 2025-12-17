#!/usr/bin/env python3
"""
Working QuickFS credit checker based on the quantitative_stock_scorer version
"""
from quickfs import QuickFS
from datetime import datetime
import json
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Change to project root directory
os.chdir(PROJECT_ROOT)

# Try to import config
try:
    from config import QUICKFS_API_KEY
    API_KEY = QUICKFS_API_KEY
except ImportError:
    API_KEY = os.environ.get('QUICKFS_API_KEY')
    if not API_KEY:
        print("Error: QuickFS API key not found.")
        sys.exit(1)

def check_credits():
    """
    Check and display QuickFS API credit usage
    """
    try:
        print("Checking QuickFS API credits...")
        print("=" * 60)

        client = QuickFS(API_KEY)
        usage = client.get_usage()

        if not usage or "quota" not in usage:
            print("Error: Could not retrieve usage information")
            print(f"Raw response: {usage}")
            return

        quota = usage["quota"]
        used = quota.get("used", 0)
        remaining = quota.get("remaining", 0)
        resets_str = quota.get("resets", "")

        # Calculate total quota
        total = used + remaining

        # Parse reset time
        reset_time = None
        if resets_str:
            try:
                # Parse ISO format datetime
                reset_time = datetime.fromisoformat(resets_str.replace('Z', '+00:00'))
                # Convert to local time (remove timezone for display)
                reset_time = reset_time.replace(tzinfo=None)
            except:
                pass

        # Display information
        print(f"\nQuickFS API Credit Status")
        print(f"{'=' * 60}")
        print(f"Total Quota:     {total:,}")
        print(f"Credits Used:    {used:,}")
        print(f"Credits Remaining: {remaining:,}")

        # Calculate percentage
        if total > 0:
            used_pct = (used / total) * 100
            remaining_pct = (remaining / total) * 100
            print(f"\nUsage:           {used_pct:.1f}%")
            print(f"Remaining:       {remaining_pct:.1f}%")

        # Display reset time
        if reset_time:
            print(f"\nQuota Resets:    {reset_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print(f"                ({reset_time.strftime('%B %d, %Y at %I:%M %p')} UTC)")

        # Visual progress bar
        if total > 0:
            bar_length = 50
            used_bars = int((used / total) * bar_length)
            remaining_bars = bar_length - used_bars

            print(f"\nProgress Bar:")
            print(f"[{'#' * used_bars}{'.' * remaining_bars}]")
            print(f" {'Used':<10} {'Remaining':>10}")

        # Warning if low on credits
        if remaining < 100:
            print(f"\nWARNING: Low on credits! Only {remaining} remaining.")
        elif remaining < 1000:
            print(f"\nNote: {remaining} credits remaining. Consider monitoring usage.")
        else:
            print(f"\nYou have plenty of credits remaining.")

        print(f"\n{'=' * 60}")

        # Show cost for company name population
        print("Company Name Population Cost:")
        print("-" * 40)
        print(f"Missing names:   17,272 tickers")
        print(f"Cost per ticker: 1 credit")
        print(f"Total cost:      17,272 credits")

        if remaining >= 17272:
            print(f"Status:          ENOUGH credits available")
        else:
            shortage = 17272 - remaining
            print(f"Status:          NEED {shortage:,} more credits")

        return usage

    except Exception as e:
        print(f"Error checking credits: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """
    Main function to check QuickFS credits
    """
    check_credits()

if __name__ == "__main__":
    main()