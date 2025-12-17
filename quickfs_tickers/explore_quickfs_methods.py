#!/usr/bin/env python3
"""
Explore all available methods on the QuickFS API client
"""

import os
import sys
import inspect

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

def explore_quickfs_methods():
    """Explore all methods available on QuickFS client"""
    try:
        from quickfs import QuickFS

        print("Exploring QuickFS API Methods")
        print("=" * 50)

        # Create client instance
        client = QuickFS(API_KEY)

        # Get all methods and attributes
        methods = []
        for attr_name in dir(client):
            if not attr_name.startswith('_'):  # Skip private methods
                attr = getattr(client, attr_name)
                if callable(attr):
                    methods.append((attr_name, attr))

        print(f"Found {len(methods)} callable methods/attributes:")
        print()

        # Categorize methods
        data_methods = []
        utility_methods = []
        other_methods = []

        for method_name, method_obj in methods:
            if 'get_' in method_name:
                data_methods.append(method_name)
            elif any(word in method_name.lower() for word in ['usage', 'credit', 'quota', 'metadata', 'supported']):
                utility_methods.append(method_name)
            else:
                other_methods.append(method_name)

        # Display categorized methods
        print("DATA RETRIEVAL METHODS:")
        for method in sorted(data_methods):
            print(f"  - {method}")
        print()

        print("UTILITY METHODS:")
        for method in sorted(utility_methods):
            print(f"  - {method}")
        print()

        print("OTHER METHODS:")
        for method in sorted(other_methods):
            print(f"  - {method}")
        print()

        # Try to get method signatures where possible
        print("METHOD DETAILS:")
        print("-" * 30)

        detailed_methods = [
            'get_data_full',
            'get_supported_companies',
            'get_api_metadata',
            'get_usage'
        ]

        for method_name in detailed_methods:
            if hasattr(client, method_name):
                method = getattr(client, method_name)
                try:
                    sig = inspect.signature(method)
                    print(f"  {method_name}{sig}")
                except:
                    print(f"  {method_name}: signature unavailable")

        print("\n" + "=" * 50)
        print("QuickFS API exploration complete!")
        print("Most useful methods are in the DATA RETRIEVAL section above.")

    except Exception as e:
        print(f"Error exploring QuickFS methods: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    explore_quickfs_methods()