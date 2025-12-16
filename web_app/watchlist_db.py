#!/usr/bin/env python3
"""
Watchlist database for storing user's ticker watchlist.
"""

import sqlite3
import os
from typing import List, Dict, Any
from datetime import datetime

# Path to watchlist database
WATCHLIST_DB = os.path.join(os.path.dirname(__file__), 'data', 'watchlist.db')


def init_watchlist_database():
    """Initialize the watchlist database."""
    os.makedirs(os.path.dirname(WATCHLIST_DB), exist_ok=True)
    
    conn = sqlite3.connect(WATCHLIST_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            ticker TEXT PRIMARY KEY,
            added_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()


def add_to_watchlist(ticker: str) -> bool:
    """Add a ticker to the watchlist.
    
    Args:
        ticker: Ticker symbol to add
        
    Returns:
        True if added, False if already exists
    """
    ticker = ticker.strip().upper()
    init_watchlist_database()
    
    conn = sqlite3.connect(WATCHLIST_DB)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO watchlist (ticker, added_at)
            VALUES (?, ?)
        ''', (ticker, datetime.now().isoformat()))
        conn.commit()
        added = True
    except sqlite3.IntegrityError:
        # Ticker already exists
        added = False
    finally:
        conn.close()
    
    return added


def remove_from_watchlist(ticker: str) -> bool:
    """Remove a ticker from the watchlist.
    
    Args:
        ticker: Ticker symbol to remove
        
    Returns:
        True if removed, False if not found
    """
    ticker = ticker.strip().upper()
    init_watchlist_database()
    
    conn = sqlite3.connect(WATCHLIST_DB)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM watchlist WHERE ticker = ?', (ticker,))
    removed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return removed


def is_in_watchlist(ticker: str) -> bool:
    """Check if a ticker is in the watchlist.
    
    Args:
        ticker: Ticker symbol to check
        
    Returns:
        True if in watchlist, False otherwise
    """
    ticker = ticker.strip().upper()
    init_watchlist_database()
    
    conn = sqlite3.connect(WATCHLIST_DB)
    cursor = conn.cursor()
    
    cursor.execute('SELECT 1 FROM watchlist WHERE ticker = ?', (ticker,))
    result = cursor.fetchone()
    conn.close()
    
    return result is not None


def get_watchlist() -> List[str]:
    """Get all tickers in the watchlist.
    
    Returns:
        List of ticker symbols, ordered by added_at
    """
    init_watchlist_database()
    
    conn = sqlite3.connect(WATCHLIST_DB)
    cursor = conn.cursor()
    
    cursor.execute('SELECT ticker FROM watchlist ORDER BY added_at DESC')
    tickers = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return tickers
