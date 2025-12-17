#!/usr/bin/env python3
"""
Test script to verify that peer results are properly replaced when a ticker is rerun
"""

from web_app.peers.peers_results_db import save_peer_analysis, get_peer_analysis

def test_peer_replacement():
    """Test that re-running a ticker replaces old peer results"""

    ticker = "TEST"
    company_name = "Test Company"

    # First run - save some peers
    peers1 = ["Company A", "Company B", "Company C"]
    success1 = save_peer_analysis(ticker, company_name, peers1)
    print(f"First save successful: {success1}")

    # Check results
    results1 = get_peer_analysis(ticker, limit=1)
    if results1:
        print(f"First run - Peers: {results1[0]['peers']}")
        print(f"First run - Timestamp: {results1[0]['analysis_timestamp']}")

    # Second run - save different peers (simulate re-run)
    peers2 = ["Company X", "Company Y", "Company Z"]
    success2 = save_peer_analysis(ticker, company_name, peers2)
    print(f"\nSecond save successful: {success2}")

    # Check results again
    results2 = get_peer_analysis(ticker, limit=1)
    if results2:
        print(f"Second run - Peers: {results2[0]['peers']}")
        print(f"Second run - Timestamp: {results2[0]['analysis_timestamp']}")

    # Verify that old peers are gone and new ones are there
    if results2 and results2[0]['peers'] == peers2:
        print("\n✅ SUCCESS: Old peer results were replaced with new ones")
    else:
        print("\n❌ FAILURE: Peer results were not properly replaced")

    # Check that we only have one analysis (the most recent)
    all_results = get_peer_analysis(ticker, limit=10)
    if len(all_results) == 1:
        print("✅ SUCCESS: Only one analysis remains (most recent)")
    else:
        print(f"❌ FAILURE: Found {len(all_results)} analyses, expected 1")

if __name__ == "__main__":
    test_peer_replacement()