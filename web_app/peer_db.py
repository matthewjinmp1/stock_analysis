#!/usr/bin/env python3
"""
Peer data management for web app.
Uses peers database for peer relationships.
"""

# Import from peers database
from web_app.peers_db import (
    get_peers_for_ticker,
    init_peers_database,
    import_peers_from_json,
    has_peers,
    get_all_tickers_with_peers
)

# Re-export for backward compatibility
__all__ = [
    'get_peers_for_ticker',
    'init_peers_database',
    'import_peers_from_json',
    'has_peers',
    'get_all_tickers_with_peers'
]
