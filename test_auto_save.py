#!/usr/bin/env python3
"""
Quick test to verify automatic database saving in peer_getter.py
"""

import sys
import os

# Add project root to path
current_dir = os.path.abspath(os.path.dirname(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_auto_save():
    """Test that the save_peers_to_database function works."""
    try:
        # Import the save function
        sys.path.append(os.path.join(current_dir, 'web_app', 'peers'))
        from peer_getter import save_peers_to_database

        # Test data
        ticker = "TEST"
        company_name = "Test Company Inc."
        peers = ["Company A", "Company B", "Company C"]
        token_usage = {"prompt_tokens": 100, "completion_tokens": 200}
        cost = 0.05

        print("Testing automatic database save...")
        success = save_peers_to_database(ticker, company_name, peers, token_usage, cost)

        if success:
            print("SUCCESS: Auto-save test passed!")
            return True
        else:
            print("FAILED: Auto-save test failed!")
            return False

    except Exception as e:
        print(f"ERROR: Error during test: {e}")
        return False

if __name__ == "__main__":
    test_auto_save()