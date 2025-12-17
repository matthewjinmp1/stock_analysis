#!/usr/bin/env python3
"""
Peer data management for web app.
Uses peers database for peer relationships.
"""

# Import from peers database
from web_app.peers_db import (
    get_peers_for_company,
    get_peers_for_ticker,
    init_peers_database,
    import_peers_from_json,
    add_peer_company,
    add_peer,
    remove_peer_company,
    remove_peer,
    has_peers_company,
    has_peers,
    get_all_companies_with_peers,
    get_all_tickers_with_peers
)

# Re-export for backward compatibility
__all__ = [
    'get_peers_for_company',
    'get_peers_for_ticker',
    'init_peers_database',
    'import_peers_from_json',
    'add_peer_company',
    'add_peer',
    'remove_peer_company',
    'remove_peer',
    'has_peers_company',
    'has_peers',
    'get_all_companies_with_peers',
    'get_all_tickers_with_peers'
]
