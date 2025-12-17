#!/usr/bin/env python3
"""
Get AI-generated peers for a ticker and convert company names to ticker symbols.
Uses multiple matching strategies against the tickers database.
"""

import sys
import os
import sqlite3
import json
import time
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
import re

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def get_ticker_database() -> Dict[str, str]:
    """
    Load ticker to company name mapping from tickers.db.

    Returns:
        Dict mapping ticker symbols to company names
    """
    tickers_db = os.path.join(PROJECT_ROOT, 'web_app', 'data', 'tickers.db')

    if not os.path.exists(tickers_db):
        print(f"Warning: Tickers database not found at {tickers_db}")
        return {}

    try:
        conn = sqlite3.connect(tickers_db)
        cur = conn.cursor()

        # Get all ticker-company mappings
        cur.execute("SELECT ticker, company_name FROM tickers")
        rows = cur.fetchall()

        ticker_map = {}
        for ticker, company_name in rows:
            if ticker and company_name:
                ticker_map[ticker.upper()] = company_name.strip()

        conn.close()
        print(f"Loaded {len(ticker_map)} ticker mappings from database")
        return ticker_map

    except Exception as e:
        print(f"Error loading ticker database: {e}")
        return {}

def normalize_company_name(name: str) -> str:
    """
    Normalize company name for better matching.

    Args:
        name: Raw company name

    Returns:
        Normalized company name
    """
    if not name:
        return ""

    # Convert to lowercase
    name = name.lower()

    # Remove common suffixes
    suffixes = [
        ' corporation', ' corp.', ' corp', ' inc.', ' inc', ' incorporated',
        ' limited', ' ltd.', ' ltd', ' llc', ' lp', ' plc', ' co.', ' co',
        ' company', ' group', ' holdings', ' technologies', ' technology',
        ' systems', ' solutions', ' international', ' global'
    ]

    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]

    # Remove punctuation and extra spaces
    name = re.sub(r'[^\w\s]', '', name)
    name = ' '.join(name.split())

    return name.strip()

def find_ticker_for_company(company_name: str, ticker_map: Dict[str, str]) -> Optional[str]:
    """
    Find ticker symbol for a company name using multiple matching strategies.

    Args:
        company_name: Company name to find ticker for
        ticker_map: Dict mapping tickers to company names

    Returns:
        Ticker symbol if found, None otherwise
    """
    if not company_name or not ticker_map:
        return None

    # Strategy 1: Exact match
    normalized_target = normalize_company_name(company_name)

    for ticker, db_name in ticker_map.items():
        if normalize_company_name(db_name) == normalized_target:
            return ticker

    # Strategy 2: Direct substring match (company name contains target or vice versa)
    for ticker, db_name in ticker_map.items():
        if (normalized_target in normalize_company_name(db_name) or
            normalize_company_name(db_name) in normalized_target):
            return ticker

    # Strategy 3: Fuzzy matching with high similarity
    best_match = None
    best_score = 0.0
    best_ticker = None

    for ticker, db_name in ticker_map.items():
        score = SequenceMatcher(None, normalized_target, normalize_company_name(db_name)).ratio()
        if score > best_score:
            best_score = score
            best_match = db_name
            best_ticker = ticker

    # Only return fuzzy match if similarity is high enough (>85%)
    if best_score > 0.85:
        return best_ticker

    # Strategy 4: Try partial matches with key words
    words = normalized_target.split()
    if len(words) >= 2:
        # Try first two words
        partial_name = ' '.join(words[:2])
        for ticker, db_name in ticker_map.items():
            if partial_name in normalize_company_name(db_name):
                return ticker

    return None

def get_peers_with_tickers(ticker: str, include_details: bool = False) -> Dict:
    """
    Get AI-generated peers for a ticker and convert to ticker symbols.

    Args:
        ticker: Stock ticker symbol
        include_details: Whether to include matching details

    Returns:
        Dict with peer analysis results
    """
    print(f"Getting peers for: {ticker}")
    print("=" * 50)

    # Load ticker database
    ticker_map = get_ticker_database()
    if not ticker_map:
        return {"error": "Could not load ticker database"}

    # Get company name for the input ticker
    input_company_name = None
    for t, name in ticker_map.items():
        if t == ticker.upper():
            input_company_name = name
            break

    if not input_company_name:
        return {"error": f"Ticker {ticker} not found in database"}

    print(f"Company: {input_company_name}")

    # Import peer finding functionality
    try:
        from web_app.peers.test_peer_finder import find_peers_for_ticker_ai
    except ImportError:
        return {"error": "Could not import peer finding functionality"}

    # Find peers using AI
    print("\nFinding peers using AI...")
    peers, error, token_usage, cost_cents = find_peers_for_ticker_ai(ticker, input_company_name)

    if error:
        return {"error": f"Error finding peers: {error}"}

    if not peers:
        return {"error": "No peers found"}

    print(f"\nFound {len(peers)} peer companies:")
    for i, peer in enumerate(peers, 1):
        print(f"  {i}. {peer}")

    # Convert company names to tickers
    print("\nConverting company names to ticker symbols...")
    peer_tickers = []
    unmatched_peers = []
    matching_details = []

    for peer_name in peers:
        ticker_found = find_ticker_for_company(peer_name, ticker_map)

        if ticker_found:
            peer_tickers.append(ticker_found)
            if include_details:
                matching_details.append({
                    "peer_name": peer_name,
                    "ticker": ticker_found,
                    "matched": True
                })
        else:
            peer_tickers.append(peer_name)  # Keep original name if no ticker found
            unmatched_peers.append(peer_name)
            if include_details:
                matching_details.append({
                    "peer_name": peer_name,
                    "ticker": None,
                    "matched": False
                })

    # Display results
    print("\nPeer tickers found:")
    for i, (original, ticker_result) in enumerate(zip(peers, peer_tickers), 1):
        status = "[OK]" if ticker_result != original else "[FAIL]"
        print(f"  {i}. {original} → {ticker_result} {status}")

    if unmatched_peers:
        print(f"\nWarning: {len(unmatched_peers)} peers could not be matched to tickers:")
        for peer in unmatched_peers:
            print(f"     - {peer}")

    # Prepare result
    result = {
        "input_ticker": ticker,
        "input_company": input_company_name,
        "peer_companies": peers,
        "peer_tickers": peer_tickers,
        "total_peers": len(peers),
        "matched_peers": len(peers) - len(unmatched_peers),
        "unmatched_peers": unmatched_peers,
        "token_usage": token_usage,
        "estimated_cost_cents": cost_cents
    }

    if include_details:
        result["matching_details"] = matching_details

    return result

def main():
    """Main interactive function."""
    print("AI Peer Finder with Ticker Conversion")
    print("=" * 50)

    while True:
        ticker = input("\nEnter ticker symbol (or 'quit' to exit): ").strip().upper()

        if ticker.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        if not ticker:
            print("Please enter a valid ticker symbol.")
            continue

        # Get peers with tickers
        result = get_peers_with_tickers(ticker, include_details=True)

        if "error" in result:
            print(f"Error: {result['error']}")
            continue

        # Display summary
        print(f"\nSuccessfully processed {ticker}")
        print(f"   Company: {result['input_company']}")
        print(f"   Peers found: {result['total_peers']}")
        print(f"   Tickers matched: {result['matched_peers']}")
        if result['estimated_cost_cents']:
            print(".4f"        print(f"   Peer tickers: {', '.join(result['peer_tickers'])}")

        # Ask to save results
        save_choice = input("\nSave results to JSON file? (y/n): ").strip().lower()
        if save_choice in ['y', 'yes']:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"peers_tickers_{ticker}_{timestamp}.json"

            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"Results saved to: {filename}")
            except Exception as e:
                print(f"Error saving file: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()