#!/usr/bin/env python3
"""
Database for storing AI-generated peer analysis results.
Stores peer finding results with metadata, token usage, and costs.
"""

import os
import sqlite3
import json
from typing import List, Dict, Optional, Any, Union
from datetime import datetime

# Database path
PEERS_RESULTS_DB = os.path.join(os.path.dirname(__file__), "peers_results.db")

def init_peers_results_db() -> None:
    """Initialize the peers results database."""
    os.makedirs(os.path.dirname(PEERS_RESULTS_DB), exist_ok=True)
    conn = sqlite3.connect(PEERS_RESULTS_DB)
    cur = conn.cursor()

    # Create peer analysis results table (one peer per row)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS peer_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            company_name TEXT,
            peer_name TEXT NOT NULL,        -- Individual peer company name
            peer_ticker TEXT,               -- Individual peer ticker symbol (if available)
            peer_rank INTEGER NOT NULL,     -- Position in peer list (1-10)
            token_usage_json TEXT,          -- JSON object with token usage details
            estimated_cost_cents REAL,      -- Cost per analysis (duplicated across peers)
            analysis_timestamp TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker, peer_name, analysis_timestamp)
        )
        """
    )

    # Create indexes for better query performance
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_peer_results_ticker ON peer_results(ticker)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_peer_results_timestamp ON peer_results(analysis_timestamp)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_peer_results_peer_name ON peer_results(peer_name)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_peer_results_rank ON peer_results(peer_rank)"
    )

    conn.commit()
    conn.close()

def save_peer_analysis(
    ticker: str,
    company_name: str,
    peers: List[Union[str, Dict[str, Any]]],
    token_usage: Optional[Dict[str, Any]] = None,
    estimated_cost_cents: Optional[float] = None,
    analysis_timestamp: Optional[str] = None
) -> bool:
    """
    Save peer analysis results to database - one peer per row.

    Args:
        ticker: Stock ticker symbol
        company_name: Full company name
        peers: List of peer company names (strings) or peer data (dicts with 'name' and 'ticker' keys)
        token_usage: Dictionary with token usage details
        estimated_cost_cents: Cost in cents
        analysis_timestamp: ISO timestamp of analysis

    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        init_peers_results_db()

        if analysis_timestamp is None:
            analysis_timestamp = datetime.now().isoformat()

        conn = sqlite3.connect(PEERS_RESULTS_DB)
        cur = conn.cursor()

        # Delete all existing peer results for this ticker before inserting new ones
        cur.execute("DELETE FROM peer_results WHERE ticker = ?", (ticker,))

        # Convert token usage to JSON for storage
        token_usage_json = json.dumps(token_usage) if token_usage else None

        # Insert one row per peer
        for rank, peer_data in enumerate(peers, start=1):
            # Handle both old format (string) and new format (dict)
            if isinstance(peer_data, dict):
                peer_name = peer_data.get('name', '')
                peer_ticker = peer_data.get('ticker')
            else:
                # Backward compatibility: peer_data is a string
                peer_name = peer_data
                peer_ticker = None

            cur.execute(
                """
                INSERT OR REPLACE INTO peer_results
                (ticker, company_name, peer_name, peer_ticker, peer_rank, token_usage_json,
                 estimated_cost_cents, analysis_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticker,
                    company_name,
                    peer_name,
                    peer_ticker,
                    rank,
                    token_usage_json,
                    estimated_cost_cents,
                    analysis_timestamp
                )
            )

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"Error saving peer analysis: {e}")
        return False

def get_peer_analysis(ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get peer analysis history for a ticker.

    Args:
        ticker: Stock ticker symbol
        limit: Maximum number of analyses to return

    Returns:
        List of peer analysis records, grouped by analysis_timestamp
    """
    try:
        init_peers_results_db()
        conn = sqlite3.connect(PEERS_RESULTS_DB)
        cur = conn.cursor()

        # Get distinct analysis timestamps for this ticker
        cur.execute(
            """
            SELECT DISTINCT analysis_timestamp
            FROM peer_results
            WHERE ticker = ?
            ORDER BY analysis_timestamp DESC
            LIMIT ?
            """,
            (ticker, limit)
        )

        timestamps = [row[0] for row in cur.fetchall()]

        results = []
        for analysis_timestamp in timestamps:
            # Get all peers for this analysis
            cur.execute(
                """
                SELECT ticker, company_name, peer_name, peer_ticker, peer_rank, token_usage_json,
                       estimated_cost_cents, created_at
                FROM peer_results
                WHERE ticker = ? AND analysis_timestamp = ?
                ORDER BY peer_rank ASC
                """,
                (ticker, analysis_timestamp)
            )

            peer_rows = cur.fetchall()
            if not peer_rows:
                continue

            # Extract data from first row (shared across all peers)
            ticker_name, company_name, _, _, _, token_usage_json, \
            estimated_cost_cents, created_at = peer_rows[0]

            # Parse token usage
            token_usage = json.loads(token_usage_json) if token_usage_json else None

            # Extract peer names and tickers
            peers = []
            for row in peer_rows:
                peer_name = row[2]  # peer_name column
                peer_ticker = row[3]  # peer_ticker column
                peers.append({
                    "name": peer_name,
                    "ticker": peer_ticker
                })

            results.append({
                "ticker": ticker_name,
                "company_name": company_name,
                "peers": peers,
                "peer_count": len(peers),
                "token_usage": token_usage,
                "estimated_cost_cents": estimated_cost_cents,
                "analysis_timestamp": analysis_timestamp,
                "created_at": created_at
            })

        conn.close()
        return results

    except Exception as e:
        print(f"Error retrieving peer analysis: {e}")
        return []

def get_all_peer_analyses(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get all peer analyses from database.

    Args:
        limit: Maximum number of analyses to return

    Returns:
        List of all peer analysis records, grouped by analysis
    """
    try:
        init_peers_results_db()
        conn = sqlite3.connect(PEERS_RESULTS_DB)
        cur = conn.cursor()

        # Get distinct analysis timestamps
        cur.execute(
            """
            SELECT DISTINCT ticker, analysis_timestamp
            FROM peer_results
            ORDER BY analysis_timestamp DESC
            LIMIT ?
            """,
            (limit,)
        )

        analysis_keys = [(row[0], row[1]) for row in cur.fetchall()]  # (ticker, timestamp)

        results = []
        for ticker, analysis_timestamp in analysis_keys:
            # Get all peers for this analysis
            cur.execute(
                """
                SELECT ticker, company_name, peer_name, peer_rank, token_usage_json,
                       estimated_cost_cents, created_at
                FROM peer_results
                WHERE ticker = ? AND analysis_timestamp = ?
                ORDER BY peer_rank ASC
                """,
                (ticker, analysis_timestamp)
            )

            peer_rows = cur.fetchall()
            if not peer_rows:
                continue

            # Extract data from first row (shared across all peers)
            ticker_name, company_name, _, _, _, token_usage_json, \
            estimated_cost_cents, created_at = peer_rows[0]

            # Parse token usage
            token_usage = json.loads(token_usage_json) if token_usage_json else None

            # Extract peer names and tickers
            peers = []
            for row in peer_rows:
                peer_name = row[2]  # peer_name column
                peer_ticker = row[3]  # peer_ticker column
                peers.append({
                    "name": peer_name,
                    "ticker": peer_ticker
                })

            results.append({
                "ticker": ticker_name,
                "company_name": company_name,
                "peers": peers,
                "peer_count": len(peers),
                "token_usage": token_usage,
                "estimated_cost_cents": estimated_cost_cents,
                "analysis_timestamp": analysis_timestamp,
                "created_at": created_at
            })

        conn.close()
        return results

    except Exception as e:
        print(f"Error retrieving peer analyses: {e}")
        return []

def migrate_from_json_schema():
    """
    Migrate existing data from old JSON schema to new normalized schema.
    This should be run once to convert existing data.
    """
    try:
        # Check if old table exists
        conn = sqlite3.connect(PEERS_RESULTS_DB)
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='peer_analysis'")
        old_table_exists = cur.fetchone()

        if not old_table_exists:
            print("No old peer_analysis table found - nothing to migrate")
            conn.close()
            return True

        print("Found old peer_analysis table - migrating data...")

        # Get all existing data
        cur.execute("SELECT * FROM peer_analysis")
        old_rows = cur.fetchall()

        if not old_rows:
            print("No data to migrate")
            conn.close()
            return True

        # Initialize new schema
        init_peers_results_db()

        migrated_count = 0
        for row in old_rows:
            try:
                (id_val, ticker, company_name, peers_json, peer_count,
                 token_usage_json, estimated_cost_cents, analysis_timestamp, created_at) = row

                # Parse peers from JSON
                peers = json.loads(peers_json)

                # Insert each peer as separate row
                for rank, peer_name in enumerate(peers, start=1):
                    cur.execute(
                        """
                        INSERT INTO peer_results
                        (ticker, company_name, peer_name, peer_rank, token_usage_json,
                         estimated_cost_cents, analysis_timestamp, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            ticker,
                            company_name,
                            peer_name,
                            rank,
                            token_usage_json,
                            estimated_cost_cents,
                            analysis_timestamp,
                            created_at
                        )
                    )

                migrated_count += 1

            except Exception as e:
                print(f"Error migrating row {id_val}: {e}")
                continue

        # Drop old table
        cur.execute("DROP TABLE peer_analysis")

        conn.commit()
        conn.close()

        print(f"Successfully migrated {migrated_count} analyses")
        return True

    except Exception as e:
        print(f"Error during migration: {e}")
        return False

def get_peer_analysis_stats() -> Dict[str, Any]:
    """
    Get statistics about peer analyses in the database.

    Returns:
        Dictionary with database statistics
    """
    try:
        init_peers_results_db()
        conn = sqlite3.connect(PEERS_RESULTS_DB)
        cur = conn.cursor()

        # Get total analyses (unique timestamp+ticker combinations)
        cur.execute("SELECT COUNT(DISTINCT analysis_timestamp || '_' || ticker) FROM peer_results")
        total_analyses = cur.fetchone()[0]

        # Get unique tickers analyzed
        cur.execute("SELECT COUNT(DISTINCT ticker) FROM peer_results")
        unique_tickers = cur.fetchone()[0]

        # Get total cost (sum unique costs per analysis)
        cur.execute("""
            SELECT SUM(estimated_cost_cents)
            FROM (
                SELECT DISTINCT analysis_timestamp, ticker, estimated_cost_cents
                FROM peer_results
                WHERE estimated_cost_cents IS NOT NULL
            )
        """)
        total_cost_cents = cur.fetchone()[0] or 0

        # Get most recent analysis
        cur.execute("SELECT MAX(analysis_timestamp) FROM peer_results")
        latest_analysis = cur.fetchone()[0]

        # Get most analyzed ticker (count distinct analyses per ticker)
        cur.execute("""
            SELECT ticker, COUNT(DISTINCT analysis_timestamp) as count
            FROM peer_results
            GROUP BY ticker
            ORDER BY count DESC
            LIMIT 1
        """)
        most_analyzed = cur.fetchone()
        most_analyzed_ticker = most_analyzed[0] if most_analyzed else None
        most_analyzed_count = most_analyzed[1] if most_analyzed else 0

        # Get total peer relationships stored
        cur.execute("SELECT COUNT(*) FROM peer_results")
        total_peer_relationships = cur.fetchone()[0]

        conn.close()

        return {
            "total_analyses": total_analyses,
            "unique_tickers": unique_tickers,
            "total_cost_cents": total_cost_cents,
            "total_cost_dollars": total_cost_cents / 100,
            "latest_analysis": latest_analysis,
            "most_analyzed_ticker": most_analyzed_ticker,
            "most_analyzed_count": most_analyzed_count,
            "total_peer_relationships": total_peer_relationships
        }

    except Exception as e:
        print(f"Error getting peer analysis stats: {e}")
        return {}

if __name__ == '__main__':
    import sys

    # Check for migration flag
    if len(sys.argv) > 1 and sys.argv[1] == '--migrate':
        print("Running migration from old JSON schema...")
        success = migrate_from_json_schema()
        if success:
            print("Migration completed successfully!")
        else:
            print("Migration failed!")
        sys.exit(0 if success else 1)

    # Initialize database
    init_peers_results_db()
    print(f"Peers results database initialized at {PEERS_RESULTS_DB}")

    # Check for old data that needs migration
    conn = sqlite3.connect(PEERS_RESULTS_DB)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='peer_analysis'")
    old_table_exists = cur.fetchone()
    conn.close()

    if old_table_exists:
        print("\n⚠️  Old peer_analysis table detected!")
        print("Run this script with --migrate to convert old data to new schema:")
        print("python peers_results_db.py --migrate")

    # Show current stats
    stats = get_peer_analysis_stats()
    if stats:
        print(f"\nDatabase Statistics:")
        print(f"  Total analyses: {stats['total_analyses']}")
        print(f"  Unique tickers: {stats['unique_tickers']}")
        print(f"  Total peer relationships: {stats['total_peer_relationships']}")
        print(f"  Total cost: ${stats['total_cost_dollars']:.4f}")
        if stats['most_analyzed_ticker']:
            print(f"  Most analyzed: {stats['most_analyzed_ticker']} ({stats['most_analyzed_count']} times)")