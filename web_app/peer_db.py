#!/usr/bin/env python3
"""
Peer data management for web app.
Uses peers_results database for AI-generated peer relationships.
"""

# Import from peers_results database
from web_app.peers.peers_results_db import (
    get_peer_analysis,
    init_peers_results_db
)

def get_peers_for_ticker(ticker: str) -> list:
    """
    Get peer data for a ticker from peers_results.db.
    Returns list of peer dictionaries with 'name' and 'ticker' keys.
    """
    # Get latest peer analysis for this ticker
    analyses = get_peer_analysis(ticker, limit=1)
    if not analyses:
        return []

    latest_analysis = analyses[0]
    peers_data = latest_analysis.get('peers', [])

    # Return list of peer dictionaries (backward compatible with new structure)
    return peers_data

def get_peers_for_company(company_name: str) -> list:
    """
    Get peer data for a company name from peers_results.db.
    This is a legacy function - peers_results.db is ticker-based.
    """
    # This function is less relevant now since peers_results.db is ticker-based
    # Return empty list for backward compatibility
    return []

def init_peers_database():
    """Initialize the peers results database."""
    init_peers_results_db()

# Legacy functions for backward compatibility
def import_peers_from_json():
    """Not applicable for peers_results.db"""
    pass

def add_peer_company(company_name, peer_company_name, rank=1):
    """Not applicable for peers_results.db - data comes from AI"""
    pass

def add_peer(ticker, peer_ticker, rank=1):
    """Not applicable for peers_results.db - data comes from AI"""
    pass

def remove_peer_company(company_name, peer_company_name):
    """Not applicable for peers_results.db - data comes from AI"""
    pass

def remove_peer(ticker, peer_ticker):
    """Not applicable for peers_results.db - data comes from AI"""
    pass

def has_peers_company(company_name):
    """Check if company has peers in peers_results.db"""
    # This would require searching through all analyses - simplified for now
    return False

def has_peers(ticker):
    """Check if ticker has peer analysis in peers_results.db"""
    analyses = get_peer_analysis(ticker, limit=1)
    return len(analyses) > 0

def get_all_companies_with_peers():
    """Not directly applicable for peers_results.db"""
    return []

def get_all_tickers_with_peers():
    """Get all tickers that have peer analysis"""
    # This would require a more complex query - simplified for now
    return []

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
