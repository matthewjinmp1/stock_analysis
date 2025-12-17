#!/usr/bin/env python3
"""
Debug the matching logic to understand why some names aren't matching
"""

from web_app.peers.get_company_names import normalize_company_name

def debug_matching():
    """Debug the normalization and matching"""

    test_cases = [
        ("Netflix", "Netflix, Inc."),
        ("Google", "Alphabet Inc."),
        ("Samsung", "Samsung Electronics Co Ltd"),
        ("Apple", "Apple Inc."),
        ("Microsoft", "Microsoft Corporation"),
    ]

    print("Debugging normalization and prefix matching:")
    print("=" * 60)

    for ai_name, db_name in test_cases:
        normalized_ai = normalize_company_name(ai_name)
        normalized_db = normalize_company_name(db_name)

        ai_is_prefix = normalized_db.startswith(normalized_ai)
        db_is_prefix = normalized_ai.startswith(normalized_db)

        print(f"AI: '{ai_name}' -> '{normalized_ai}'")
        print(f"DB: '{db_name}' -> '{normalized_db}'")
        print(f"AI is prefix of DB: {ai_is_prefix}")
        print(f"DB is prefix of AI: {db_is_prefix}")
        print("-" * 40)

if __name__ == "__main__":
    debug_matching()