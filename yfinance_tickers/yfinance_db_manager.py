#!/usr/bin/env python3
"""
YFinance Database Manager
Query and manage the yfinance tickers database
"""

import sqlite3
import os
import sys
from typing import List, Dict, Optional

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Database path
DB_PATH = os.path.join(PROJECT_ROOT, 'yfinance_tickers', 'yfinance_tickers.db')

def get_db_connection():
    """Get database connection"""
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        print("Run yfinance_ticker_collector.py first to create the database.")
        sys.exit(1)
    return sqlite3.connect(DB_PATH)

def get_total_ticker_count() -> int:
    """Get total number of tickers in database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT COUNT(*) FROM tickers')
        result = cursor.fetchone()
        return result[0] if result else 0
    finally:
        conn.close()

def get_all_tickers(limit: Optional[int] = None) -> List[Dict]:
    """Get all tickers with full information"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if limit:
            cursor.execute('SELECT * FROM tickers ORDER BY ticker LIMIT ?', (limit,))
        else:
            cursor.execute('SELECT * FROM tickers ORDER BY ticker')

        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()

        return [dict(zip(columns, row)) for row in results]
    finally:
        conn.close()

def search_tickers(query: str, limit: int = 50) -> List[Dict]:
    """Search tickers by company name or ticker symbol"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Search in both ticker and company_name
        cursor.execute('''
            SELECT * FROM tickers
            WHERE ticker LIKE ? OR company_name LIKE ?
            ORDER BY ticker
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', limit))

        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()

        return [dict(zip(columns, row)) for row in results]
    finally:
        conn.close()

def get_tickers_by_sector(sector: str) -> List[Dict]:
    """Get tickers by sector"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM tickers WHERE sector = ? ORDER BY ticker', (sector,))
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()

        return [dict(zip(columns, row)) for row in results]
    finally:
        conn.close()

def get_tickers_by_source(source: str) -> List[Dict]:
    """Get tickers by source"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM tickers WHERE source = ? ORDER BY ticker', (source,))
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()

        return [dict(zip(columns, row)) for row in results]
    finally:
        conn.close()

def get_sector_breakdown() -> Dict[str, int]:
    """Get breakdown of tickers by sector"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT sector, COUNT(*) FROM tickers WHERE sector IS NOT NULL GROUP BY sector ORDER BY COUNT(*) DESC')
        results = dict(cursor.fetchall())
        return results
    finally:
        conn.close()

def get_source_breakdown() -> Dict[str, int]:
    """Get breakdown of tickers by source"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT source, COUNT(*) FROM tickers GROUP BY source ORDER BY COUNT(*) DESC')
        results = dict(cursor.fetchall())
        return results
    finally:
        conn.close()

def get_database_stats() -> Dict:
    """Get comprehensive database statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        stats = {}

        # Basic counts
        cursor.execute('SELECT COUNT(*) FROM tickers')
        stats['total_tickers'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM ticker_sources')
        stats['total_sources'] = cursor.fetchone()[0]

        # Sector breakdown
        stats['sector_breakdown'] = get_sector_breakdown()

        # Source breakdown
        stats['source_breakdown'] = get_source_breakdown()

        # Tickers with company names
        cursor.execute('SELECT COUNT(*) FROM tickers WHERE company_name IS NOT NULL AND company_name != ""')
        stats['with_company_names'] = cursor.fetchone()[0]

        # Database file info
        if os.path.exists(DB_PATH):
            stats['database_size_mb'] = round(os.path.getsize(DB_PATH) / (1024 * 1024), 2)

        stats['database_path'] = DB_PATH

        return stats
    finally:
        conn.close()

def export_to_json(output_file: str, include_details: bool = True):
    """Export tickers to JSON file"""
    tickers = get_all_tickers()

    if include_details:
        data = {
            "export_timestamp": str(datetime.now()),
            "total_tickers": len(tickers),
            "tickers": tickers,
            "stats": get_database_stats()
        }
    else:
        data = {
            "export_timestamp": str(datetime.now()),
            "total_tickers": len(tickers),
            "tickers": [t['ticker'] for t in tickers]
        }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(tickers)} tickers to {output_file}")

def show_sample_tickers(count: int = 20, detailed: bool = False):
    """Display sample tickers"""
    tickers = get_all_tickers(limit=count)

    print(f"Sample of {len(tickers)} tickers from YFinance database:")
    print("-" * 80)

    for ticker in tickers:
        if detailed:
            print(f"{ticker['ticker']:<6} | {ticker['company_name'][:40]:<40} | {ticker['sector'] or 'N/A':<20} | {ticker['source']}")
        else:
            print(f"{ticker['ticker']:<6} | {ticker['company_name'] or 'N/A'}")

    print("-" * 80)

def main():
    """Command line interface"""
    import argparse

    parser = argparse.ArgumentParser(description="YFinance Database Manager")
    parser.add_argument('action', choices=['stats', 'sample', 'search', 'sectors', 'sources', 'export'],
                       help='Action to perform')
    parser.add_argument('--query', '-q', help='Search query for search action')
    parser.add_argument('--limit', '-l', type=int, default=20,
                       help='Limit for sample/search results (default: 20)')
    parser.add_argument('--detailed', '-d', action='store_true',
                       help='Show detailed information in sample')
    parser.add_argument('--output', '-o', help='Output file for export action')
    parser.add_argument('--sector', help='Filter by sector')
    parser.add_argument('--source', help='Filter by source')

    args = parser.parse_args()

    if args.action == 'stats':
        stats = get_database_stats()
        print("YFinance Database Statistics")
        print("=" * 50)
        print(f"Total tickers: {stats['total_tickers']}")
        print(f"Total sources: {stats['total_sources']}")
        print(f"With company names: {stats['with_company_names']}")
        print(".1f")
        print(f"Database path: {stats['database_path']}")
        print()

        if stats['sector_breakdown']:
            print("Top sectors:")
            for sector, count in list(stats['sector_breakdown'].items())[:10]:
                print(f"  {sector}: {count}")
        print()

        if stats['source_breakdown']:
            print("Sources:")
            for source, count in stats['source_breakdown'].items():
                print(f"  {source}: {count}")

    elif args.action == 'sample':
        show_sample_tickers(args.limit, args.detailed)

    elif args.action == 'search':
        if not args.query:
            print("Error: --query required for search action")
            return
        results = search_tickers(args.query, args.limit)
        print(f"Search results for '{args.query}' ({len(results)} found):")
        print("-" * 80)
        for ticker in results:
            if args.detailed:
                print(f"{ticker['ticker']:<6} | {ticker['company_name'][:40]:<40} | {ticker['sector'] or 'N/A'}")
            else:
                print(f"{ticker['ticker']:<6} | {ticker['company_name'] or 'N/A'}")

    elif args.action == 'sectors':
        if args.sector:
            tickers = get_tickers_by_sector(args.sector)
            print(f"Tickers in sector '{args.sector}' ({len(tickers)} found):")
            for ticker in tickers[:args.limit]:
                print(f"  {ticker['ticker']} - {ticker['company_name']}")
        else:
            sectors = get_sector_breakdown()
            print("All sectors:")
            for sector, count in sectors.items():
                print(f"  {sector}: {count}")

    elif args.action == 'sources':
        if args.source:
            tickers = get_tickers_by_source(args.source)
            print(f"Tickers from source '{args.source}' ({len(tickers)} found):")
            for ticker in tickers[:args.limit]:
                print(f"  {ticker['ticker']} - {ticker['company_name']}")
        else:
            sources = get_source_breakdown()
            print("All sources:")
            for source, count in sources.items():
                print(f"  {source}: {count}")

    elif args.action == 'export':
        if not args.output:
            print("Error: --output required for export action")
            return
        export_to_json(args.output, include_details=args.detailed)

if __name__ == '__main__':
    main()