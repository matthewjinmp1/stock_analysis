#!/usr/bin/env python3
"""
Peer data management for web app.
Loads peer data from AI_stock_scorer peers.json file.
"""

import json
import os
import sys

# Ensure project root is on path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Path to peers file
PEERS_FILE = os.path.join(PROJECT_ROOT, "AI_stock_scorer", "data", "peers.json")

def load_peers():
    """Load peers data from JSON file.
    
    Returns:
        dict: Dictionary mapping ticker to list of peer tickers
    """
    if os.path.exists(PEERS_FILE):
        try:
            with open(PEERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not load peers file: {e}")
            return {}
    return {}

def get_peers_for_ticker(ticker: str) -> list:
    """Get peer tickers for a given ticker.
    
    Args:
        ticker: Stock ticker symbol (uppercase)
        
    Returns:
        list: List of peer ticker symbols (up to 10), or empty list if not found
    """
    ticker_upper = ticker.strip().upper()
    peers_data = load_peers()
    
    if ticker_upper in peers_data:
        peer_tickers = peers_data[ticker_upper]
        # Limit to top 10
        return peer_tickers[:10] if isinstance(peer_tickers, list) else []
    
    return []
