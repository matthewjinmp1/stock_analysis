"""
Program to check remaining QuickFS API credits for the day
"""
import sys
import os
import requests
from datetime import datetime

# Add current directory to path for config
sys.path.insert(0, os.path.dirname(__file__))

try:
    from config import QUICKFS_API_KEY
except ImportError:
    print("Error: Could not import QUICKFS_API_KEY from config.py")
    print("Make sure config.py exists in the same directory as this script")
    sys.exit(1)

def check_credits():
    """
    Check and display QuickFS API credit usage by calling the API directly
    """
    try:
        print("Checking QuickFS API credits...")
        print("=" * 60)

        # Try using QuickFS library first
        usage = None
        try:
            from quickfs import QuickFS
            print("Connecting to QuickFS API...")
            client = QuickFS(QUICKFS_API_KEY)
            usage = client.get_usage()
            print("Successfully retrieved usage information")
        except Exception as e:
            print(f"Failed to retrieve usage information: {e}")
            usage = None

        if usage is None:
            print("Failed to retrieve usage information")
            print("You may need to check your QuickFS account dashboard manually:")
            print("https://quickfs.net/dashboard or https://quickfs.net/account")
            return

        print("Successfully retrieved usage information")

        # Check if we have the expected structure
        if not isinstance(usage, dict):
            print(f"Unexpected response format: {type(usage)}")
            print(f"Response: {usage}")
            return

        # Extract quota information
        quota = usage.get("quota", {})
        if not quota:
            print("No quota information found in response")
            print(f"Available keys: {list(usage.keys())}")
            return

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
            except Exception as e:
                print(f"Could not parse reset time: {e}")

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

