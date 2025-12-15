"""
Get Glassdoor rating for a company by using SerpAPI web search.
"""
import re
import os
import json
from typing import Optional, Dict
from datetime import datetime

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

# Cache file path
CACHE_FILE = os.path.join(os.path.dirname(__file__), 'glassdoor_cache.json')


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
        cached_data = cache[key]
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
            
            # Extract "recommend to friend" percentage - try multiple patterns
            recommend_patterns = [
                r'(\d+)%\s*(?:of\s+\w+\s+)?(?:employees\s+)?would\s+recommend(?: working there)?(?: to a friend)?',
                r'(\d+)%\s*(?:would\s+)?recommend(?: to a friend)?',
                r'(\d+)%\s*recommend',
            ]
            for pattern in recommend_patterns:
                recommend_match = re.search(pattern, snippet_text, re.IGNORECASE)
                if recommend_match:
                    stats['recommend_to_friend'] = int(recommend_match.group(1))
                    break
            
            # Extract CEO approval percentage - try multiple patterns
            ceo_patterns = [
                r'(\d+)%\s*approve of CEO',
                r'(\d+)%\s*CEO approval',
                r'CEO[:\s]+(\d+)%',
            ]
            for pattern in ceo_patterns:
                ceo_match = re.search(pattern, snippet_text, re.IGNORECASE)
                if ceo_match:
                    stats['ceo_approval'] = int(ceo_match.group(1))
                    break
            
            # Extract positive business outlook percentage - try multiple patterns
            outlook_patterns = [
                r'(\d+)%\s*positive business outlook',
                r'(\d+)%\s*business outlook',
                r'positive business outlook[:\s]+(\d+)%',
            ]
            for pattern in outlook_patterns:
                outlook_match = re.search(pattern, snippet_text, re.IGNORECASE)
                if outlook_match:
                    stats['positive_business_outlook'] = int(outlook_match.group(1))
                    break
            
            # Extract category ratings - look for patterns like:
            # "4.0 -- Culture & values"
            # "3.1 out of 5 for work life balance"
            # "rated Figma 3.1 out of 5 for work life balance"
            category_ratings = {}
            
            # Pattern 1: "X out of 5 for [category]"
            pattern1 = r'(\d+\.?\d*)\s*(?:out of|/)\s*5\s+for\s+([^,\.\n]+?)(?=[,\.\n]|$)'
            matches = re.finditer(pattern1, snippet_text, re.IGNORECASE)
            for match in matches:
                rating_val = float(match.group(1))
                category = match.group(2).strip()
                # Filter out overall rating mentions
                if category.lower() not in ['overall', 'rating', 'stars'] and len(category) > 3:
                    category_ratings[category] = rating_val
            
            # Pattern 2: "X -- Category Name" or "X - Category Name"
            if not category_ratings:
                pattern2 = r'(\d+\.?\d*)\s*[-–—]\s*([A-Z][^,\n\.]+?)(?=[,\n\.]|$)'
                matches = re.finditer(pattern2, snippet_text)
                for match in matches:
                    rating_val = float(match.group(1))
                    category = match.group(2).strip()
                    if len(category) > 3 and not re.match(r'^\d', category):
                        category_ratings[category] = rating_val
            
            # Pattern 3: Look for common category names with nearby ratings
            if not category_ratings:
                categories = ['Culture & values', 'Diversity', 'Compensation', 'Career opportunities', 
                             'Senior management', 'Work/Life balance', 'Work-Life balance', 'Work life balance']
                for category in categories:
                    # Find category name
                    cat_match = re.search(re.escape(category), snippet_text, re.IGNORECASE)
                    if cat_match:
                        # Look for rating before or after category (within 30 chars)
                        start = max(0, cat_match.start() - 30)
                        end = min(len(snippet_text), cat_match.end() + 30)
                        context = snippet_text[start:end]
                        rating_match = re.search(r'(\d+\.?\d*)\s*(?:out of|/)\s*5', context, re.IGNORECASE)
                        if rating_match:
                            category_ratings[category] = float(rating_match.group(1))
            
            if category_ratings:
                stats['category_ratings'] = category_ratings
            
            return stats
        
        # Collect stats from all sources and merge them
        combined_stats = {}
        best_url = None
        source = None
        
        # Check organic results first - prioritize rich_snippet which has structured data
        if "organic_results" in results:
            for result in results["organic_results"]:
                snippet = result.get("snippet", "")
                link = result.get("link", "")
                
                if "glassdoor" in snippet.lower() or "glassdoor.com" in link:
                    if not best_url:
                        best_url = link
                    
                    # Check for rich_snippet which has structured rating data (most reliable)
                    rich_snippet = result.get("rich_snippet", {})
                    if rich_snippet:
                        top = rich_snippet.get("top", {})
                        detected = top.get("detected_extensions", {})
                        
                        # Extract rating from rich_snippet (most reliable)
                        if "rating" in detected:
                            combined_stats['rating'] = float(detected["rating"])
                            if "reviews" in detected:
                                combined_stats['num_reviews'] = detected["reviews"]
                            if not source:
                                source = 'serpapi_rich_snippet'
                    
                    # Parse snippet for additional stats (recommend, CEO, outlook, categories)
                    snippet_stats = parse_snippet(snippet)
                    
                    # Merge stats, prioritizing already collected values
                    if not combined_stats.get('num_reviews') and snippet_stats.get('num_reviews'):
                        combined_stats['num_reviews'] = snippet_stats['num_reviews']
                    if not combined_stats.get('recommend_to_friend') and snippet_stats.get('recommend_to_friend'):
                        combined_stats['recommend_to_friend'] = snippet_stats['recommend_to_friend']
                    if not combined_stats.get('ceo_approval') and snippet_stats.get('ceo_approval'):
                        combined_stats['ceo_approval'] = snippet_stats['ceo_approval']
                    if not combined_stats.get('positive_business_outlook') and snippet_stats.get('positive_business_outlook'):
                        combined_stats['positive_business_outlook'] = snippet_stats['positive_business_outlook']
                    if not combined_stats.get('category_ratings') and snippet_stats.get('category_ratings'):
                        combined_stats['category_ratings'] = snippet_stats['category_ratings']
        
        # Check related_questions for additional stats
        if "related_questions" in results:
            for q in results["related_questions"]:
                if q.get("type") == "featured_snippet":
                    snippet = q.get("snippet", "")
                    link = q.get("link", "")
                    if snippet and "glassdoor" in snippet.lower():
                        if not best_url:
                            best_url = link
                        
                        snippet_stats = parse_snippet(snippet)
                        
                        # Merge stats, prioritizing already collected values
                        if not combined_stats.get('rating') and snippet_stats.get('rating'):
                            combined_stats['rating'] = snippet_stats['rating']
                        if not combined_stats.get('num_reviews') and snippet_stats.get('num_reviews'):
                            combined_stats['num_reviews'] = snippet_stats['num_reviews']
                        if not combined_stats.get('recommend_to_friend') and snippet_stats.get('recommend_to_friend'):
                            combined_stats['recommend_to_friend'] = snippet_stats['recommend_to_friend']
                        if not combined_stats.get('ceo_approval') and snippet_stats.get('ceo_approval'):
                            combined_stats['ceo_approval'] = snippet_stats['ceo_approval']
                        if not combined_stats.get('positive_business_outlook') and snippet_stats.get('positive_business_outlook'):
                            combined_stats['positive_business_outlook'] = snippet_stats['positive_business_outlook']
                        if not combined_stats.get('category_ratings') and snippet_stats.get('category_ratings'):
                            combined_stats['category_ratings'] = snippet_stats['category_ratings']
        
        # Check answer box for additional stats
        if "answer_box" in results:
            answer_box = results["answer_box"]
            snippet = answer_box.get("snippet", "")
            
            if snippet:
                if not best_url:
                    best_url = answer_box.get('link')
                
                snippet_stats = parse_snippet(snippet)
                
                # Merge stats, prioritizing already collected values
                if not combined_stats.get('rating') and snippet_stats.get('rating'):
                    combined_stats['rating'] = snippet_stats['rating']
                if not combined_stats.get('num_reviews') and snippet_stats.get('num_reviews'):
                    combined_stats['num_reviews'] = snippet_stats['num_reviews']
                if not combined_stats.get('recommend_to_friend') and snippet_stats.get('recommend_to_friend'):
                    combined_stats['recommend_to_friend'] = snippet_stats['recommend_to_friend']
                if not combined_stats.get('ceo_approval') and snippet_stats.get('ceo_approval'):
                    combined_stats['ceo_approval'] = snippet_stats['ceo_approval']
                if not combined_stats.get('positive_business_outlook') and snippet_stats.get('positive_business_outlook'):
                    combined_stats['positive_business_outlook'] = snippet_stats['positive_business_outlook']
                if not combined_stats.get('category_ratings') and snippet_stats.get('category_ratings'):
                    combined_stats['category_ratings'] = snippet_stats['category_ratings']
        
        # Return combined stats if we have at least a rating
        if combined_stats.get('rating'):
            combined_stats['url'] = best_url
            combined_stats['source'] = source or 'serpapi_combined'
            return combined_stats
        
        return None
        
    except Exception as e:
        print(f"SerpAPI snippet extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_glassdoor_rating(company_name: str, use_cache: bool = True) -> Optional[Dict[str, any]]:
    """
    Get Glassdoor rating for a company by using SerpAPI web search.
    Results are cached in a JSON file to avoid repeated API calls.
    
    Args:
        company_name: Name of the company
        use_cache: If True, check cache first and save results (default: True)
        
    Returns:
        Dictionary with 'rating', 'num_reviews', and 'url' keys, or None if not found
        
    Example:
        >>> result = get_glassdoor_rating("Apple")
        >>> print(result)
        {'rating': 4.3, 'num_reviews': 15000, 'url': 'https://www.glassdoor.com/...'}
    """
    # Check cache first
    if use_cache:
        cached_result = get_cached_result(company_name)
        if cached_result:
            print(f"Found cached result for: {company_name}")
            print(f"(Cached at: {cached_result.get('_cached_at', 'unknown')})")
            return cached_result
    
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
        
        # Cache the result
        if use_cache:
            cache_result(company_name, result)
        
        return result
    
    # If snippet extraction didn't work, try to find the URL and inform user
    print("Could not extract rating from search snippets. Searching for Glassdoor URL...")
    glassdoor_url = search_glassdoor_url(company_name)
    
    if glassdoor_url:
        print(f"Found Glassdoor URL: {glassdoor_url}")
        print("Note: Rating extraction from page requires web scraping which may be blocked.")
        print(f"Please visit the URL manually to see the rating: {glassdoor_url}")
        url_result = {
            'rating': None,
            'num_reviews': None,
            'url': glassdoor_url,
            'source': 'serpapi_url_only'
        }
        
        # Cache the URL result (even if no rating)
        if use_cache:
            cache_result(company_name, url_result)
        
        return url_result
    
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
        if result.get('_cached'):
            print(f"Cached: Yes (cached at {result.get('_cached_at', 'unknown')})")
        print("="*50)
    else:
        print(f"\nCould not find Glassdoor rating for {company_name}")
