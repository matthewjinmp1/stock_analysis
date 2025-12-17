#!/usr/bin/env python3
"""
Quick test for AI peer finding - automatically tests AAPL
"""

import sys
import os
import time

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def quick_test():
    """Quick test of peer finding for AAPL."""
    print("Quick Peer Finder Test for AAPL")
    print("=" * 40)

    # Import required modules
    try:
        from src.clients.grok_client import GrokClient
        from src.clients.openrouter_client import OpenRouterClient
        from config import XAI_API_KEY, OPENROUTER_KEY
        from web_app.ui_cache_db import get_complete_data
        print("Modules imported successfully")
    except ImportError as e:
        print(f"Import error: {e}")
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

    # Test AAPL
    ticker = "AAPL"
    print(f"Testing ticker: {ticker}")

    # Get company data
    ticker_data = get_complete_data(ticker)
    if not ticker_data:
        print("No data found for AAPL")
        return

    company_name = ticker_data.get('company_name', ticker)
    print(f"Company: {company_name}")

    # Find peers
    try:
        print("Querying AI for peers...")

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

        start_time = time.time()
        grok = get_api_client()
        model = get_model_for_ticker(ticker)
        response, token_usage = grok.simple_query_with_tokens(prompt, model=model)
        elapsed_time = time.time() - start_time

        print(f"AI query completed in {elapsed_time:.2f} seconds")
        print(f"Response: {response[:200]}...")

        # Parse company names
        response_clean = response.strip()

        if ';' in response_clean:
            company_names = [name.strip() for name in response_clean.split(';') if name.strip()]
        else:
            company_names = [name.strip() for name in response_clean.split(',') if name.strip()]

        company_names = company_names[:10]

        print(f"\nFound {len(company_names)} peers:")
        for i, peer in enumerate(company_names, 1):
            print(f"{i:2d}. {peer}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_test()