#!/usr/bin/env python3
"""
Peers database for storing peer relationships between tickers.
"""

import sqlite3
import os
import json
import sys
from typing import List, Optional

# Ensure project root is on path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Path to peers database
PEERS_DB = os.path.join(os.path.dirname(__file__), 'data', 'peers.db')

# Path to source peers file (for initial import)
PEERS_FILE = os.path.join(PROJECT_ROOT, "AI_stock_scorer", "data", "peers.json")


def init_peers_database():
    """Initialize the peers database."""
    os.makedirs(os.path.dirname(PEERS_DB), exist_ok=True)

    conn = sqlite3.connect(PEERS_DB)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS peers (
            company_name TEXT NOT NULL,
            peer_company_name TEXT NOT NULL,
            rank INTEGER NOT NULL,
            PRIMARY KEY (company_name, peer_company_name)
        )
    ''')

    # Create index for faster lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_company_name ON peers(company_name)
    ''')

    conn.commit()
    conn.close()


def import_peers_from_json():
    """Import peers data from the JSON file into the database.

    Returns:
        int: Number of peer relationships imported
    """
    if not os.path.exists(PEERS_FILE):
        print(f"Warning: Peers file not found at {PEERS_FILE}")
        return 0

    try:
        with open(PEERS_FILE, 'r', encoding='utf-8') as f:
            peers_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: Could not load peers file: {e}")
        return 0

    # Get ticker to company mapping from tickers.db (only real tickers)
    tickers_db = os.path.join(os.path.dirname(__file__), 'data', 'tickers.db')
    ticker_to_company = {}
    if os.path.exists(tickers_db):
        conn_tickers = sqlite3.connect(tickers_db)
        cur_tickers = conn_tickers.cursor()
        cur_tickers.execute("SELECT ticker, company_name FROM tickers")
        ticker_to_company = {row[0]: row[1] for row in cur_tickers.fetchall()}
        conn_tickers.close()

    init_peers_database()

    conn = sqlite3.connect(PEERS_DB)
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute('DELETE FROM peers')

    # Import all peer relationships
    count = 0
    for ticker, peer_list in peers_data.items():
        ticker_upper = ticker.strip().upper()
        company_name = ticker_to_company.get(ticker_upper)
        if not company_name or not isinstance(peer_list, list):
            continue

        for rank, peer_ticker in enumerate(peer_list[:10], start=1):  # Limit to top 10
            peer_ticker_upper = peer_ticker.strip().upper()
            peer_company_name = ticker_to_company.get(peer_ticker_upper)
            if peer_company_name:
                try:
                    cursor.execute('''
                        INSERT INTO peers (company_name, peer_company_name, rank)
                        VALUES (?, ?, ?)
                    ''', (company_name, peer_company_name, rank))
                    count += 1
                except sqlite3.IntegrityError:
                    # Skip duplicates
                    pass

    conn.commit()
    conn.close()

    return count


def get_peers_for_company(company_name: str) -> List[str]:
    """Get peer company names for a given company.

    Args:
        company_name: Company name

    Returns:
        list: List of peer company names (up to 10), ordered by rank
    """
    init_peers_database()

    conn = sqlite3.connect(PEERS_DB)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT peer_company_name
        FROM peers
        WHERE company_name = ?
        ORDER BY rank ASC
        LIMIT 10
    ''', (company_name,))

    peers = [row[0] for row in cursor.fetchall()]
    conn.close()

    return peers

def get_peers_for_ticker(ticker: str) -> List[str]:
    """Get peer company names for a given ticker (legacy compatibility).

    Args:
        ticker: Stock ticker symbol (uppercase)

    Returns:
        list: List of peer company names (up to 10), ordered by rank
    """
    # Get company name from ticker using tickers.db
    tickers_db = os.path.join(os.path.dirname(__file__), 'data', 'tickers.db')
    if os.path.exists(tickers_db):
        conn_tickers = sqlite3.connect(tickers_db)
        cur_tickers = conn_tickers.cursor()
        cur_tickers.execute("SELECT company_name FROM tickers WHERE ticker = ?", (ticker.upper(),))
        result = cur_tickers.fetchone()
        conn_tickers.close()
        if result:
            return get_peers_for_company(result[0])

    return []


def add_peer_company(company_name: str, peer_company_name: str, rank: Optional[int] = None) -> bool:
    """Add a peer relationship using company names.

    Args:
        company_name: Main company name
        peer_company_name: Peer company name
        rank: Optional rank (if None, will be set to next available rank)

    Returns:
        True if added, False if already exists
    """
    init_peers_database()

    conn = sqlite3.connect(PEERS_DB)
    cursor = conn.cursor()

    # If rank not provided, get the next rank
    if rank is None:
        cursor.execute('''
            SELECT COALESCE(MAX(rank), 0) + 1
            FROM peers
            WHERE company_name = ?
        ''', (company_name,))
        rank = cursor.fetchone()[0]

    try:
        cursor.execute('''
            INSERT INTO peers (company_name, peer_company_name, rank)
            VALUES (?, ?, ?)
        ''', (company_name, peer_company_name, rank))
        conn.commit()
        added = True
    except sqlite3.IntegrityError:
        # Relationship already exists
        added = False
    finally:
        conn.close()

    return added

def add_peer(ticker: str, peer_ticker: str, rank: Optional[int] = None) -> bool:
    """Add a peer relationship (legacy compatibility).

    Args:
        ticker: Main ticker symbol
        peer_ticker: Peer ticker symbol
        rank: Optional rank (if None, will be set to next available rank)

    Returns:
        True if added, False if already exists
    """
    # Convert tickers to company names using tickers.db
    tickers_db = os.path.join(os.path.dirname(__file__), 'data', 'tickers.db')
    if os.path.exists(tickers_db):
        conn_tickers = sqlite3.connect(tickers_db)
        cur_tickers = conn_tickers.cursor()

        cur_tickers.execute("SELECT company_name FROM tickers WHERE ticker = ?", (ticker.upper(),))
        main_result = cur_tickers.fetchone()
        cur_tickers.execute("SELECT company_name FROM tickers WHERE ticker = ?", (peer_ticker.upper(),))
        peer_result = cur_tickers.fetchone()

        conn_tickers.close()

        if main_result and peer_result:
            return add_peer_company(main_result[0], peer_result[0], rank)

    return False


def remove_peer_company(company_name: str, peer_company_name: str) -> bool:
    """Remove a peer relationship using company names.

    Args:
        company_name: Main company name
        peer_company_name: Peer company name to remove

    Returns:
        True if removed, False if not found
    """
    init_peers_database()

    conn = sqlite3.connect(PEERS_DB)
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM peers
        WHERE company_name = ? AND peer_company_name = ?
    ''', (company_name, peer_company_name))

    removed = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return removed

def remove_peer(ticker: str, peer_ticker: str) -> bool:
    """Remove a peer relationship (legacy compatibility).

    Args:
        ticker: Main ticker symbol
        peer_ticker: Peer ticker symbol to remove

    Returns:
        True if removed, False if not found
    """
    # Convert tickers to company names
    tickers_db = os.path.join(os.path.dirname(__file__), 'data', 'tickers.db')
    if os.path.exists(tickers_db):
        conn_tickers = sqlite3.connect(tickers_db)
        cur_tickers = conn_tickers.cursor()

        cur_tickers.execute("SELECT company_name FROM tickers WHERE ticker = ?", (ticker.upper(),))
        main_result = cur_tickers.fetchone()
        cur_tickers.execute("SELECT company_name FROM tickers WHERE ticker = ?", (peer_ticker.upper(),))
        peer_result = cur_tickers.fetchone()

        conn_tickers.close()

        if main_result and peer_result:
            return remove_peer_company(main_result[0], peer_result[0])

    return False


def has_peers_company(company_name: str) -> bool:
    """Check if a company has any peers in the database.

    Args:
        company_name: Company name to check

    Returns:
        True if company has peers, False otherwise
    """
    init_peers_database()

    conn = sqlite3.connect(PEERS_DB)
    cursor = conn.cursor()

    cursor.execute('SELECT 1 FROM peers WHERE company_name = ? LIMIT 1', (company_name,))
    result = cursor.fetchone()
    conn.close()

    return result is not None

def has_peers(ticker: str) -> bool:
    """Check if a ticker has any peers in the database (legacy compatibility).

    Args:
        ticker: Ticker symbol to check

    Returns:
        True if ticker has peers, False otherwise
    """
    # Convert ticker to company name using tickers.db
    tickers_db = os.path.join(os.path.dirname(__file__), 'data', 'tickers.db')
    if os.path.exists(tickers_db):
        conn_tickers = sqlite3.connect(tickers_db)
        cur_tickers = conn_tickers.cursor()
        cur_tickers.execute("SELECT company_name FROM tickers WHERE ticker = ?", (ticker.upper(),))
        result = cur_tickers.fetchone()
        conn_tickers.close()
        if result:
            return has_peers_company(result[0])

    return False


def get_all_companies_with_peers() -> List[str]:
    """Get all companies that have peers.

    Returns:
        List of company names
    """
    init_peers_database()

    conn = sqlite3.connect(PEERS_DB)
    cursor = conn.cursor()

    cursor.execute('SELECT DISTINCT company_name FROM peers ORDER BY company_name')
    companies = [row[0] for row in cursor.fetchall()]
    conn.close()

    return companies

def get_all_tickers_with_peers() -> List[str]:
    """Get all tickers that have peers (legacy compatibility).

    Returns:
        List of ticker symbols
    """
    companies = get_all_companies_with_peers()

    # Convert company names back to tickers using tickers.db
    tickers_db = os.path.join(os.path.dirname(__file__), 'data', 'tickers.db')
    if os.path.exists(tickers_db):
        conn_tickers = sqlite3.connect(tickers_db)
        cur_tickers = conn_tickers.cursor()

        tickers = []
        for company in companies:
            cur_tickers.execute("SELECT ticker FROM tickers WHERE company_name = ?", (company,))
            result = cur_tickers.fetchone()
            if result:
                tickers.append(result[0])

        conn_tickers.close()
        return tickers

    return []
