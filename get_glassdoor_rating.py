"""
Get Glassdoor rating for a company by using web search to find the company's Glassdoor page.
"""
import requests
from bs4 import BeautifulSoup
import time
import re
from typing import Optional, Dict


def search_glassdoor_url(company_name: str) -> Optional[str]:
    """
    Use web search to find the Glassdoor URL for a company.
    
    Args:
        company_name: Name of the company to search for
        
    Returns:
        Glassdoor URL if found, None otherwise
    """
    try:
        # Search Google for the company's Glassdoor page
        search_query = f"{company_name} glassdoor rating site:glassdoor.com"
        google_search_url = f"https://www.google.com/search?q={requests.utils.quote(search_query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(google_search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract search result URLs
        glassdoor_urls = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and 'glassdoor.com' in href:
                # Clean up Google redirect URLs
                if href.startswith('/url?q='):
                    href = href.split('/url?q=')[1].split('&')[0]
                # Decode URL encoding
                href = requests.utils.unquote(href)
                
                # Look for company review or overview pages
                if ('glassdoor.com/Reviews' in href or 
                    'glassdoor.com/Overview' in href or
                    'glassdoor.com/Reviews/' in href):
                    if href not in glassdoor_urls:
                        glassdoor_urls.append(href)
        
        # Return the first valid Glassdoor URL found
        if glassdoor_urls:
            return glassdoor_urls[0]
        
        # Fallback: try constructing URL directly
        company_slug = company_name.lower().replace(' ', '-').replace(',', '').replace('.', '').replace('&', 'and')
        company_slug = re.sub(r'[^a-z0-9-]', '', company_slug)
        potential_url = f"https://www.glassdoor.com/Reviews/{company_slug}-Reviews-E1.htm"
        return potential_url
        
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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(glassdoor_url, headers=headers, timeout=10)
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
    print(f"Searching for Glassdoor page for: {company_name}")
    
    # Step 1: Use web search to find Glassdoor URL
    glassdoor_url = search_glassdoor_url(company_name)
    
    if not glassdoor_url:
        print(f"Could not find Glassdoor URL for {company_name}")
        return None
    
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
    
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python get_glassdoor_rating.py <company_name>")
        print("Example: python get_glassdoor_rating.py 'Apple Inc'")
        sys.exit(1)
    
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
