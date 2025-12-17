#!/usr/bin/env python3
"""
Final test of complete word matching for peer name to ticker conversion
"""

from web_app.peers.get_company_names import find_ticker_for_company, get_ticker_database

def test_complete_word_matching():
    """Test that complete word matching works correctly"""

    # Get ticker database
    ticker_map = get_ticker_database()
    if not ticker_map:
        print("Could not load ticker database")
        return

    # Test cases that should work (complete word matches)
    success_cases = [
        ("Meta", "META", "Meta Platforms, Inc."),
        ("Apple", "AAPL", "Apple Inc."),
        ("Microsoft", "MSFT", "Microsoft Corporation"),
        ("Alphabet", "GOOG", "Alphabet Inc."),
        ("Nike", "NKE", "Nike, Inc."),
        ("Sony", "SONY", "Sony Group Corporation"),
    ]

    print("Testing complete word matching:")
    print("=" * 50)

    print("SUCCESS cases (should match):")
    for ai_name, expected_ticker, expected_company in success_cases:
        ticker = find_ticker_for_company(ai_name, ticker_map)
        actual_company = ticker_map.get(ticker, "Unknown") if ticker else "None"

        if ticker == expected_ticker:
            print(f"  PASS: '{ai_name}' -> {ticker} ({actual_company})")
        else:
            print(f"  FAIL: '{ai_name}' -> {ticker or 'None'} (expected {expected_ticker})")

    print("\nTesting that incomplete words don't match:")

    # Test cases that should NOT work (incomplete words)
    # These should not match because they're not complete words
    fail_cases = ["Met", "Micr", "App", "Alph", "Nik", "Son"]

    for ai_name in fail_cases:
        ticker = find_ticker_for_company(ai_name, ticker_map)
        if ticker:
            company = ticker_map.get(ticker, "Unknown")
            print(f"  UNEXPECTED: '{ai_name}' matched {ticker} ({company})")
        else:
            print(f"  PASS: '{ai_name}' correctly did not match")

if __name__ == "__main__":
    test_complete_word_matching()