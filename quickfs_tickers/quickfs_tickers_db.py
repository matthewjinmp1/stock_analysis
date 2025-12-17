#!/usr/bin/env python3
"""
QuickFS Tickers Database Manager
Provides functions to query and manage the QuickFS tickers database
"""

import sqlite3
import os
import sys
from typing import List, Dict, Optional, Tuple

# Ensure project root is on path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Database path
DB_PATH = os.path.join(PROJECT_ROOT, 'quickfs_tickers', 'quickfs_tickers.db')

def get_db_connection():
    """Get database connection."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    return sqlite3.connect(DB_PATH)

def get_total_ticker_count() -> int:
    """Get total number of tickers in database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT COUNT(*) FROM tickers')
        result = cursor.fetchone()
        return result[0] if result else 0
    finally:
        conn.close()

def get_all_tickers(limit: Optional[int] = None) -> List[str]:
    """Get all tickers from database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if limit:
            cursor.execute('SELECT ticker FROM tickers ORDER BY ticker LIMIT ?', (limit,))
        else:
            cursor.execute('SELECT ticker FROM tickers ORDER BY ticker')

        results = cursor.fetchall()
        return [row[0] for row in results]
    finally:
        conn.close()

def ticker_exists(ticker: str) -> bool:
    """Check if ticker exists in database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT 1 FROM tickers WHERE ticker = ? LIMIT 1', (ticker.upper(),))
        result = cursor.fetchone()
        return result is not None
    finally:
        conn.close()

def search_tickers(query: str, limit: int = 50) -> List[str]:
    """Search tickers by partial match."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Use LIKE for partial matching
        cursor.execute(
            'SELECT ticker FROM tickers WHERE ticker LIKE ? ORDER BY ticker LIMIT ?',
            (f'%{query.upper()}%', limit)
        )

        results = cursor.fetchall()
        return [row[0] for row in results]
    finally:
        conn.close()

def get_tickers_by_exchange(exchange_codes: List[str]) -> Dict[str, List[str]]:
    """
    Get tickers grouped by exchange.
    Note: This is an approximation based on ticker patterns, not actual exchange data.
    """
    # This is a simplified approach - in reality you'd need exchange mapping
    # For now, return all tickers (since we don't have exchange info in the DB)
    all_tickers = get_all_tickers()
    return {"all_quickfs": all_tickers}

def get_database_stats() -> Dict:
    """Get database statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Total count
        cursor.execute('SELECT COUNT(*) FROM tickers')
        total_count = cursor.fetchone()[0]

        # Source breakdown
        cursor.execute('SELECT source, COUNT(*) FROM tickers GROUP BY source')
        source_counts = dict(cursor.fetchall())

        # Check for company names (should be NULL for QuickFS)
        cursor.execute('SELECT COUNT(*) FROM tickers WHERE company_name IS NOT NULL')
        named_count = cursor.fetchone()[0]

        return {
            "total_tickers": total_count,
            "source_breakdown": source_counts,
            "tickers_with_names": named_count,
            "database_path": DB_PATH,
            "database_size_mb": round(os.path.getsize(DB_PATH) / (1024 * 1024), 2) if os.path.exists(DB_PATH) else 0
        }
    finally:
        conn.close()

def export_to_json(output_file: str):
    """Export all tickers to JSON file."""
    tickers = get_all_tickers()
    data = {
        "total_tickers": len(tickers),
        "tickers": tickers,
        "source": "quickfs_database_export"
    }

    with open(output_file, 'w') as f:
        import json
        json.dump(data, f, indent=2)

    print(f"Exported {len(tickers)} tickers to {output_file}")

def show_sample_tickers(count: int = 20):
    """Display sample tickers from database."""
    tickers = get_all_tickers(limit=count)

    print(f"Sample of {len(tickers)} tickers from QuickFS database:")
    print("-" * 50)
    for i, ticker in enumerate(tickers, 1):
        print(f"{i:3}. {ticker}")
    print("-" * 50)

def main():
    """Command line interface for database operations."""
    import argparse

    parser = argparse.ArgumentParser(description="QuickFS Tickers Database Manager")
    parser.add_argument('action', choices=['stats', 'sample', 'search', 'export'],
                       help='Action to perform')
    parser.add_argument('--query', '-q', help='Search query for search action')
    parser.add_argument('--limit', '-l', type=int, default=20,
                       help='Limit for sample/search results (default: 20)')
    parser.add_argument('--output', '-o', help='Output file for export action')

    args = parser.parse_args()

    if args.action == 'stats':
        stats = get_database_stats()
        print("QuickFS Tickers Database Statistics")
        print("=" * 40)
        print(f"Total tickers: {stats['total_tickers']}")
        print(f"Database size: {stats['database_size_mb']} MB")
        print(f"Tickers with names: {stats['tickers_with_names']}")
        print(f"Source breakdown: {stats['source_breakdown']}")
        print(f"Database path: {stats['database_path']}")

    elif args.action == 'sample':
        show_sample_tickers(args.limit)

    elif args.action == 'search':
        if not args.query:
            print("Error: --query required for search action")
            return
        results = search_tickers(args.query, args.limit)
        print(f"Search results for '{args.query}' ({len(results)} found):")
        for ticker in results:
            print(f"  {ticker}")

    elif args.action == 'export':
        if not args.output:
            print("Error: --output required for export action")
            return
        export_to_json(args.output)

if __name__ == '__main__':
    main()