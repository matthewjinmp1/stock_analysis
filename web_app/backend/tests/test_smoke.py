import sys
import os
import pytest

# Add the web_app directory to the path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def test_imports():
    """Verify that all major components can be imported without errors."""
    try:
        from web_app.backend.services.watchlist_service import WatchlistService
        from web_app.backend.services.data_service import DataService
        from web_app.backend.services.peers_service import PeersService
        from web_app.backend.services.adjusted_pe_service import AdjustedPEService
        from web_app.backend.controllers.api_controller import ApiController
        from web_app.backend.repositories.data_repository import DataRepository
        from web_app.backend.repositories.watchlist_repository import WatchlistRepository
        
        print("All imports successful")
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred during import: {e}")

def test_repository_initialization():
    """Verify that repositories can be initialized (this checks DB paths, etc.)."""
    from web_app.backend.repositories.data_repository import DataRepository
    from web_app.backend.repositories.watchlist_repository import WatchlistRepository
    
    try:
        data_repo = DataRepository()
        watchlist_repo = WatchlistRepository()
        assert data_repo is not None
        assert watchlist_repo is not None
    except Exception as e:
        pytest.fail(f"Repository initialization failed: {e}")
