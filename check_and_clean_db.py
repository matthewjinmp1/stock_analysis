#!/usr/bin/env python3
"""
Check peers database contents and remove test entries.
"""

import sys
import os
import sqlite3

# Add project root to path
current_dir = os.path.abspath(os.path.dirname(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def check_database_contents():
    """Check what entries are in the database."""
    db_path = os.path.join(current_dir, 'web_app', 'peers', 'peers_results.db')

    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Get all entries
    cur.execute("SELECT id, ticker, company_name, peer_name, analysis_timestamp FROM peer_results ORDER BY analysis_timestamp DESC")
    rows = cur.fetchall()

    print("Current database contents:")
    print("=" * 80)

    for row in rows:
        id_val, ticker, company_name, peer_name, timestamp = row
        print(f"ID: {id_val}, Ticker: {ticker}, Company: {company_name}, Peer: {peer_name}, Time: {timestamp}")

    print(f"\nTotal entries: {len(rows)}")

    # Check for test entries
    cur.execute("SELECT DISTINCT ticker FROM peer_results WHERE ticker = 'TEST'")
    test_entries = cur.fetchall()

    if test_entries:
        print(f"\nFound {len(test_entries)} test entries with ticker 'TEST'")
        return True
    else:
        print("\nNo test entries found.")
        return False

    conn.close()

def remove_test_entries():
    """Remove test entries from database."""
    db_path = os.path.join(current_dir, 'web_app', 'peers', 'peers_results.db')

    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Delete test entries
    cur.execute("DELETE FROM peer_results WHERE ticker = 'TEST'")
    deleted_count = cur.rowcount

    conn.commit()
    conn.close()

    print(f"Removed {deleted_count} test entries from database.")

def main():
    """Main function."""
    print("Checking peers database contents...")

    has_test_entries = check_database_contents()

    if has_test_entries:
        print("\nAutomatically removing test entries...")
        remove_test_entries()
        print("\nChecking database after cleanup...")
        check_database_contents()
    else:
        print("No cleanup needed.")

if __name__ == "__main__":
    main()