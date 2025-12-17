#!/usr/bin/env python3
"""Test the peers_results.db integration"""

import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def test_peer_integration():
    """Test the peer database integration"""
    print("Testing peer database integration...")

    try:
        from web_app.peer_db import get_peers_for_ticker
        print("PASS: peer_db import successful")

        # Test getting peers for AAPL
        peers = get_peers_for_ticker('AAPL')
        print(f"PASS: get_peers_for_ticker('AAPL') returned {len(peers)} peers")

        if peers:
            print(f"  First peer: {peers[0]}")
            print(f"  Peer data structure: {type(peers[0])}")
            if isinstance(peers[0], dict):
                print(f"  Keys: {peers[0].keys()}")

        # Test with a ticker that might not have peers
        peers_empty = get_peers_for_ticker('NONEXISTENT')
        print(f"PASS: get_peers_for_ticker('NONEXISTENT') returned {len(peers_empty)} peers")

        print("PASS: All tests passed!")

    except Exception as e:
        print(f"FAIL: Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    test_peer_integration()