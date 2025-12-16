#!/usr/bin/env python3
"""
Script to get all financial data for a ticker using QuickFS API.
Uses the same QuickFS method as the project (QuickFS Python SDK).

Usage:
    python get_quickfs_data.py <TICKER>
    python get_quickfs_data.py AAPL
    
Or run without arguments for interactive mode:
    python get_quickfs_data.py
"""

import json
import os
import sys
from quickfs import QuickFS
from typing import Optional, Dict

# Try to import config, fallback to environment variable
try:
    from config import QUICKFS_API_KEY
    API_KEY = QUICKFS_API_KEY
except ImportError:
    # Try environment variable
    API_KEY = os.environ.get('QUICKFS_API_KEY')
    if not API_KEY:
        print("Error: QuickFS API key not found.")
        print("Please set QUICKFS_API_KEY environment variable or create config.py with QUICKFS_API_KEY")
        sys.exit(1)

def format_symbol(ticker: str) -> str:
    """
    Format ticker symbol for QuickFS (add :US for US stocks)
    Same method as used in src/data_collection/get_data.py
    
    Args:
        ticker: Ticker symbol
        
    Returns:
        Formatted ticker symbol
    """
    if ":" not in ticker:
        return f"{ticker}:US"
    return ticker

def get_all_data(ticker: str) -> Optional[Dict]:
    """
    Get all financial data for a ticker using QuickFS API.
    Uses the same method as src/data_collection/get_data.py
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary containing all financial data or None if error
    """
    ticker_upper = ticker.strip().upper()
    formatted_symbol = format_symbol(ticker_upper)
    
    print(f"\nFetching data for {ticker_upper} (formatted as {formatted_symbol})...")
    
    try:
        client = QuickFS(API_KEY)
        data = client.get_data_full(formatted_symbol)
        
        if not data:
            print(f"  No data returned for {ticker_upper}")
            return None
        
        # Extract metadata
        metadata = data.get("metadata", {})
        company_name = metadata.get("name", ticker_upper)
        
        # Extract financials
        financials = data.get("financials", {})
        quarterly = financials.get("quarterly", {})
        annual = financials.get("annual", {})
        
        result = {
            "symbol": ticker_upper,
            "company_name": company_name,
            "formatted_symbol": formatted_symbol,
            "metadata": metadata,
            "financials": {
                "quarterly": quarterly,
                "annual": annual
            },
            "raw_data": data  # Include full raw data
        }
        
        return result
        
    except Exception as e:
        error_str = str(e).lower()
        if '429' in error_str or 'rate limit' in error_str or 'too many requests' in error_str:
            print(f"  Error: Rate limit exceeded. Please wait and try again.")
        elif 'not found' in error_str or '404' in error_str:
            print(f"  Error: Ticker {ticker_upper} not found on QuickFS")
        else:
            print(f"  Error fetching data for {ticker_upper}: {e}")
        return None

def display_data(data: Dict):
    """Display the financial data in a readable format."""
    if not data:
        return
    
    ticker = data.get("symbol", "UNKNOWN")
    company_name = data.get("company_name", ticker)
    
    print(f"\n{'='*80}")
    print(f"FINANCIAL DATA FOR {ticker}")
    print(f"{'='*80}")
    print(f"Company: {company_name}")
    print(f"Formatted Symbol: {data.get('formatted_symbol')}")
    print(f"{'='*80}\n")
    
    # Display metadata
    metadata = data.get("metadata", {})
    if metadata:
        print("METADATA:")
        print(f"  Name: {metadata.get('name', 'N/A')}")
        print(f"  Exchange: {metadata.get('exchange', 'N/A')}")
        print(f"  Country: {metadata.get('country', 'N/A')}")
        print(f"  Currency: {metadata.get('currency', 'N/A')}")
        print()
    
    # Display quarterly data summary
    quarterly = data.get("financials", {}).get("quarterly", {})
    if quarterly:
        print("QUARTERLY DATA:")
        print(f"  Available metrics: {len(quarterly)}")
        
        # Show some key metrics
        key_metrics = ['revenue', 'operating_income', 'net_income', 'total_assets', 'total_liabilities']
        print("\n  Key Metrics (showing first few values):")
        for metric in key_metrics:
            if metric in quarterly:
                values = quarterly[metric]
                if isinstance(values, list) and len(values) > 0:
                    # Show first 3 values
                    preview = values[:3]
                    print(f"    {metric}: {preview} ... ({len(values)} total quarters)")
        
        print()
    
    # Display annual data summary
    annual = data.get("financials", {}).get("annual", {})
    if annual:
        print("ANNUAL DATA:")
        print(f"  Available metrics: {len(annual)}")
        print()
    
    # Ask if user wants to see full data
    print(f"{'='*80}")
    print("Full data structure available. Use JSON output option to see all data.")
    print(f"{'='*80}\n")

def save_to_json(data: Dict, ticker: str):
    """Save data to JSON file."""
    filename = f"quickfs_{ticker}_data.json"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to: {filename}")
    except Exception as e:
        print(f"Error saving to file: {e}")

def process_ticker(ticker: str, save_json: bool = False):
    """Process a single ticker and display results."""
    ticker = ticker.strip().upper()
    
    if not ticker:
        print("Error: Empty ticker provided")
        return
    
    data = get_all_data(ticker)
    
    if data:
        display_data(data)
        
        if save_json:
            save_to_json(data, ticker)
        else:
            # Ask if user wants to save
            try:
                save = input("Save data to JSON file? (y/n): ").strip().lower()
                if save in ['y', 'yes']:
                    save_to_json(data, ticker)
            except (EOFError, KeyboardInterrupt):
                pass
        
        # Print JSON output option
        print("\nTo see full JSON data, run with --json flag or check saved file.")
    else:
        print(f"\n{'='*80}")
        print(f"Could not fetch data for {ticker}")
        print(f"{'='*80}\n")

def main():
    """Main function with interactive loop."""
    print(f"\n{'='*80}")
    print("QuickFS Data Fetcher")
    print(f"{'='*80}")
    print("Get all financial data for tickers using QuickFS API")
    print("Commands:")
    print("  - Enter a ticker to fetch data (e.g., AAPL, TSLA)")
    print("  - Type 'quit' or 'exit' to exit")
    print("  - Type 'help' for more information")
    print("  - Type 'json' to toggle JSON saving mode")
    print(f"{'='*80}\n")
    
    save_json_mode = False
    
    # Check if ticker provided as command line argument
    if len(sys.argv) >= 2:
        ticker = sys.argv[1].strip().upper()
        if ticker in ['QUIT', 'EXIT', 'HELP']:
            # Treat as command, fall through to interactive mode
            pass
        elif ticker == '--JSON' or ticker == '-J':
            save_json_mode = True
            print("JSON saving mode enabled. All data will be saved automatically.")
        else:
            # Process the ticker and exit
            process_ticker(ticker, save_json=save_json_mode)
            return
    
    # Interactive loop
    while True:
        try:
            prompt = "\nEnter ticker (or 'quit' to exit)"
            if save_json_mode:
                prompt += " [JSON mode ON]"
            prompt += ": "
            
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
            
            user_input_upper = user_input.upper()
            
            # Handle commands
            if user_input_upper in ['QUIT', 'EXIT', 'Q']:
                print("\nExiting...")
                break
            elif user_input_upper in ['HELP', 'H']:
                print("\n" + "="*80)
                print("HELP")
                print("="*80)
                print("Enter a stock ticker symbol to fetch all financial data from QuickFS API")
                print("\nExamples:")
                print("  AAPL  - Apple Inc.")
                print("  TSLA  - Tesla Inc.")
                print("  MSFT  - Microsoft Corporation")
                print("\nCommands:")
                print("  quit, exit, q  - Exit the program")
                print("  help, h        - Show this help message")
                print("  json, j        - Toggle JSON saving mode")
                print("\nData includes:")
                print("  - Quarterly financial statements")
                print("  - Annual financial statements")
                print("  - All available financial metrics")
                print("="*80)
                continue
            elif user_input_upper in ['JSON', 'J']:
                save_json_mode = not save_json_mode
                status = "ON" if save_json_mode else "OFF"
                print(f"JSON saving mode: {status}")
                continue
            
            # Process the ticker
            process_ticker(user_input, save_json=save_json_mode)
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except EOFError:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
            continue

if __name__ == '__main__':
    main()
