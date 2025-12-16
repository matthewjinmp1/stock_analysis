#!/usr/bin/env python3
"""
Script to view raw data for a ticker from the source data files.
Usage:
    python view_ticker_data.py <TICKER>
    python view_ticker_data.py TSLA
"""

import json
import os
import sys

def find_ticker_data(ticker: str):
    """Find and return raw data for a ticker from both NYSE and NASDAQ files."""
    ticker_upper = ticker.upper()
    
    # Paths to data files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    nyse_file = os.path.join(script_dir, 'quantitative_stock_scorer', 'data', 'nyse_data.jsonl')
    nasdaq_file = os.path.join(script_dir, 'quantitative_stock_scorer', 'data', 'nasdaq_data.jsonl')
    
    files_to_check = [
        ('NYSE', nyse_file),
        ('NASDAQ', nasdaq_file)
    ]
    
    for exchange, filepath in files_to_check:
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found")
            continue
        
        print(f"\n{'='*80}")
        print(f"Searching in {exchange} file: {filepath}")
        print(f"{'='*80}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    symbol = data.get('symbol', '').upper()
                    
                    if symbol == ticker_upper:
                        print(f"\nFound {ticker_upper} in {exchange} file (line {line_num})")
                        print(f"\n{'='*80}")
                        print("RAW DATA:")
                        print(f"{'='*80}\n")
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                        print(f"\n{'='*80}")
                        return data
                        
                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON on line {line_num}: {e}")
                    continue
                except Exception as e:
                    print(f"Warning: Error processing line {line_num}: {e}")
                    continue
    
    print(f"\n{'='*80}")
    print(f"Ticker '{ticker_upper}' not found in any data files")
    print(f"{'='*80}")
    return None

def main():
    """Main function."""
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
    else:
        ticker = input("Enter ticker symbol: ").strip()
    
    if not ticker:
        print("Error: No ticker provided")
        sys.exit(1)
    
    find_ticker_data(ticker)

if __name__ == '__main__':
    main()
