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
    Extract rating and stats from Google search result snippets using SerpAPI.
    
    Args:
        company_name: Name of the company
        
    Returns:
        Dictionary with rating info and additional stats if found in snippets, None otherwise
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
        
        # Helper function to extract stats from snippet text
        def parse_snippet(snippet_text: str) -> Dict:
            stats = {}
            
            # Find overall rating - look for patterns like "has an employee rating of X" or "X out of 5 stars"
            # This should come before category ratings
            overall_patterns = [
                r'has an employee rating of (\d+\.?\d*)\s*(?:out of|/)\s*5',
                r'(\d+\.?\d*)\s*(?:out of|/)\s*5\s*stars?',
                r'rating[:\s]+(\d+\.?\d*)\s*(?:out of|/)\s*5',
            ]
            
            rating = None
            for pattern in overall_patterns:
                match = re.search(pattern, snippet_text, re.IGNORECASE)
                if match:
                    rating = float(match.group(1))
                    break
            
            # If no overall pattern found, try to find the first rating that's likely overall
            # (usually appears early in the text, before "Ratings by category")
            if not rating:
                # Look for rating before "Ratings by category" or category names
                # Split by common category indicators
                before_categories = snippet_text
                for splitter in ['Ratings by category', 'Culture & values', 'Diversity', 'Compensation']:
                    if splitter in before_categories:
                        before_categories = before_categories.split(splitter)[0]
                        break
                
                # Look for the first rating in this section
                rating_match = re.search(r'(\d+\.?\d*)\s*(?:out of|/)\s*5', before_categories, re.IGNORECASE)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            if rating:
                stats['rating'] = rating
            
            # Extract number of reviews
            review_match = re.search(r'based on (\d+(?:,\d+)*)\s*company reviews?', snippet_text, re.IGNORECASE)
            if not review_match:
                review_match = re.search(r'(\d+(?:,\d+)*)\s*company reviews?', snippet_text, re.IGNORECASE)
            if not review_match:
                review_match = re.search(r'(\d+(?:,\d+)*)\s*reviews?', snippet_text, re.IGNORECASE)
            if review_match:
                stats['num_reviews'] = int(review_match.group(1).replace(',', ''))
            
            # Extract "recommend to friend" percentage
            recommend_match = re.search(r'(\d+)%\s*(?:would\s+)?recommend(?: to a friend)?', snippet_text, re.IGNORECASE)
            if recommend_match:
                stats['recommend_to_friend'] = int(recommend_match.group(1))
            
            # Extract CEO approval percentage
            ceo_match = re.search(r'(\d+)%\s*approve of CEO', snippet_text, re.IGNORECASE)
            if ceo_match:
                stats['ceo_approval'] = int(ceo_match.group(1))
            
            # Extract positive business outlook percentage
            outlook_match = re.search(r'(\d+)%\s*positive business outlook', snippet_text, re.IGNORECASE)
            if outlook_match:
                stats['positive_business_outlook'] = int(outlook_match.group(1))
            
            # Extract category ratings - look for patterns like "4.0 -- Culture & values"
            category_ratings = {}
            # Try multiple patterns for category ratings
            category_patterns = [
                r'(\d+\.?\d*)\s*[-–—]\s*([A-Z][^\\n]+?)(?=\\n|\d+\.|$)',
                r'(\d+\.?\d*)\s*[-–—]\s*([A-Z][^\\r\\n]+?)(?=\\r|\\n|\d+\.|$)',
                r'(\d+\.?\d*)\s*[-–—]\s*([A-Za-z][^\\n]+?)(?=\\n|$)',
            ]
            
            for pattern in category_patterns:
                category_matches = re.findall(pattern, snippet_text)
                for rating_val, category in category_matches:
                    # Filter out non-category matches (like dates, etc.)
                    category_clean = category.strip()
                    if len(category_clean) > 3 and not re.match(r'^\d', category_clean):
                        try:
                            category_ratings[category_clean] = float(rating_val)
                        except:
                            pass
                if category_ratings:
                    break
            
            if category_ratings:
                stats['category_ratings'] = category_ratings
            
            return stats
        
        # Check answer box first (often contains rich snippet with all stats)
        if "answer_box" in results:
            answer_box = results["answer_box"]
            snippet = answer_box.get("snippet", "")
            if snippet:
                stats = parse_snippet(snippet)
                if stats.get('rating'):
                    result = {
                        'rating': stats['rating'],
                        'num_reviews': stats.get('num_reviews'),
                        'recommend_to_friend': stats.get('recommend_to_friend'),
                        'ceo_approval': stats.get('ceo_approval'),
                        'positive_business_outlook': stats.get('positive_business_outlook'),
                        'category_ratings': stats.get('category_ratings'),
                        'url': answer_box.get('link'),
                        'source': 'serpapi_answer_box'
                    }
                    return result
        
        # Check organic results snippets
        if "organic_results" in results:
            for result in results["organic_results"]:
                snippet = result.get("snippet", "")
                link = result.get("link", "")
                if "glassdoor" in snippet.lower() or "glassdoor.com" in link:
                    stats = parse_snippet(snippet)
                    if stats.get('rating'):
                        return {
                            'rating': stats['rating'],
                            'num_reviews': stats.get('num_reviews'),
                            'recommend_to_friend': stats.get('recommend_to_friend'),
                            'ceo_approval': stats.get('ceo_approval'),
                            'positive_business_outlook': stats.get('positive_business_outlook'),
                            'category_ratings': stats.get('category_ratings'),
                            'url': link,
                            'source': 'serpapi_snippet'
                        }
        
        return None
        
    except Exception as e:
        print(f"SerpAPI snippet extraction failed: {e}")
        import traceback
        traceback.print_exc()
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
        print(f"Overall Rating: {result['rating']}/5.0")
        if result.get('num_reviews'):
            print(f"Number of reviews: {result['num_reviews']}")
        if result.get('recommend_to_friend'):
            print(f"Recommend to friend: {result['recommend_to_friend']}%")
        if result.get('ceo_approval'):
            print(f"CEO approval: {result['ceo_approval']}%")
        if result.get('positive_business_outlook'):
            print(f"Positive business outlook: {result['positive_business_outlook']}%")
        if result.get('category_ratings'):
            print("\nCategory Ratings:")
            for category, rating in result['category_ratings'].items():
                print(f"  {category}: {rating}/5.0")
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
        print("\n" + "="*50)
        print("RESULT")
        print("="*50)
        print(f"Company: {company_name}")
        if result.get('rating'):
            print(f"Overall Rating: {result['rating']}/5.0")
        if result.get('num_reviews'):
            print(f"Number of Reviews: {result['num_reviews']}")
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
            print(f"\nURL: {result['url']}")
        if result.get('source'):
            print(f"Source: {result['source']}")
        print("="*50)
    else:
        print(f"\nCould not find Glassdoor rating for {company_name}")
