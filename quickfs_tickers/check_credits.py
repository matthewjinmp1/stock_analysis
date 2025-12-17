#!/usr/bin/env python3
"""
Check QuickFS API credits and usage
"""

import os
import sys
import json

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Change to project root directory
os.chdir(PROJECT_ROOT)

# Try to import config
try:
    from config import QUICKFS_API_KEY
    API_KEY = QUICKFS_API_KEY
except ImportError:
    API_KEY = os.environ.get('QUICKFS_API_KEY')
    if not API_KEY:
        print("Error: QuickFS API key not found.")
        sys.exit(1)

def check_credits():
    """Check QuickFS credits using available methods"""
    try:
        from quickfs import QuickFS

        client = QuickFS(API_KEY)

        # Try different methods to check credits
        methods_to_try = []

        # Check if client has credit checking methods
        if hasattr(client, 'get_credits'):
            methods_to_try.append(('get_credits', lambda: client.get_credits()))
        if hasattr(client, 'check_credits'):
            methods_to_try.append(('check_credits', lambda: client.check_credits()))
        if hasattr(client, 'credits'):
            methods_to_try.append(('credits', lambda: client.credits()))
        if hasattr(client, 'get_api_usage'):
            methods_to_try.append(('get_api_usage', lambda: client.get_api_usage()))
        if hasattr(client, 'usage'):
            methods_to_try.append(('usage', lambda: client.usage()))

        # Try the methods
        results = {}
        for method_name, method_func in methods_to_try:
            try:
                print(f"Trying {method_name}...")
                result = method_func()
                results[method_name] = result
                print(f"  Success: {result}")
            except Exception as e:
                print(f"  Failed: {e}")
                results[method_name] = f"Error: {e}"

        # Try making a test API call to see if we get rate limit info
        print("\nMaking test API call to check rate limits...")
        try:
            # This should work for AAPL
            data = client.get_data_full('AAPL:US')
            if data:
                print("  Test API call successful")
            else:
                print("  Test API call returned no data")
        except Exception as e:
            error_str = str(e).lower()
            if 'rate limit' in error_str or '429' in error_str:
                print(f"  Rate limit detected: {e}")
                results['rate_limit'] = str(e)
            else:
                print(f"  Test API call failed: {e}")

        # Try to get API metadata which might include usage info
        print("\nChecking API metadata...")
        try:
            metadata = client.get_api_metadata()
            if metadata:
                print("  API metadata retrieved")
                results['metadata'] = metadata

                # Check if metadata contains usage info
                if isinstance(metadata, dict):
                    usage_keys = [k for k in metadata.keys() if 'usage' in k.lower() or 'credit' in k.lower() or 'limit' in k.lower()]
                    if usage_keys:
                        print(f"  Found usage-related keys: {usage_keys}")
                        for key in usage_keys:
                            print(f"    {key}: {metadata[key]}")
            else:
                print("  No metadata available")
        except Exception as e:
            print(f"  Metadata check failed: {e}")

        # Try direct API call to credits endpoint (if it exists)
        print("\nTrying direct credits API call...")
        import requests
        try:
            response = requests.get("https://public-api.quickfs.net/v1/credits", params={"api_key": API_KEY}, timeout=10)
            if response.status_code == 200:
                credits_data = response.json()
                print(f"  Credits API response: {credits_data}")
                results['direct_credits_api'] = credits_data
            else:
                print(f"  Credits API returned status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"  Direct credits API failed: {e}")

        return results

    except Exception as e:
        print(f"Error checking credits: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_credit_usage():
    """Analyze what API calls use credits"""
    print("Analyzing QuickFS API credit usage...")
    print("=" * 60)

    # Test different API calls to see which ones consume credits
    test_calls = [
        ('get_supported_companies', 'Get list of tickers for an exchange'),
        ('get_data_full', 'Get complete financial data for a ticker (used for company names)'),
        ('get_api_metadata', 'Get information about supported exchanges'),
    ]

    print("API Methods and their typical credit usage:")
    for method, description in test_calls:
        print(f"  {method}: {description}")

    print("\nCredit Usage Analysis:")
    print("  - get_supported_companies: Usually low/no credit cost (bulk data)")
    print("  - get_data_full: Typically costs 1 credit per call")
    print("  - get_api_metadata: Usually low/no credit cost")

    print("\nFor company name population:")
    print("  - Each ticker requires 1 get_data_full() call")
    print("  - So populating N company names costs N credits")
    print("  - With 17,278 tickers, this would cost 17,278 credits")

def main():
    """Main function"""
    print("QuickFS Credits Checker")
    print("=" * 60)

    # Check credits
    credit_info = check_credits()

    print(f"\n{'='*60}")
    print("CREDITS CHECK RESULTS")
    print(f"{'='*60}")

    if credit_info:
        print(json.dumps(credit_info, indent=2))
    else:
        print("Could not retrieve credit information.")

    # Analyze usage
    print("\n")
    analyze_credit_usage()

    print(f"\n{'='*60}")
    print("RECOMMENDATIONS")
    print(f"{'='*60}")
    print("1. Check your QuickFS dashboard at https://quickfs.net/ for accurate credit info")
    print("2. The get_data_full() method used for company names costs 1 credit per call")
    print("3. With 17,278 tickers, full population would cost 17,278 credits")
    print("4. Consider doing this in batches to manage credit usage")

if __name__ == '__main__':
    main()