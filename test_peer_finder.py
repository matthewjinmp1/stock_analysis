#!/usr/bin/env python3
"""
Test script for AI peer finding functionality.
Allows testing the peer discovery from command line.
"""

import sys
import os
import time

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def test_peer_finder():
    """Test the AI peer finding functionality."""
    print("AI Peer Finder Test")
    print("=" * 50)

    # Import required modules
    try:
        from src.clients.grok_client import GrokClient
        from src.clients.openrouter_client import OpenRouterClient
        from config import XAI_API_KEY, OPENROUTER_KEY
        from web_app.ui_cache_db import get_complete_data
        AI_AVAILABLE = True
        print("AI modules imported successfully")
    except ImportError as e:
        print(f"Failed to import AI modules: {e}")
        print("Make sure you have the required dependencies and config files.")
        return

    def get_api_client():
        """Get configured API client."""
        if XAI_API_KEY:
            return GrokClient(XAI_API_KEY)
        elif OPENROUTER_KEY:
            return OpenRouterClient(OPENROUTER_KEY)
        else:
            raise ValueError("No API key configured")

    def get_model_for_ticker(ticker):
        """Get appropriate model for ticker analysis."""
        return "grok-4-1-fast-reasoning" if XAI_API_KEY else "anthropic/claude-3.5-sonnet"

    def find_peers_for_ticker_ai(ticker, company_name=None):
        """Find peers for a ticker using AI."""
        try:
            # Get company name if not provided
            if not company_name:
                ticker_data = get_complete_data(ticker)
                company_name = ticker_data.get('company_name') if ticker_data else ticker

            print(f"Finding peers for: {ticker} ({company_name})")

            # Create AI prompt
            prompt = f"""You are analyzing companies to find the 10 most comparable companies to {company_name} ({ticker}).

Your task is to find the 10 MOST comparable companies to {company_name}.

Consider factors such as:
1. Industry and market segment similarity (MUST be in same or very similar industry)
2. Business model similarity
3. Product/service similarity
4. Market overlap and customer base similarity
5. Competitive dynamics (direct competitors)
6. Company size and scale (if relevant)

Return ONLY a semicolon-separated list of exactly 10 FULL company names, starting with the most comparable company first.
CRITICAL: Use semicolons (;) to separate company names, NOT commas, because company names often contain commas.
Each company name must be complete (e.g., "Microsoft Corporation", "Alphabet Inc.", "Meta Platforms Inc.", "Nike, Inc.").
DO NOT return partial names, suffixes alone (like "Inc" or "Corporation"), or abbreviations.
Each name should be the full legal company name or commonly used full name.
Do not include explanations, ticker symbols, ranking numbers, or any other text - just the 10 complete company names separated by semicolons in order from most to least comparable.

Example format: "Microsoft Corporation; Alphabet Inc.; Meta Platforms Inc.; Amazon.com Inc.; NVIDIA Corporation; Intel Corporation; Advanced Micro Devices Inc.; Salesforce Inc.; Oracle Corporation; Adobe Inc."

Return exactly 10 complete company names in ranked order, separated by semicolons, nothing else."""

            print("Querying AI for peer recommendations...")
            start_time = time.time()

            # Query AI
            grok = get_api_client()
            model = get_model_for_ticker(ticker)
            response, token_usage = grok.simple_query_with_tokens(prompt, model=model)

            elapsed_time = time.time() - start_time
            print(f"AI query completed in {elapsed_time:.2f} seconds")
            if token_usage:
                # Calculate cost
                from company_keywords.generate_company_keywords import calculate_grok_cost
                cost = calculate_grok_cost(token_usage, "grok-4-1-fast-reasoning")
                print(f"Estimated cost: ${cost:.6f}")
                print(f"Token usage: {token_usage}")

            # Parse company names
            response_clean = response.strip()

            # Split by semicolons first (preferred), then fall back to commas if needed
            if ';' in response_clean:
                company_names = [name.strip() for name in response_clean.split(';') if name.strip()]
            else:
                # Fallback: try to split by commas, but this is less reliable
                company_names = [name.strip() for name in response_clean.split(',') if name.strip()]

            # Clean up company names and limit to 10
            company_names = company_names[:10]

            return company_names, None

        except Exception as e:
            return None, str(e)

    # Main test loop
    while True:
        print("\n" + "=" * 50)
        ticker = input("Enter ticker symbol (or 'quit' to exit): ").strip().upper()

        if ticker.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        if not ticker:
            print("Please enter a valid ticker symbol.")
            continue

        print(f"\nTesting peer finding for: {ticker}")

        # Get company data first
        print("Fetching company data...")
        ticker_data = get_complete_data(ticker)

        if not ticker_data:
            print(f"No data found for ticker: {ticker}")
            print("Make sure the ticker exists and has been analyzed.")
            continue

        company_name = ticker_data.get('company_name', ticker)
        print(f"Found company: {company_name}")

        # Find peers
        peers, error = find_peers_for_ticker_ai(ticker, company_name)

        if error:
            print(f"Error finding peers: {error}")
            continue

        if not peers:
            print("No peers found.")
            continue

        # Display results
        print("\nAI-Generated Peer Recommendations:")
        print("-" * 40)

        for i, peer in enumerate(peers, 1):
            print(f"{i:2d}. {peer}")

        print(f"\nTotal peers found: {len(peers)}")
        print("Test completed successfully!")

if __name__ == "__main__":
    try:
        test_peer_finder()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Goodbye!")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()