#!/usr/bin/env python3
"""
Web app wrapper for batch short interest scraper.

Runs the existing batch short interest scraper from src/scrapers/get_short_interest.py
and then syncs the generated short_interest.json into the web_app/data directory so the
web app can read it directly.
"""

import os
import sys
import shutil

# Ensure project root is on path so we can import src modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.scrapers.get_short_interest import main as scrape_short_interest

SRC_DATA_FILE = os.path.join(PROJECT_ROOT, "data", "short_interest.json")
WEBAPP_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
WEBAPP_DATA_FILE = os.path.join(WEBAPP_DATA_DIR, "short_interest.json")


def sync_short_interest_file() -> None:
    """Copy the scraped short_interest.json into web_app/data."""
    if not os.path.exists(SRC_DATA_FILE):
        print(f"Source short interest file not found: {SRC_DATA_FILE}")
        return

    os.makedirs(WEBAPP_DATA_DIR, exist_ok=True)
    shutil.copy2(SRC_DATA_FILE, WEBAPP_DATA_FILE)
    print(f"Synced short interest data to {WEBAPP_DATA_FILE}")


def main() -> None:
    """Run the scraper and sync its data into the web app folder."""
    # The batch scraper uses relative paths like "data/scores.json" based on CWD.
    # Temporarily change to the project root so those paths resolve correctly,
    # regardless of where this wrapper script is run from.
    prev_cwd = os.getcwd()
    try:
        os.chdir(PROJECT_ROOT)
        # Run the existing batch scraper (writes data/short_interest.json at project root)
        scrape_short_interest()
    finally:
        os.chdir(prev_cwd)

    # Sync the generated data into web_app/data
    sync_short_interest_file()


if __name__ == "__main__":
    main()

