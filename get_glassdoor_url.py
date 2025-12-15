#!/usr/bin/env python3
"""
Simple script to get Glassdoor URL for a company using Grok (without web search tool).
Takes company name as user input and prints the URL that Grok produces.
"""

import sys
import re
import json

def check_api_availability():
    """Check if xAI SDK and API key are available."""
    try:
        from xai_sdk import Client
        from xai_sdk.chat import user
    except ImportError:
        print("Error: xAI SDK not available. Install with: pip install xai-sdk")
        return None, None
    
    try:
        from config import XAI_API_KEY
        if not XAI_API_KEY:
            print("Error: XAI_API_KEY not found in config.py")
            return None, None
    except ImportError:
        print("Error: config.py not found. Please create config.py with XAI_API_KEY")
        return None, None
    
    return Client, user

def get_glassdoor_url(company_name: str):
    """
    Ask Grok to provide the Glassdoor URL for a company (without web search tool).
    
    Args:
        company_name: Name of the company
        
    Returns:
        str or None: The Glassdoor URL, or None if not found
    """
    Client, user = check_api_availability()
    if Client is None:
        return None
    
    try:
        from config import XAI_API_KEY
        
        print(f"Querying Grok for Glassdoor URL of {company_name}...")
        
        # Initialize client
        client = Client(api_key=XAI_API_KEY)
        
        # Create chat WITHOUT web search tool (relying on Grok's knowledge)
        chat = client.chat.create(
            model="grok-4-1-fast",
            # No tools - Grok will use its training data/knowledge
        )
        
        # Create prompt asking for Glassdoor URL
        prompt = f"""What is the Glassdoor URL for {company_name}?

Please provide the URL to the company's Glassdoor page. 
Format your response as JSON with the following structure:
{{
    "url": "<glassdoor url or null>",
    "company_name": "{company_name}"
}}

If you cannot find the URL, return null for the url field."""
        
        # Send the prompt
        chat.append(user(prompt))
        
        # Get response
        response = chat.sample()
        
        print(f"Grok response received (length: {len(response.content)} chars)\n")
        print(f"Raw response:\n{response.content}\n")
        print("=" * 80)
        
        # Try to extract URL from the response
        url = None
        
        # Method 1: Try to parse JSON
        try:
            json_start = response.content.find('{')
            json_end = response.content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response.content[json_start:json_end]
                parsed_data = json.loads(json_str)
                url = parsed_data.get('url')
                if url and url.lower() != 'null':
                    return url
        except json.JSONDecodeError:
            pass
        
        # Method 2: Try regex to find Glassdoor URL
        url_match = re.search(r'https?://[^\s\)"]+glassdoor[^\s\)"]+', response.content, re.IGNORECASE)
        if url_match:
            url = url_match.group(0)
            return url
        
        # Method 3: Look for URL in markdown links
        markdown_url_match = re.search(r'\[.*?\]\((https?://[^\s\)]+glassdoor[^\s\)]+)\)', response.content, re.IGNORECASE)
        if markdown_url_match:
            url = markdown_url_match.group(1)
            return url
        
        return None
        
    except Exception as e:
        print(f"Error querying Grok: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function to get company name from user and print Glassdoor URL."""
    print("=" * 80)
    print("Glassdoor URL Finder (using Grok without web search)")
    print("=" * 80)
    print()
    
    # Get company name from command line or user input
    if len(sys.argv) >= 2:
        company_name = ' '.join(sys.argv[1:])
    else:
        company_name = input("Enter company name: ").strip()
    
    if not company_name:
        print("Error: No company name provided.")
        sys.exit(1)
    
    print(f"\nFetching Glassdoor URL for: {company_name}")
    print("=" * 80)
    
    url = get_glassdoor_url(company_name)
    
    print("\n" + "=" * 80)
    if url:
        print(f"Glassdoor URL: {url}")
    else:
        print("Could not find Glassdoor URL for this company.")
    print("=" * 80)

if __name__ == "__main__":
    main()
