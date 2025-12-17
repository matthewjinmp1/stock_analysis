#!/usr/bin/env python3
"""
Migrate peers_results.db to include peer_ticker column
"""

import sqlite3
import json

def migrate_peers_results_db():
    """Migrate peers_results.db to include peer_ticker column"""

    db_path = 'web_app/peers/peers_results.db'

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Get existing data
    cur.execute('SELECT * FROM peer_results')
    existing_data = cur.fetchall()

    # Get column names
    cur.execute('PRAGMA table_info(peer_results)')
    old_columns = [row[1] for row in cur.fetchall()]

    print(f"Found {len(existing_data)} existing records")
    print(f"Old columns: {old_columns}")

    # Create new table with peer_ticker column
    cur.execute('DROP TABLE IF EXISTS peer_results_new')
    cur.execute('''
        CREATE TABLE peer_results_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            company_name TEXT,
            peer_name TEXT NOT NULL,
            peer_ticker TEXT,
            peer_rank INTEGER NOT NULL,
            token_usage_json TEXT,
            estimated_cost_cents REAL,
            analysis_timestamp TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert existing data (peer_ticker will be NULL)
    for row in existing_data:
        # Map old row data to new columns (peer_ticker will be NULL)
        new_row = list(row)
        # Insert NULL for peer_ticker (position 4, after peer_name at position 3)
        new_row.insert(4, None)
        cur.execute('''
            INSERT INTO peer_results_new
            (id, ticker, company_name, peer_name, peer_ticker, peer_rank,
             token_usage_json, estimated_cost_cents, analysis_timestamp, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', new_row)

    # Replace old table with new one
    cur.execute('DROP TABLE peer_results')
    cur.execute('ALTER TABLE peer_results_new RENAME TO peer_results')

    # Recreate indexes
    cur.execute('CREATE INDEX IF NOT EXISTS idx_peer_results_ticker ON peer_results(ticker)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_peer_results_timestamp ON peer_results(analysis_timestamp)')

    conn.commit()

    # Verify the migration
    cur.execute('PRAGMA table_info(peer_results)')
    new_columns = [row[1] for row in cur.fetchall()]

    cur.execute('SELECT COUNT(*) FROM peer_results')
    new_count = cur.fetchone()[0]

    print(f"New columns: {new_columns}")
    print(f"Records after migration: {new_count}")

    if 'peer_ticker' in new_columns and new_count == len(existing_data):
        print("✅ Migration successful!")
    else:
        print("❌ Migration failed!")

    conn.close()

if __name__ == "__main__":
    print("Migrating peers_results.db to include peer_ticker column...")
    migrate_peers_results_db()