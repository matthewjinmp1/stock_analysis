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

from web_app.financial_scores_db import init_database, populate_database_from_json, calculate_and_populate_database

def main():
    """Main function to populate database."""
    print("=" * 60)
    print("Populating Financial Scores Database")
    print("=" * 60)
    
    # Check if user wants to calculate from source or load from JSON
    if len(sys.argv) > 1:
        if sys.argv[1] == '--calculate' or sys.argv[1] == '-c':
            # Calculate scores from source data files
            if calculate_and_populate_database():
                print("\n" + "=" * 60)
                print("Database populated successfully from source data!")
                print("=" * 60)
            else:
                print("\n" + "=" * 60)
                print("Could not calculate and populate database.")
                print("=" * 60)
            return
        else:
            # User provided a JSON file path
            json_file = sys.argv[1]
            init_database()
            print("Database initialized")
            if populate_database_from_json(json_file):
                print("\n" + "=" * 60)
                print("Database populated successfully from JSON!")
                print("=" * 60)
            else:
                print("\n" + "=" * 60)
                print("Could not populate database from JSON file.")
                print("=" * 60)
            return
    
    # Default: Try to calculate from source data, fallback to JSON
    print("Calculating scores from source data files...")
    if calculate_and_populate_database():
        print("\n" + "=" * 60)
        print("Database populated successfully from source data!")
        print("=" * 60)
    else:
        print("\nTrying to load from existing scores.json file...")
        init_database()
        print("Database initialized")
        if populate_database_from_json(None):
            print("\n" + "=" * 60)
            print("Database populated successfully from JSON!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("Could not populate database.")
            print("Options:")
            print("  1. Run with --calculate to calculate from source data")
            print("  2. Run with <path_to_scores.json> to load from JSON file")
            print("=" * 60)

if __name__ == '__main__':
    main()
