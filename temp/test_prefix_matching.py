#!/usr/bin/env python3
"""
Test the exact prefix matching for peer name to ticker conversion
"""

from web_app.peers.get_company_names import find_ticker_for_company, get_ticker_database

def test_prefix_matching():
    """Test exact prefix matching functionality"""

    # Get ticker database
    ticker_map = get_ticker_database()
    if not ticker_map:
        print("Could not load ticker database")
        return

    # Test cases
    test_cases = [
        ("Apple", "Expected to match Apple Inc."),
        ("Microsoft", "Expected to match Microsoft Corporation"),
        ("Alphabet", "Expected to match Alphabet Inc."),
        ("Meta", "Expected to match Meta Platforms, Inc."),
        ("Nike", "Expected to match Nike, Inc."),
        ("Tesla", "Expected to match Tesla, Inc."),
        ("Amazon", "Expected to match Amazon.com, Inc."),
        ("Netflix", "Expected to match Netflix, Inc."),
        ("Google", "Should match Alphabet Inc. (reverse prefix)"),
        ("Sony", "Should match Sony Group Corporation"),
        ("Samsung", "Should match Samsung Electronics Co Ltd"),
    ]

    print("Testing exact prefix matching:")
    print("=" * 50)

    for test_name, expected in test_cases:
        ticker = find_ticker_for_company(test_name, ticker_map)
        status = "PASS" if ticker else "FAIL"
        result = f"{ticker}" if ticker else "None"
        print(f"{status}: '{test_name}' -> {result} ({expected})")

if __name__ == "__main__":
    test_prefix_matching()