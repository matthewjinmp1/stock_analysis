#!/usr/bin/env python3
"""
Simple script to get Glassdoor rating for a single company by ticker symbol.
Uses Grok 4.1 Fast with xAI SDK web search tool for RAG (Retrieval-Augmented Generation).
Grok performs actual web searches to find and extract current Glassdoor ratings.

Usage: python get_rating.py AAPL
       python get_rating.py MSFT
       python get_rating.py  (will prompt for ticker)
"""
import sys
import os
import json
from typing import Optional, Dict
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from get_glassdoor_rating import ticker_to_company_name

# Cache file path (in web_app directory)
CACHE_FILE = os.path.join(os.path.dirname(__file__), 'grok_glassdoor_cache.json')


def load_cache() -> Dict[str, Dict]:
    """
    Load cached results from JSON file.
    
    Returns:
        Dictionary mapping company names to cached results
    """
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load cache file: {e}")
            return {}
    return {}


def save_cache(cache: Dict[str, Dict]) -> None:
    """
    Save cache to JSON file.
    
    Args:
        cache: Dictionary mapping company names to cached results
    """
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save cache file: {e}")


def get_cached_result(company_name: str) -> Optional[Dict[str, any]]:
    """
    Get cached result for a company if available.
    
    Args:
        company_name: Name of the company
        
    Returns:
        Cached result dictionary or None if not found
    """
    cache = load_cache()
    # Normalize company name for cache lookup (lowercase)
    key = company_name.lower().strip()
    if key in cache:
        cached_data = cache[key].copy()
        # Add a flag to indicate this is from cache
        cached_data['_cached'] = True
        cached_data['_cached_at'] = cached_data.get('_cached_at', 'unknown')
        return cached_data
    return None


def cache_result(company_name: str, result: Dict[str, any]) -> None:
    """
    Cache a result for a company.
    
    Args:
        company_name: Name of the company
        result: Result dictionary to cache
    """
    cache = load_cache()
    # Normalize company name for cache lookup (lowercase)
    key = company_name.lower().strip()
    
    # Create a copy without internal flags for caching
    cache_entry = {k: v for k, v in result.items() if not k.startswith('_')}
    cache_entry['_cached_at'] = datetime.now().isoformat()
    
    cache[key] = cache_entry
    save_cache(cache)


def check_api_availability():
    """Check if xAI SDK and API key are available."""
    try:
        from xai_sdk import Client
        from xai_sdk.chat import user
        from xai_sdk.tools import web_search
        from config import XAI_API_KEY
        
        if not XAI_API_KEY:
            print("Error: XAI_API_KEY not found in config.py")
            print("Please make sure your xAI Grok API key is configured.")
            print("Get your API key from: https://console.x.ai/")
            return False
        return True
    except ImportError as e:
        print(f"Error: xAI SDK not available. Install with: pip install xai-sdk")
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Error checking API availability: {e}")
        return False


def get_glassdoor_rating_with_web_search(company_name: str, ticker: str, use_cache: bool = True):
    """
    Use Grok with web search tool to find and extract Glassdoor rating.
    
    Args:
        company_name: Name of the company
        ticker: Stock ticker symbol
        use_cache: If True, check cache first and save results (default: True)
        
    Returns:
        Dictionary with rating information or None if error
    """
    # Check cache first
    if use_cache:
        cached_result = get_cached_result(company_name)
        if cached_result:
            print(f"Found cached result for: {company_name}")
            print(f"(Cached at: {cached_result.get('_cached_at', 'unknown')})")
            # Ensure ticker is set
            cached_result['ticker'] = ticker
            cached_result['company_name'] = company_name
            return cached_result
    
    try:
        from xai_sdk import Client
        from xai_sdk.chat import user
        from xai_sdk.tools import web_search
        from config import XAI_API_KEY
        
        print(f"Creating Grok chat session with web search enabled...")
        
        # Initialize client
        client = Client(api_key=XAI_API_KEY)
        
        # Create chat with web search tool enabled
        chat = client.chat.create(
            model="grok-4-1-fast",
            tools=[
                web_search(),  # Enable web search + page browsing
            ],
        )
        
        # Create prompt that asks Grok to search and extract Glassdoor rating
        prompt = f"""Find the current Glassdoor rating for {company_name} (stock ticker: {ticker}).

Use web search to find "{company_name} Glassdoor rating" and extract the following information:
1. The overall rating (out of 5.0)
2. The number of reviews (if available)
3. Recommend to friend percentage (if available)
4. CEO approval percentage (if available)
5. Positive business outlook percentage (if available)
6. Category ratings (Work/Life Balance, Culture & Values, Career Opportunities, etc.) if available
7. The Glassdoor URL

Format your response as JSON with the following structure:
{{
    "rating": <number between 0 and 5, or null if not found>,
    "num_reviews": <number or null>,
    "recommend_to_friend": <percentage number or null>,
    "ceo_approval": <percentage number or null>,
    "positive_business_outlook": <percentage number or null>,
    "category_ratings": {{
        "Work/Life Balance": <rating>,
        "Culture & Values": <rating>,
        ...
    }} or null,
    "url": "<glassdoor url or null>",
    "snippet": "<brief summary of the rating information>"
}}

IMPORTANT: Use web search to find the actual current Glassdoor rating. Include citations/links for the information you find.
"""
        
        print(f"Querying Grok with web search for {company_name}...")
        
        # Send the prompt
        chat.append(user(prompt))
        
        # Get response
        response = chat.sample()
        
        print(f"Grok response received (length: {len(response.content)} chars)")
        
        # Extract usage information if available
        token_usage = {}
        total_cost = 0.0
        
        # Check if response has usage information
        # xAI SDK might return usage in different formats
        if hasattr(response, 'usage'):
            usage = response.usage
            if usage:
                token_usage = {
                    'prompt_tokens': getattr(usage, 'prompt_tokens', 0),
                    'completion_tokens': getattr(usage, 'completion_tokens', 0),
                    'total_tokens': getattr(usage, 'total_tokens', 0),
                }
                # Check for cached tokens
                if hasattr(usage, 'prompt_cache_hit_tokens'):
                    token_usage['cached_tokens'] = usage.prompt_cache_hit_tokens
                elif hasattr(usage, 'cached_input_tokens'):
                    token_usage['cached_tokens'] = usage.cached_input_tokens
                
                # Calculate cost for grok-4-1-fast
                # Pricing: $0.20 per 1M input tokens, $0.50 per 1M output tokens, $0.05 per 1M cached input tokens
                input_cost_per_1M = 0.20
                output_cost_per_1M = 0.50
                cached_input_cost_per_1M = 0.05
                
                prompt_tokens = token_usage.get('prompt_tokens', 0)
                completion_tokens = token_usage.get('completion_tokens', 0)
                cached_tokens = token_usage.get('cached_tokens', 0)
                
                regular_input_tokens = max(0, prompt_tokens - cached_tokens)
                regular_input_cost = (regular_input_tokens / 1_000_000) * input_cost_per_1M
                cached_input_cost = (cached_tokens / 1_000_000) * cached_input_cost_per_1M
                output_cost = (completion_tokens / 1_000_000) * output_cost_per_1M
                
                total_cost = regular_input_cost + cached_input_cost + output_cost
        elif hasattr(response, 'token_usage'):
            # Alternative: check if usage is directly on response
            token_usage = response.token_usage
            if token_usage:
                # Calculate cost
                input_cost_per_1M = 0.20
                output_cost_per_1M = 0.50
                cached_input_cost_per_1M = 0.05
                
                prompt_tokens = token_usage.get('prompt_tokens', 0) if isinstance(token_usage, dict) else getattr(token_usage, 'prompt_tokens', 0)
                completion_tokens = token_usage.get('completion_tokens', 0) if isinstance(token_usage, dict) else getattr(token_usage, 'completion_tokens', 0)
                cached_tokens = token_usage.get('cached_tokens', 0) if isinstance(token_usage, dict) else getattr(token_usage, 'cached_tokens', 0)
                
                regular_input_tokens = max(0, prompt_tokens - cached_tokens)
                regular_input_cost = (regular_input_tokens / 1_000_000) * input_cost_per_1M
                cached_input_cost = (cached_tokens / 1_000_000) * cached_input_cost_per_1M
                output_cost = (completion_tokens / 1_000_000) * output_cost_per_1M
                
                total_cost = regular_input_cost + cached_input_cost + output_cost
                
                # Convert to dict if needed
                if not isinstance(token_usage, dict):
                    token_usage = {
                        'prompt_tokens': prompt_tokens,
                        'completion_tokens': completion_tokens,
                        'total_tokens': prompt_tokens + completion_tokens,
                        'cached_tokens': cached_tokens
                    }
        
        # Debug: print response attributes to help troubleshoot
        if not token_usage:
            print(f"Debug: Response attributes: {dir(response)}")
            if hasattr(response, '__dict__'):
                print(f"Debug: Response dict keys: {list(response.__dict__.keys())}")
        
        # Parse the response
        result = {
            "ticker": ticker,
            "company_name": company_name,
            "raw_response": response.content,
            "source": "grok_web_search",
            "token_usage": token_usage,
            "total_cost": total_cost
        }
        
        # Try to extract JSON from the response
        try:
            # Look for JSON in the response
            json_start = response.content.find('{')
            json_end = response.content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response.content[json_start:json_end]
                parsed_data = json.loads(json_str)
                result.update(parsed_data)
            else:
                # Try to extract rating from natural language using regex
                import re
                rating_match = re.search(r'"rating"\s*:\s*(\d+\.?\d*)', response.content, re.IGNORECASE)
                if not rating_match:
                    rating_match = re.search(r'rating["\']?\s*[:=]\s*(\d+\.?\d*)', response.content, re.IGNORECASE)
                if rating_match:
                    result["rating"] = float(rating_match.group(1))
                
                reviews_match = re.search(r'"num_reviews"\s*:\s*(\d+[,\d]*)', response.content, re.IGNORECASE)
                if not reviews_match:
                    reviews_match = re.search(r'reviews?["\']?\s*[:=]\s*(\d+[,\d]*)', response.content, re.IGNORECASE)
                if reviews_match:
                    result["num_reviews"] = int(reviews_match.group(1).replace(',', ''))
                
                url_match = re.search(r'https?://[^\s\)"]+glassdoor[^\s\)"]+', response.content, re.IGNORECASE)
                if url_match:
                    result["url"] = url_match.group(0)
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse JSON from response: {e}")
        except Exception as e:
            print(f"Warning: Error parsing response: {e}")
        
        # Cache the result
        if use_cache and result:
            cache_result(company_name, result)
        
        return result
        
    except Exception as e:
        print(f"Error querying Grok with web search: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Get and display Glassdoor rating for a ticker using Grok with web search."""
    # Check API availability first
    if not check_api_availability():
        sys.exit(1)
    
    if len(sys.argv) < 2:
        ticker = input("Enter ticker symbol: ").strip().upper()
        if not ticker:
            print("Error: No ticker provided")
            sys.exit(1)
    else:
        ticker = sys.argv[1].strip().upper()
    
    # Get company name from ticker
    print(f"Looking up company name for {ticker}...")
    company_name = ticker_to_company_name(ticker)
    
    if not company_name:
        print(f"Error: Ticker '{ticker}' not found in ticker database.")
        print("Please enter a valid ticker from stock_tickers_clean.json or ticker_definitions.json")
        sys.exit(1)
    
    print(f"Company name: {company_name}")
    print(f"\nFetching Glassdoor rating for {ticker} using Grok with web search...")
    print("=" * 80)
    
    # Use Grok with web search
    result = get_glassdoor_rating_with_web_search(company_name, ticker)
    
    if result:
        print("\n" + "=" * 80)
        print("RESULT:")
        print("=" * 80)
        print(f"Ticker: {ticker}")
        print(f"Company: {company_name}")
        if result.get('rating'):
            print(f"\nOverall Rating: {result['rating']}/5.0")
        if result.get('num_reviews'):
            print(f"Number of Reviews: {result['num_reviews']:,}")
        if result.get('recommend_to_friend'):
            print(f"Recommend to Friend: {result['recommend_to_friend']}%")
        if result.get('ceo_approval'):
            print(f"CEO Approval: {result['ceo_approval']}%")
        if result.get('positive_business_outlook'):
            print(f"Positive Business Outlook: {result['positive_business_outlook']}%")
        if result.get('category_ratings'):
            print("\nCategory Ratings:")
            for category, rating in result['category_ratings'].items():
                print(f"  • {category}: {rating}/5.0")
        if result.get('url'):
            print(f"\nGlassdoor URL: {result['url']}")
        if result.get('snippet'):
            print(f"\nSnippet: {result['snippet']}")
        if result.get('_cached'):
            print(f"\n(Cached result from {result.get('_cached_at', 'unknown')})")
        if result.get('token_usage') and result['token_usage'].get('total_tokens'):
            print(f"\nToken Usage:")
            print(f"  Total Tokens: {result['token_usage'].get('total_tokens', 0):,}")
            print(f"  Input Tokens: {result['token_usage'].get('prompt_tokens', 0):,}")
            print(f"  Output Tokens: {result['token_usage'].get('completion_tokens', 0):,}")
            if result['token_usage'].get('cached_tokens'):
                print(f"  Cached Tokens: {result['token_usage'].get('cached_tokens', 0):,}")
        if result.get('total_cost') and result['total_cost'] > 0:
            print(f"\nTotal Cost: ${result['total_cost']:.6f} USD")
            print(f"Total Cost: ${result['total_cost'] * 100:.4f} cents")
        print("=" * 80)
        
        # Also print as JSON for easy parsing
        print("\n" + "=" * 80)
        print("JSON OUTPUT:")
        print("=" * 80)
        print(json.dumps({
            'ticker': ticker,
            'company_name': result.get('company_name', company_name),
            'rating': result.get('rating'),
            'num_reviews': result.get('num_reviews'),
            'recommend_to_friend': result.get('recommend_to_friend'),
            'ceo_approval': result.get('ceo_approval'),
            'positive_business_outlook': result.get('positive_business_outlook'),
            'category_ratings': result.get('category_ratings'),
            'snippet': result.get('snippet'),
            'url': result.get('url'),
            'source': result.get('source', 'grok_web_search'),
            'token_usage': result.get('token_usage'),
            'total_cost_usd': result.get('total_cost', 0),
            'total_cost_cents': result.get('total_cost', 0) * 100 if result.get('total_cost') else 0
        }, indent=2))
    else:
        print(f"\nError: Could not fetch Glassdoor rating for {ticker}")
        sys.exit(1)


if __name__ == '__main__':
    main()

