#!/usr/bin/env python3
"""
Migrate peers.db from ticker-based to company-name-based storage.
"""

import sqlite3
import os

def get_ticker_to_company_mapping():
    """Get mapping from ticker to company name."""
    tickers_db = 'web_app/data/tickers.db'
    if not os.path.exists(tickers_db):
        print(f"Warning: Tickers database not found at {tickers_db}")
        return {}

    conn = sqlite3.connect(tickers_db)
    cur = conn.cursor()
    cur.execute("SELECT ticker, company_name FROM tickers")
    mapping = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()
    return mapping

def migrate_peers_db():
    """Migrate peers.db to use company names instead of tickers."""
    peers_db = 'web_app/data/peers.db'
    if not os.path.exists(peers_db):
        print(f"Peers database not found at {peers_db}")
        return

    # Get ticker to company mapping
    ticker_to_company = get_ticker_to_company_mapping()
    print(f"Loaded {len(ticker_to_company)} ticker->company mappings")

    conn = sqlite3.connect(peers_db)
    cur = conn.cursor()

    # Get existing data
    cur.execute("SELECT ticker, peer_ticker, rank FROM peers")
    existing_peers = cur.fetchall()
    print(f"Found {len(existing_peers)} existing peer relationships")

    # Create new table with company names
    cur.execute("DROP TABLE IF EXISTS peers_new")
    cur.execute('''
        CREATE TABLE peers_new (
            company_name TEXT NOT NULL,
            peer_company_name TEXT NOT NULL,
            rank INTEGER NOT NULL,
            PRIMARY KEY (company_name, peer_company_name)
        )
    ''')

    # Migrate data
    migrated_count = 0
    skipped_count = 0

    for ticker, peer_ticker, rank in existing_peers:
        company_name = ticker_to_company.get(ticker.upper())
        peer_company_name = ticker_to_company.get(peer_ticker.upper())

        if company_name and peer_company_name:
            try:
                cur.execute('''
                    INSERT INTO peers_new (company_name, peer_company_name, rank)
                    VALUES (?, ?, ?)
                ''', (company_name, peer_company_name, rank))
                migrated_count += 1
            except sqlite3.IntegrityError:
                # Skip duplicates
                pass
        else:
            skipped_count += 1
            if not company_name:
                print(f"Warning: No company name found for ticker '{ticker}'")
            if not peer_company_name:
                print(f"Warning: No company name found for peer ticker '{peer_ticker}'")

    # Replace old table with new one
    cur.execute("DROP TABLE peers")
    cur.execute("ALTER TABLE peers_new RENAME TO peers")

    # Create index for faster lookups
    cur.execute('''
        CREATE INDEX IF NOT EXISTS idx_company_name ON peers(company_name)
    ''')

    conn.commit()
    conn.close()

    print(f"Migration complete: {migrated_count} relationships migrated, {skipped_count} skipped")

def update_peers_db_functions():
    """Update the peers_db.py functions to work with company names."""
    # This will be done by modifying peers_db.py directly
    pass

if __name__ == "__main__":
    print("Starting peers database migration...")
    migrate_peers_db()
    print("Migration completed!")