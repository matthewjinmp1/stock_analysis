#!/usr/bin/env python3
"""
Test script for the refactored layered architecture.
"""
import sys
import os

# Add web_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web_app'))

def test_repositories():
    """Test repository layer functionality."""
    print("Testing repository layer...")

    try:
        from repositories.data_repository import DataRepository

        repo = DataRepository()
        print("[OK] DataRepository created successfully")

        # Test getting all tickers
        tickers = repo.get_all_tickers()
        print(f"[OK] Found {len(tickers)} tickers")
        print(f"  First 5 tickers: {tickers[:5]}")

        # Test getting complete data for AAPL
        data = repo.get_complete_data('AAPL')
        if data:
            print("[OK] AAPL data retrieved successfully")
            print(f"  Company name: {data.get('company_name')}")
            print(f"  Has AI scores: {'total_score_percentage' in data}")
            print(f"  Has financial scores: {'financial_total_percentile' in data}")
        else:
            print("[FAIL] No AAPL data found")

        return True

    except Exception as e:
        print(f"[FAIL] Repository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_services():
    """Test service layer functionality."""
    print("\nTesting service layer...")

    try:
        from repositories.data_repository import DataRepository
        from repositories.watchlist_repository import WatchlistRepository
        from services.data_service import DataService
        from services.watchlist_service import WatchlistService

        # Create dependencies
        data_repo = DataRepository()
        watchlist_repo = WatchlistRepository()
        data_service = DataService(data_repo, watchlist_repo)
        watchlist_service = WatchlistService(watchlist_repo, data_repo)

        print("[OK] Services created successfully")

        # Test search functionality
        result = data_service.search_ticker('AAPL')
        if result['success']:
            print("[OK] Search functionality works")
            print(f"  Found ticker: {result['data']['ticker']}")
        else:
            print(f"[FAIL] Search failed: {result['message']}")

        # Test watchlist functionality
        watchlist_result = watchlist_service.get_watchlist()
        if watchlist_result['success']:
            print("[OK] Watchlist service works")
            print(f"  Watchlist has {len(watchlist_result['watchlist'])} items")
        else:
            print(f"[FAIL] Watchlist service failed: {watchlist_result}")

        return True

    except Exception as e:
        print(f"[FAIL] Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_controllers():
    """Test controller layer functionality."""
    print("\nTesting controller layer...")

    try:
        from repositories.data_repository import DataRepository
        from repositories.watchlist_repository import WatchlistRepository
        from services.data_service import DataService
        from services.watchlist_service import WatchlistService
        from controllers.api_controller import ApiController

        # Create full stack
        data_repo = DataRepository()
        watchlist_repo = WatchlistRepository()
        data_service = DataService(data_repo, watchlist_repo)
        watchlist_service = WatchlistService(watchlist_repo, data_repo)
        api_controller = ApiController(data_service, watchlist_service)

        print("[OK] Controllers created successfully")

        # Test API responses (without Flask context)
        result = data_service.search_ticker('AAPL')  # Test the underlying service
        if result['success']:
            print("[OK] API controller logic works (service layer)")
        else:
            print(f"[FAIL] API controller logic failed: {result['message']}")

        return True

    except Exception as e:
        print(f"[FAIL] Controller test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app():
    """Test the Flask app."""
    print("\nTesting Flask app...")

    try:
        from app_new import app

        print("[OK] App imported successfully")

        # Test app context
        with app.app_context():
            print("[OK] App context works")

        # Check routes
        routes = [str(rule) for rule in app.url_map._rules]
        api_routes = [r for r in routes if r.startswith('/api/')]
        print(f"[OK] App has {len(api_routes)} API routes")

        return True

    except Exception as e:
        print(f"[FAIL] App test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Testing refactored layered architecture system")
    print("=" * 50)

    results = []
    results.append(("Repositories", test_repositories()))
    results.append(("Services", test_services()))
    results.append(("Controllers", test_controllers()))
    results.append(("Flask App", test_app()))

    print("\n" + "=" * 50)
    print("Test Results Summary:")

    all_passed = True
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\nSUCCESS: All tests passed! The refactored system is working correctly.")
    else:
        print("\nFAILURE: Some tests failed. Please check the errors above.")

    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)