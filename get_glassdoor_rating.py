"""
Get Glassdoor rating for a company by using web search to find the company's Glassdoor page.
"""
import requests
from bs4 import BeautifulSoup
import time
import re
import os
from typing import Optional, Dict

# Try to import SerpAPI
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    print("Warning: serpapi not available. Install with: pip install google-search-results")

# Try to load API key from config or environment
SERP_API_KEY = None
try:
    import config
    SERP_API_KEY = getattr(config, 'SERP_API_KEY', None)
except ImportError:
    pass

if not SERP_API_KEY:
    SERP_API_KEY = os.getenv('SERP_API_KEY')


def search_glassdoor_url(company_name: str) -> Optional[str]:
    """
    Use web search to find the Glassdoor URL for a company using SerpAPI (preferred) or fallback to scraping.
    
    Args:
        company_name: Name of the company to search for
        
    Returns:
        Glassdoor URL if found, None otherwise
    """
    # Try SerpAPI first (much more reliable)
    if SERPAPI_AVAILABLE and SERP_API_KEY:
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
                        # Also accept other Glassdoor pages as fallback
                        elif "glassdoor.com" in link:
                            print(f"Found Glassdoor URL via SerpAPI: {link}")
                            return link
            
            # Also check knowledge graph and answer box
            if "answer_box" in results:
                answer_box = results["answer_box"]
                if "link" in answer_box and "glassdoor.com" in answer_box["link"]:
                    return answer_box["link"]
            
        except Exception as e:
            print(f"SerpAPI search failed: {e}")
            print("Falling back to web scraping method...")
    
    # Fallback: Use web scraping (original method)
    try:
        # Create a session to maintain cookies
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        session.headers.update(headers)
        
        # Try natural language search queries
        search_queries = [
            f"{company_name} glassdoor rating",
            f"{company_name} glassdoor reviews",
            f"{company_name} glassdoor site:glassdoor.com"
        ]
        
        glassdoor_urls = []
        
        for search_query in search_queries:
            try:
                google_search_url = f"https://www.google.com/search?q={requests.utils.quote(search_query)}"
                response = session.get(google_search_url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for result links in search results
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href:
                        # Extract URL from Google's redirect format
                        if href.startswith('/url?q='):
                            url = href.split('/url?q=')[1].split('&')[0]
                            url = requests.utils.unquote(url)
                            
                            # Check if it's a Glassdoor URL
                            if 'glassdoor.com' in url:
                                # Prefer Reviews or Overview pages
                                if any(pattern in url for pattern in ['/Reviews/', '/Overview/', '/Reviews', '/Overview']):
                                    if url not in glassdoor_urls:
                                        glassdoor_urls.append(url)
                                        print(f"Found potential URL from search: {url}")
                
                # If we found URLs, break early
                if glassdoor_urls:
                    break
                    
                time.sleep(0.5)  # Small delay between searches
                
            except Exception as e:
                print(f"Error with search query '{search_query}': {e}")
                continue
        
        # Return the best URL found (prefer Reviews pages)
        if glassdoor_urls:
            # Prioritize URLs with /Reviews/ in them
            reviews_urls = [url for url in glassdoor_urls if '/Reviews/' in url]
            if reviews_urls:
                return reviews_urls[0]
            return glassdoor_urls[0]
        
        print(f"Could not find Glassdoor URL from web search for {company_name}")
        return None
        
    except Exception as e:
        print(f"Error searching for Glassdoor URL: {e}")
        return None


def extract_rating_from_page(glassdoor_url: str) -> Optional[Dict[str, any]]:
    """
    Extract rating from a Glassdoor company page.
    
    Args:
        glassdoor_url: URL of the Glassdoor company page
        
    Returns:
        Dictionary with rating and number of reviews, or None if not found
    """
    try:
        # Use a session to maintain cookies and headers
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/'
        }
        session.headers.update(headers)
        
        # First, try to access the main Glassdoor page to establish session
        try:
            session.get('https://www.glassdoor.com', timeout=5)
            time.sleep(0.5)
        except:
            pass
        
        response = session.get(glassdoor_url, timeout=10)
        
        # Handle 403 errors
        if response.status_code == 403:
            print(f"Warning: Got 403 Forbidden. Glassdoor may be blocking automated requests.")
            print(f"Try accessing the URL manually: {glassdoor_url}")
            return None
        
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple selectors to find the rating
        rating = None
        num_reviews = None
        
        # Method 1: Look for rating in common Glassdoor structures
        rating_selectors = [
            {'class': 'rating'},
            {'data-test': 'rating'},
            {'class': 'ratingValue'},
            {'class': 'overallRating'},
            {'data-testid': 'rating'},
        ]
        
        for selector in rating_selectors:
            rating_elem = soup.find(attrs=selector)
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                # Extract number from text (e.g., "4.5" from "4.5 out of 5")
                match = re.search(r'(\d+\.?\d*)', rating_text)
                if match:
                    rating = float(match.group(1))
                    break
        
        # Method 2: Look for rating in JSON-LD structured data
        if not rating:
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'aggregateRating' in data:
                        agg_rating = data['aggregateRating']
                        if 'ratingValue' in agg_rating:
                            rating = float(agg_rating['ratingValue'])
                        if 'reviewCount' in agg_rating:
                            num_reviews = int(agg_rating['reviewCount'])
                        break
                except:
                    continue
        
        # Method 3: Look for rating in meta tags
        if not rating:
            meta_rating = soup.find('meta', property='og:rating')
            if meta_rating and meta_rating.get('content'):
                try:
                    rating = float(meta_rating['content'])
                except:
                    pass
        
        # Extract number of reviews
        review_selectors = [
            {'class': 'numReviews'},
            {'data-test': 'numReviews'},
            {'class': 'reviewCount'},
        ]
        
        for selector in review_selectors:
            reviews_elem = soup.find(attrs=selector)
            if reviews_elem:
                reviews_text = reviews_elem.get_text(strip=True)
                # Extract number from text (e.g., "1,234 reviews")
                match = re.search(r'([\d,]+)', reviews_text)
                if match:
                    num_reviews = int(match.group(1).replace(',', ''))
                    break
        
        if rating is not None:
            return {
                'rating': rating,
                'num_reviews': num_reviews,
                'url': glassdoor_url
            }
        
    except Exception as e:
        print(f"Error extracting rating from page: {e}")
    
    return None


def extract_rating_from_search_snippets(company_name: str) -> Optional[Dict[str, any]]:
    """
    Try to extract rating from Google search result snippets as a fallback.
    Uses SerpAPI if available, otherwise falls back to scraping.
    
    Args:
        company_name: Name of the company
        
    Returns:
        Dictionary with rating info if found in snippets, None otherwise
    """
    # Try SerpAPI first
    if SERPAPI_AVAILABLE and SERP_API_KEY:
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
                    if "glassdoor" in snippet.lower():
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
                                'url': result.get('link'),
                                'source': 'serpapi_snippet'
                            }
        except Exception as e:
            print(f"SerpAPI snippet extraction failed: {e}")
    
    # Fallback: Web scraping
    try:
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        session.headers.update(headers)
        
        search_query = f"{company_name} glassdoor rating"
        google_search_url = f"https://www.google.com/search?q={requests.utils.quote(search_query)}"
        response = session.get(google_search_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for rating patterns in search result text
        rating_pattern = re.compile(r'(\d+\.?\d*)\s*(?:out of|/)\s*5', re.IGNORECASE)
        
        for text_elem in soup.find_all(['span', 'div', 'p']):
            text = text_elem.get_text()
            match = rating_pattern.search(text)
            if match and 'glassdoor' in text.lower():
                rating = float(match.group(1))
                # Try to find review count
                review_match = re.search(r'(\d+(?:,\d+)*)\s*reviews?', text, re.IGNORECASE)
                num_reviews = None
                if review_match:
                    num_reviews = int(review_match.group(1).replace(',', ''))
                
                return {
                    'rating': rating,
                    'num_reviews': num_reviews,
                    'url': None,
                    'source': 'search_snippet'
                }
        
    except Exception as e:
        pass
    
    return None


def get_glassdoor_rating(company_name: str) -> Optional[Dict[str, any]]:
    """
    Get Glassdoor rating for a company by using web search.
    
    Args:
        company_name: Name of the company
        
    Returns:
        Dictionary with 'rating', 'num_reviews', and 'url' keys, or None if not found
        
    Example:
        >>> result = get_glassdoor_rating("Apple")
        >>> print(result)
        {'rating': 4.3, 'num_reviews': 15000, 'url': 'https://www.glassdoor.com/...'}
    """
    if not SERPAPI_AVAILABLE or not SERP_API_KEY:
        print("Note: For better results, configure SerpAPI key in config.py or set SERP_API_KEY environment variable")
        print("Get your free API key from: https://serpapi.com/\n")
    
    print(f"Searching for Glassdoor page for: {company_name}")
    
    # Step 1: Use web search to find Glassdoor URL
    glassdoor_url = search_glassdoor_url(company_name)
    
    if not glassdoor_url:
        print(f"Could not find Glassdoor URL for {company_name}")
        # Try to extract from search snippets as fallback
        print("Attempting to extract rating from search snippets...")
        return extract_rating_from_search_snippets(company_name)
    
    print(f"Found Glassdoor URL: {glassdoor_url}")
    
    # Step 2: Extract rating from the page
    time.sleep(1)  # Rate limiting
    result = extract_rating_from_page(glassdoor_url)
    
    if result:
        print(f"Rating: {result['rating']}/5.0")
        if result.get('num_reviews'):
            print(f"Number of reviews: {result['num_reviews']}")
    else:
        print(f"Could not extract rating from {glassdoor_url}")
        # Try fallback: extract from search snippets
        print("Attempting to extract rating from search snippets as fallback...")
        snippet_result = extract_rating_from_search_snippets(company_name)
        if snippet_result:
            print(f"Found rating in search snippet: {snippet_result['rating']}/5.0")
            return snippet_result
    
    return result


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
        print(f"  Rating: {result['rating']}/5.0")
        if result.get('num_reviews'):
            print(f"  Reviews: {result['num_reviews']}")
        print(f"  URL: {result['url']}")
    else:
        print(f"\nCould not find Glassdoor rating for {company_name}")
