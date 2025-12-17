#!/usr/bin/env python3
"""
Test the complete word matching for peer name to ticker conversion
"""

from web_app.peers.get_company_names import find_ticker_for_company, get_ticker_database

def test_word_matching():
    """Test complete word matching functionality"""

    # Get ticker database
    ticker_map = get_ticker_database()
    if not ticker_map:
        print("Could not load ticker database")
        return

    # Test cases
    test_cases = [
        ("Meta", "Meta Platforms, Inc.", "Should match - complete word"),
        ("Apple", "Apple Inc.", "Should match - complete word"),
        ("Microsoft", "Microsoft Corporation", "Should match - complete word"),
        ("Alphabet", "Alphabet Inc.", "Should match - complete word"),
        ("Nike", "Nike, Inc.", "Should match - complete word"),
        ("Amazon", "Amazon.com, Inc.", "Should match - complete word"),
        ("Tesla", "Tesla, Inc.", "Should match - complete word"),
        ("Sony", "Sony Group Corporation", "Should match - complete word"),
        # These should NOT match (incomplete words)
        ("Met", "Meta Platforms, Inc.", "Should NOT match - incomplete word"),
        ("Micr", "Microsoft Corporation", "Should NOT match - incomplete word"),
        ("App", "Apple Inc.", "Should NOT match - incomplete word"),
    ]

    print("Testing complete word matching:")
    print("=" * 60)

    for test_name, expected_db_name, description in test_cases:
        ticker = find_ticker_for_company(test_name, ticker_map)
        if ticker:
            # Verify it actually matches the expected company
            actual_db_name = ticker_map.get(ticker, "")
            match_correct = expected_db_name.lower() in actual_db_name.lower()
            status = "PASS" if match_correct else "WRONG"
        else:
            status = "FAIL"
            actual_db_name = "None"

        print(f"{status}: '{test_name}' -> {ticker or 'None'} ({actual_db_name}) - {description}")

if __name__ == "__main__":
    test_word_matching()