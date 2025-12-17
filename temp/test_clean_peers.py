#!/usr/bin/env python3
"""
Test the updated AI peer finding prompts to ensure they return clean company names
"""

from web_app.peers.peer_getter import find_peers_for_ticker_ai

def test_clean_peer_names():
    """Test that AI returns clean company names without suffixes"""

    print("Testing AI peer finding with updated prompts...")

    # Test with Apple
    peers, error = find_peers_for_ticker_ai("AAPL", "Apple")

    if error:
        print(f"Error: {error}")
        return

    if not peers:
        print("No peers returned")
        return

    print(f"Found {len(peers)} peers for Apple:")
    for i, peer in enumerate(peers, 1):
        print(f"{i}. '{peer}'")

    # Check if any peers have generic suffixes
    generic_suffixes = [' inc', ' corp', ' co', ' ltd', ' llc', ' group', ' holdings', ' corporation', ' incorporated', ' limited']
    clean_count = 0
    suffix_count = 0

    for peer in peers:
        peer_lower = peer.lower()
        has_suffix = any(peer_lower.endswith(suffix) for suffix in generic_suffixes)

        if has_suffix:
            suffix_count += 1
            print(f"❌ Has suffix: '{peer}'")
        else:
            clean_count += 1
            print(f"✅ Clean: '{peer}'")

    print(f"\nSummary:")
    print(f"Clean names: {clean_count}")
    print(f"Names with suffixes: {suffix_count}")
    print(f"Clean rate: {clean_count/(clean_count+suffix_count)*100:.1f}%")

if __name__ == "__main__":
    test_clean_peer_names()