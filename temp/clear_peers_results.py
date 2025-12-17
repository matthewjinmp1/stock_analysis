#!/usr/bin/env python3
"""
Clear all data from peers_results.db
"""

import sqlite3
import os

def clear_peers_results_db():
    """Clear all data from the peers results database"""

    db_path = 'web_app/peers/peers_results.db'

    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Get count before clearing
    cur.execute('SELECT COUNT(*) FROM peer_results')
    count_before = cur.fetchone()[0]
    print(f"Records before clearing: {count_before}")

    # Clear all data
    cur.execute('DELETE FROM peer_results')

    # Reset auto-increment counter
    cur.execute('DELETE FROM sqlite_sequence WHERE name="peer_results"')

    conn.commit()

    # Verify clearing
    cur.execute('SELECT COUNT(*) FROM peer_results')
    count_after = cur.fetchone()[0]
    print(f"Records after clearing: {count_after}")

    conn.close()

    if count_after == 0:
        print("Successfully cleared peers_results.db")
    else:
        print(f"Failed to clear database - {count_after} records still remain")

if __name__ == "__main__":
    print("Clearing peers_results.db...")
    clear_peers_results_db()