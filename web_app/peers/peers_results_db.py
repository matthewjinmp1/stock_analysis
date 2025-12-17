#!/usr/bin/env python3
"""
Database for storing AI-generated peer analysis results.
Stores peer finding results with metadata, token usage, and costs.
"""

import os
import sqlite3
import json
from typing import List, Dict, Optional, Any
from datetime import datetime

# Database path
PEERS_RESULTS_DB = os.path.join(os.path.dirname(__file__), "peers_results.db")

def init_peers_results_db() -> None:
    """Initialize the peers results database."""
    os.makedirs(os.path.dirname(PEERS_RESULTS_DB), exist_ok=True)
    conn = sqlite3.connect(PEERS_RESULTS_DB)
    cur = conn.cursor()

    # Create peer analysis results table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS peer_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            company_name TEXT,
            peers_json TEXT NOT NULL,  -- JSON array of peer company names
            peer_count INTEGER NOT NULL,
            token_usage_json TEXT,     -- JSON object with token usage details
            estimated_cost_cents REAL,
            analysis_timestamp TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker, analysis_timestamp)
        )
        """
    )

    # Create indexes for better query performance
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_peer_analysis_ticker ON peer_analysis(ticker)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_peer_analysis_timestamp ON peer_analysis(analysis_timestamp)"
    )

    conn.commit()
    conn.close()

def save_peer_analysis(
    ticker: str,
    company_name: str,
    peers: List[str],
    token_usage: Optional[Dict[str, Any]] = None,
    estimated_cost_cents: Optional[float] = None,
    analysis_timestamp: Optional[str] = None
) -> bool:
    """
    Save peer analysis results to database.

    Args:
        ticker: Stock ticker symbol
        company_name: Full company name
        peers: List of peer company names
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

        # Convert data to JSON for storage
        peers_json = json.dumps(peers, ensure_ascii=False)
        token_usage_json = json.dumps(token_usage) if token_usage else None

        cur.execute(
            """
            INSERT OR REPLACE INTO peer_analysis
            (ticker, company_name, peers_json, peer_count, token_usage_json,
             estimated_cost_cents, analysis_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticker,
                company_name,
                peers_json,
                len(peers),
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
        limit: Maximum number of results to return

    Returns:
        List of peer analysis records
    """
    try:
        init_peers_results_db()
        conn = sqlite3.connect(PEERS_RESULTS_DB)
        cur = conn.cursor()

        cur.execute(
            """
            SELECT ticker, company_name, peers_json, peer_count, token_usage_json,
                   estimated_cost_cents, analysis_timestamp, created_at
            FROM peer_analysis
            WHERE ticker = ?
            ORDER BY analysis_timestamp DESC
            LIMIT ?
            """,
            (ticker, limit)
        )

        results = []
        for row in cur.fetchall():
            ticker, company_name, peers_json, peer_count, token_usage_json, \
            estimated_cost_cents, analysis_timestamp, created_at = row

            # Parse JSON data
            peers = json.loads(peers_json)
            token_usage = json.loads(token_usage_json) if token_usage_json else None

            results.append({
                "ticker": ticker,
                "company_name": company_name,
                "peers": peers,
                "peer_count": peer_count,
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
        limit: Maximum number of results to return

    Returns:
        List of all peer analysis records
    """
    try:
        init_peers_results_db()
        conn = sqlite3.connect(PEERS_RESULTS_DB)
        cur = conn.cursor()

        cur.execute(
            """
            SELECT ticker, company_name, peers_json, peer_count, token_usage_json,
                   estimated_cost_cents, analysis_timestamp, created_at
            FROM peer_analysis
            ORDER BY analysis_timestamp DESC
            LIMIT ?
            """,
            (limit,)
        )

        results = []
        for row in cur.fetchall():
            ticker, company_name, peers_json, peer_count, token_usage_json, \
            estimated_cost_cents, analysis_timestamp, created_at = row

            # Parse JSON data
            peers = json.loads(peers_json)
            token_usage = json.loads(token_usage_json) if token_usage_json else None

            results.append({
                "ticker": ticker,
                "company_name": company_name,
                "peers": peers,
                "peer_count": peer_count,
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

        # Get total analyses
        cur.execute("SELECT COUNT(*) FROM peer_analysis")
        total_analyses = cur.fetchone()[0]

        # Get unique tickers analyzed
        cur.execute("SELECT COUNT(DISTINCT ticker) FROM peer_analysis")
        unique_tickers = cur.fetchone()[0]

        # Get total cost
        cur.execute("SELECT SUM(estimated_cost_cents) FROM peer_analysis WHERE estimated_cost_cents IS NOT NULL")
        total_cost_cents = cur.fetchone()[0] or 0

        # Get most recent analysis
        cur.execute("SELECT MAX(analysis_timestamp) FROM peer_analysis")
        latest_analysis = cur.fetchone()[0]

        # Get most analyzed ticker
        cur.execute("""
            SELECT ticker, COUNT(*) as count
            FROM peer_analysis
            GROUP BY ticker
            ORDER BY count DESC
            LIMIT 1
        """)
        most_analyzed = cur.fetchone()
        most_analyzed_ticker = most_analyzed[0] if most_analyzed else None
        most_analyzed_count = most_analyzed[1] if most_analyzed else 0

        conn.close()

        return {
            "total_analyses": total_analyses,
            "unique_tickers": unique_tickers,
            "total_cost_cents": total_cost_cents,
            "total_cost_dollars": total_cost_cents / 100,
            "latest_analysis": latest_analysis,
            "most_analyzed_ticker": most_analyzed_ticker,
            "most_analyzed_count": most_analyzed_count
        }

    except Exception as e:
        print(f"Error getting peer analysis stats: {e}")
        return {}

if __name__ == '__main__':
    # Initialize database
    init_peers_results_db()
    print(f"Peers results database initialized at {PEERS_RESULTS_DB}")

    # Show current stats
    stats = get_peer_analysis_stats()
    if stats:
        print(f"\nDatabase Statistics:")
        print(f"  Total analyses: {stats['total_analyses']}")
        print(f"  Unique tickers: {stats['unique_tickers']}")
        print(f"  Total cost: ${stats['total_cost_dollars']:.4f}")
        if stats['most_analyzed_ticker']:
            print(f"  Most analyzed: {stats['most_analyzed_ticker']} ({stats['most_analyzed_count']} times)")