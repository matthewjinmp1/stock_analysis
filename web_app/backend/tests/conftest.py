import pytest
from unittest.mock import MagicMock
import sys
import os

# Add project root to sys.path to resolve 'src' imports during collection
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Globally mock AI clients to prevent expensive API calls during tests
@pytest.fixture(autouse=True)
def mock_ai_clients(monkeypatch):
    """
    Globally mocks GrokClient and OpenRouterClient to prevent actual API calls.
    This fixture runs for every test automatically.
    """
    mock_grok = MagicMock()
    # Mock the common method used in the codebase
    mock_grok.return_value.simple_query_with_tokens.return_value = (
        "Microsoft|MSFT; Alphabet|GOOG; Meta|META; Amazon|AMZN; Nvidia|NVDA; Intel|INTC; AMD|AMD; Salesforce|CRM; Oracle|ORCL; Adobe|ADBE",
        {"total_tokens": 100, "estimated_cost_cents": 0.1}
    )
    
    mock_openrouter = MagicMock()
    mock_openrouter.return_value.simple_query_with_tokens.return_value = (
        "Microsoft|MSFT; Alphabet|GOOG; Meta|META; Amazon|AMZN; Nvidia|NVDA; Intel|INTC; AMD|AMD; Salesforce|CRM; Oracle|ORCL; Adobe|ADBE",
        {"total_tokens": 100, "estimated_cost_cents": 0.1}
    )

    # We use a dummy module to prevent ImportErrors if the actual files are not available or ignored
    class DummyClientModule:
        pass

    grok_module = DummyClientModule()
    grok_module.GrokClient = mock_grok
    
    openrouter_module = DummyClientModule()
    openrouter_module.OpenRouterClient = mock_openrouter

    # Inject into sys.modules
    monkeypatch.setitem(sys.modules, "src.clients.grok_client", grok_module)
    monkeypatch.setitem(sys.modules, "src.clients.openrouter_client", openrouter_module)
    
    # Also mock openai and anthropic to be safe, as they are often used for AI
    mock_openai = MagicMock()
    monkeypatch.setitem(sys.modules, "openai", mock_openai)
    
    mock_anthropic = MagicMock()
    monkeypatch.setitem(sys.modules, "anthropic", mock_anthropic)
