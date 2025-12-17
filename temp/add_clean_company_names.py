#!/usr/bin/env python3
"""
Add a new column to tickers.db with cleaned company names (generic suffixes removed)
"""

import sqlite3
import re

def clean_company_name(company_name):
    """Clean company name by removing generic suffixes from the end."""
    if not company_name:
        return company_name

    # Convert to lowercase for processing
    name_lower = company_name.lower().strip()

    # Generic suffixes to remove (in order of specificity, longest first)
    suffixes = [
        # Financial instruments (longest first)
        ' warrants, each whole warrant entitles the holder to purchase one',
        ' units, each consisting of one',
        ' american depository shares',

        # Common legal suffixes
        ' corporation', ' incorporated', ' technologies', ' technology',
        ' international', ' industries', ' associates', ' partners',
        ' partnership', ' investment', ' management', ' worldwide',

        # Shorter suffixes
        ' corp.', ' corp', ' inc.', ' inc', ' limited', ' ltd.', ' ltd',
        ' llc', ' lp', ' plc', ' co.', ' co', ' group', ' holdings',
        ' systems', ' solutions', ' global', ' common', ' stock',
        ' shares', ' services', ' financial', ' capital', ' fund',
        ' trust', ' usa', ' us', ' america',

        # Acquisition and special purpose
        ' acquisition corp.', ' acquisition corp', ' acquisition inc.', ' acquisition inc',
        ' merger corp.', ' merger corp', ' merger sub.', ' merger sub',

        # ETFs and funds
        ' bear 1x shares', ' bull 1x shares', ' 1x shares', ' ads',
    ]

    # Remove suffixes from the end
    result = name_lower
    for suffix in suffixes:
        if result.endswith(suffix):
            result = result[:-len(suffix)].strip()
            # Continue checking for more suffixes (e.g., "Inc Corp" -> remove both)
            break

    # Clean up trailing punctuation
    result = result.rstrip(',;:. -')

    # Clean up extra spaces and normalize
    result = re.sub(r'\s+', ' ', result).strip()

    # Capitalize words properly (simple title case)
    if result:
        words = result.split()
        # Handle Roman numerals and special cases
        capitalized_words = []
        for word in words:
            # Keep Roman numerals uppercase
            if word.upper() in ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']:
                capitalized_words.append(word.upper())
            else:
                capitalized_words.append(word.capitalize())
        result = ' '.join(capitalized_words)

    return result

def add_clean_company_name_column():
    """Add clean_company_name column to tickers.db and populate it."""

    conn = sqlite3.connect('web_app/data/tickers.db')
    cur = conn.cursor()

    # Add the new column if it doesn't exist
    try:
        cur.execute('ALTER TABLE tickers ADD COLUMN clean_company_name TEXT')
        print("Added clean_company_name column")
    except sqlite3.OperationalError:
        print("clean_company_name column already exists (reprocessing existing data)")

    # Get all company names and update with cleaned versions
    cur.execute('SELECT rowid, company_name FROM tickers')
    rows = cur.fetchall()

    updated_count = 0
    for rowid, company_name in rows:
        cleaned = clean_company_name(company_name)
        cur.execute('UPDATE tickers SET clean_company_name = ? WHERE rowid = ?',
                   (cleaned, rowid))
        updated_count += 1

        # Print progress every 1000 records
        if updated_count % 1000 == 0:
            print(f"Processed {updated_count} records...")

    conn.commit()

    # Show some examples
    cur.execute('SELECT company_name, clean_company_name FROM tickers LIMIT 10')
    examples = cur.fetchall()

    print(f"\nUpdated {updated_count} records")
    print("\nExamples:")
    for original, cleaned in examples:
        print(f'  "{original}" -> "{cleaned}"')

    # Show statistics
    cur.execute('SELECT COUNT(*) FROM tickers WHERE clean_company_name != company_name')
    changed_count = cur.fetchone()[0]
    print(f"\nRecords with cleaned names: {changed_count}")

    conn.close()

if __name__ == "__main__":
    print("Adding clean company name column to tickers.db...")
    add_clean_company_name_column()
    print("Done!")