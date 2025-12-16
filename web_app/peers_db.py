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
            ticker TEXT NOT NULL,
            peer_ticker TEXT NOT NULL,
            rank INTEGER NOT NULL,
            PRIMARY KEY (ticker, peer_ticker)
        )
    ''')
    
    # Create index for faster lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_ticker ON peers(ticker)
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
    
    init_peers_database()
    
    conn = sqlite3.connect(PEERS_DB)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM peers')
    
    # Import all peer relationships
    count = 0
    for ticker, peer_list in peers_data.items():
        ticker_upper = ticker.strip().upper()
        if not isinstance(peer_list, list):
            continue
        
        for rank, peer_ticker in enumerate(peer_list[:10], start=1):  # Limit to top 10
            peer_ticker_upper = peer_ticker.strip().upper()
            if peer_ticker_upper:
                try:
                    cursor.execute('''
                        INSERT INTO peers (ticker, peer_ticker, rank)
                        VALUES (?, ?, ?)
                    ''', (ticker_upper, peer_ticker_upper, rank))
                    count += 1
                except sqlite3.IntegrityError:
                    # Skip duplicates
                    pass
    
    conn.commit()
    conn.close()
    
    return count


def get_peers_for_ticker(ticker: str) -> List[str]:
    """Get peer tickers for a given ticker.
    
    Args:
        ticker: Stock ticker symbol (uppercase)
        
    Returns:
        list: List of peer ticker symbols (up to 10), ordered by rank
    """
    ticker_upper = ticker.strip().upper()
    init_peers_database()
    
    conn = sqlite3.connect(PEERS_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT peer_ticker 
        FROM peers 
        WHERE ticker = ? 
        ORDER BY rank ASC
        LIMIT 10
    ''', (ticker_upper,))
    
    peers = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return peers


def add_peer(ticker: str, peer_ticker: str, rank: Optional[int] = None) -> bool:
    """Add a peer relationship.
    
    Args:
        ticker: Main ticker symbol
        peer_ticker: Peer ticker symbol
        rank: Optional rank (if None, will be set to next available rank)
        
    Returns:
        True if added, False if already exists
    """
    ticker_upper = ticker.strip().upper()
    peer_ticker_upper = peer_ticker.strip().upper()
    init_peers_database()
    
    conn = sqlite3.connect(PEERS_DB)
    cursor = conn.cursor()
    
    # If rank not provided, get the next rank
    if rank is None:
        cursor.execute('''
            SELECT COALESCE(MAX(rank), 0) + 1 
            FROM peers 
            WHERE ticker = ?
        ''', (ticker_upper,))
        rank = cursor.fetchone()[0]
    
    try:
        cursor.execute('''
            INSERT INTO peers (ticker, peer_ticker, rank)
            VALUES (?, ?, ?)
        ''', (ticker_upper, peer_ticker_upper, rank))
        conn.commit()
        added = True
    except sqlite3.IntegrityError:
        # Relationship already exists
        added = False
    finally:
        conn.close()
    
    return added


def remove_peer(ticker: str, peer_ticker: str) -> bool:
    """Remove a peer relationship.
    
    Args:
        ticker: Main ticker symbol
        peer_ticker: Peer ticker symbol to remove
        
    Returns:
        True if removed, False if not found
    """
    ticker_upper = ticker.strip().upper()
    peer_ticker_upper = peer_ticker.strip().upper()
    init_peers_database()
    
    conn = sqlite3.connect(PEERS_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM peers 
        WHERE ticker = ? AND peer_ticker = ?
    ''', (ticker_upper, peer_ticker_upper))
    
    removed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return removed


def has_peers(ticker: str) -> bool:
    """Check if a ticker has any peers in the database.
    
    Args:
        ticker: Ticker symbol to check
        
    Returns:
        True if ticker has peers, False otherwise
    """
    ticker_upper = ticker.strip().upper()
    init_peers_database()
    
    conn = sqlite3.connect(PEERS_DB)
    cursor = conn.cursor()
    
    cursor.execute('SELECT 1 FROM peers WHERE ticker = ? LIMIT 1', (ticker_upper,))
    result = cursor.fetchone()
    conn.close()
    
    return result is not None


def get_all_tickers_with_peers() -> List[str]:
    """Get all tickers that have peers.
    
    Returns:
        List of ticker symbols
    """
    init_peers_database()
    
    conn = sqlite3.connect(PEERS_DB)
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT ticker FROM peers ORDER BY ticker')
    tickers = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return tickers
