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
            
            # Find overall rating - try explicit patterns first
            rating = None
            
            # Pattern 1: "has an employee rating of X out of 5"
            match = re.search(r'has an employee rating of (\d+\.?\d*)\s*(?:out of|/)\s*5', snippet_text, re.IGNORECASE)
            if match:
                rating = float(match.group(1))
            
            # Pattern 2: Look for rating with context that suggests it's overall
            # Check for ratings that appear near words like "rating", "stars", "overall", etc.
            if not rating:
                # Find all ratings with their surrounding context
                rating_matches = list(re.finditer(r'(\d+\.?\d*)\s*(?:out of|/)\s*5', snippet_text, re.IGNORECASE))
                
                for match in rating_matches:
                    rating_val = float(match.group(1))
                    start_pos = max(0, match.start() - 50)  # Look 50 chars before
                    end_pos = min(len(snippet_text), match.end() + 50)  # Look 50 chars after
                    context = snippet_text[start_pos:end_pos].lower()
                    
                    # Check if this rating is in overall rating context
                    overall_indicators = ['employee rating', 'overall', 'stars', 'based on', 'company reviews']
                    category_indicators = ['culture', 'diversity', 'compensation', 'career', 'senior management', 'work/life', 'work-life']
                    
                    has_overall_indicator = any(ind in context for ind in overall_indicators)
                    has_category_indicator = any(ind in context for ind in category_indicators)
                    
                    # If it has overall indicators and no category indicators, it's likely the overall rating
                    if has_overall_indicator and not has_category_indicator:
                        rating = rating_val
                        break
                
                # If still no rating found, find ratings before category section
                if not rating and rating_matches:
                    # Find where category section starts
                    category_section_start = len(snippet_text)
                    for marker in ['Ratings by category', 'Culture & values', 'Diversity', 'Compensation']:
                        idx = snippet_text.find(marker)
                        if idx != -1 and idx < category_section_start:
                            category_section_start = idx
                    
                    # Get ratings before categories
                    ratings_before_categories = []
                    for match in rating_matches:
                        if match.start() < category_section_start:
                            ratings_before_categories.append(float(match.group(1)))
                    
                    if ratings_before_categories:
                        # Take the first rating before categories (overall appears first)
                        rating = ratings_before_categories[0]
                    else:
                        # If all ratings are in category section, take the first one
                        # (might be a short snippet where overall appears first)
                        if rating_matches:
                            rating = float(rating_matches[0].group(1))
            
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
        
        # Check related_questions first - often has the best snippet with overall rating
        if "related_questions" in results:
            for q in results["related_questions"]:
                if q.get("type") == "featured_snippet":
                    snippet = q.get("snippet", "")
                    link = q.get("link", "")
                    if snippet and "glassdoor" in snippet.lower():
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
                                'source': 'serpapi_related_questions'
                            }
        
        # Check answer box (often contains rich snippet with all stats)
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
        
        # Check organic results - prioritize rich_snippet which has structured data
        if "organic_results" in results:
            for result in results["organic_results"]:
                snippet = result.get("snippet", "")
                link = result.get("link", "")
                
                if "glassdoor" in snippet.lower() or "glassdoor.com" in link:
                    # First, check for rich_snippet which has structured rating data
                    rich_snippet = result.get("rich_snippet", {})
                    if rich_snippet:
                        top = rich_snippet.get("top", {})
                        detected = top.get("detected_extensions", {})
                        
                        # Extract rating from rich_snippet (most reliable)
                        if "rating" in detected:
                            rating = float(detected["rating"])
                            num_reviews = detected.get("reviews")
                            
                            # Parse snippet for additional stats
                            stats = parse_snippet(snippet)
                            
                            return {
                                'rating': rating,
                                'num_reviews': num_reviews or stats.get('num_reviews'),
                                'recommend_to_friend': stats.get('recommend_to_friend'),
                                'ceo_approval': stats.get('ceo_approval'),
                                'positive_business_outlook': stats.get('positive_business_outlook'),
                                'category_ratings': stats.get('category_ratings'),
                                'url': link,
                                'source': 'serpapi_rich_snippet'
                            }
                    
                    # Fallback to parsing snippet text
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
