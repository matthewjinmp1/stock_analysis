#!/usr/bin/env python3
"""
Script to populate financial scores database from JSON file.
"""

import os
import sys

# Ensure project root is on path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from web_app.financial_scores_db import init_database, populate_database_from_json

def main():
    """Main function to populate database."""
    print("=" * 60)
    print("Populating Financial Scores Database")
    print("=" * 60)
    
    # Initialize database
    init_database()
    print("Database initialized")
    
    # Try to populate from JSON
    json_file = None
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    
    if populate_database_from_json(json_file):
        print("\n" + "=" * 60)
        print("Database populated successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Could not populate database. Make sure scores.json exists.")
        print("You can specify the path: python populate_financial_scores.py <path_to_scores.json>")
        print("=" * 60)

if __name__ == '__main__':
    main()
