"""
Get Glassdoor rating for a company by using SerpAPI web search.
"""
import re
import os
from typing import Optional, Dict

# Import SerpAPI
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    print("Error: serpapi not available. Install with: pip install google-search-results")
    exit(1)

# Try to load API key from config or environment
SERP_API_KEY = None
try:
    import config
    SERP_API_KEY = getattr(config, 'SERP_API_KEY', None)
except ImportError:
    pass

if not SERP_API_KEY:
    SERP_API_KEY = os.getenv('SERP_API_KEY')

if not SERP_API_KEY:
    print("Error: SERP_API_KEY not found. Set it in config.py or as environment variable SERP_API_KEY")
    print("Get your free API key from: https://serpapi.com/")
    exit(1)


def search_glassdoor_url(company_name: str) -> Optional[str]:
    """
    Use SerpAPI to find the Glassdoor URL for a company.
    
    Args:
        company_name: Name of the company to search for
        
    Returns:
        Glassdoor URL if found, None otherwise
    """
    try:
        # Use natural language search query
        search_query = f"{company_name} glassdoor rating"
        
        params = {
            "q": search_query,
            "api_key": SERP_API_KEY,
            "engine": "google",
            "num": 10  # Get top 10 results
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Look through organic results for Glassdoor URLs
        if "organic_results" in results:
            for result in results["organic_results"]:
                link = result.get("link", "")
                if "glassdoor.com" in link:
                    # Prefer Reviews or Overview pages
                    if any(pattern in link for pattern in ["/Reviews/", "/Overview/"]):
                        print(f"Found Glassdoor URL via SerpAPI: {link}")
                        return link
                    # Also accept other Glassdoor pages
                    elif "glassdoor.com" in link:
                        print(f"Found Glassdoor URL via SerpAPI: {link}")
                        return link
        
        # Also check answer box
        if "answer_box" in results:
            answer_box = results["answer_box"]
            if "link" in answer_box and "glassdoor.com" in answer_box["link"]:
                return answer_box["link"]
        
        return None
        
    except Exception as e:
        print(f"SerpAPI search failed: {e}")
        return None


def extract_rating_from_search_snippets(company_name: str) -> Optional[Dict[str, any]]:
    """
    Extract rating from Google search result snippets using SerpAPI.
    
    Args:
        company_name: Name of the company
        
    Returns:
        Dictionary with rating info if found in snippets, None otherwise
    """
    try:
        search_query = f"{company_name} glassdoor rating"
        
        params = {
            "q": search_query,
            "api_key": SERP_API_KEY,
            "engine": "google"
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Check answer box first (often contains rating)
        if "answer_box" in results:
            answer_box = results["answer_box"]
            snippet = answer_box.get("snippet", "")
            rating_match = re.search(r'(\d+\.?\d*)\s*(?:out of|/)\s*5', snippet, re.IGNORECASE)
            if rating_match:
                rating = float(rating_match.group(1))
                review_match = re.search(r'(\d+(?:,\d+)*)\s*reviews?', snippet, re.IGNORECASE)
                num_reviews = None
                if review_match:
                    num_reviews = int(review_match.group(1).replace(',', ''))
                return {
                    'rating': rating,
                    'num_reviews': num_reviews,
                    'url': answer_box.get('link'),
                    'source': 'serpapi_answer_box'
                }
        
        # Check organic results snippets
        if "organic_results" in results:
            for result in results["organic_results"]:
                snippet = result.get("snippet", "")
                link = result.get("link", "")
                if "glassdoor" in snippet.lower() or "glassdoor.com" in link:
                    rating_match = re.search(r'(\d+\.?\d*)\s*(?:out of|/)\s*5', snippet, re.IGNORECASE)
                    if rating_match:
                        rating = float(rating_match.group(1))
                        review_match = re.search(r'(\d+(?:,\d+)*)\s*reviews?', snippet, re.IGNORECASE)
                        num_reviews = None
                        if review_match:
                            num_reviews = int(review_match.group(1).replace(',', ''))
                        return {
                            'rating': rating,
                            'num_reviews': num_reviews,
                            'url': link,
                            'source': 'serpapi_snippet'
                        }
        
        return None
        
    except Exception as e:
        print(f"SerpAPI snippet extraction failed: {e}")
        return None


def get_glassdoor_rating(company_name: str) -> Optional[Dict[str, any]]:
    """
    Get Glassdoor rating for a company by using SerpAPI web search.
    
    Args:
        company_name: Name of the company
        
    Returns:
        Dictionary with 'rating', 'num_reviews', and 'url' keys, or None if not found
        
    Example:
        >>> result = get_glassdoor_rating("Apple")
        >>> print(result)
        {'rating': 4.3, 'num_reviews': 15000, 'url': 'https://www.glassdoor.com/...'}
    """
    print(f"Searching for Glassdoor rating for: {company_name}")
    
    # Try to extract rating directly from search snippets (faster and more reliable)
    print("Extracting rating from search results...")
    result = extract_rating_from_search_snippets(company_name)
    
    if result:
        print(f"Rating: {result['rating']}/5.0")
        if result.get('num_reviews'):
            print(f"Number of reviews: {result['num_reviews']}")
        return result
    
    # If snippet extraction didn't work, try to find the URL and inform user
    print("Could not extract rating from search snippets. Searching for Glassdoor URL...")
    glassdoor_url = search_glassdoor_url(company_name)
    
    if glassdoor_url:
        print(f"Found Glassdoor URL: {glassdoor_url}")
        print("Note: Rating extraction from page requires web scraping which may be blocked.")
        print(f"Please visit the URL manually to see the rating: {glassdoor_url}")
        return {
            'rating': None,
            'num_reviews': None,
            'url': glassdoor_url,
            'source': 'serpapi_url_only'
        }
    
    print(f"Could not find Glassdoor information for {company_name}")
    return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        company_name = input("Enter company name: ").strip()
        if not company_name:
            print("Error: Company name cannot be empty.")
            sys.exit(1)
    else:
        company_name = ' '.join(sys.argv[1:])
    
    result = get_glassdoor_rating(company_name)
    
    if result:
        print("\nResult:")
        print(f"  Company: {company_name}")
        if result.get('rating'):
            print(f"  Rating: {result['rating']}/5.0")
        if result.get('num_reviews'):
            print(f"  Reviews: {result['num_reviews']}")
        if result.get('url'):
            print(f"  URL: {result['url']}")
        if result.get('source'):
            print(f"  Source: {result['source']}")
    else:
        print(f"\nCould not find Glassdoor rating for {company_name}")
