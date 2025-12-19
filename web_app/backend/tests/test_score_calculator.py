import sys
import os
import pytest

# Add the project root to the path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Add web_app to path
WEB_APP_ROOT = os.path.join(PROJECT_ROOT, 'web_app')
if WEB_APP_ROOT not in sys.path:
    sys.path.insert(0, WEB_APP_ROOT)

from web_app.backend.core.score_calculator import calculate_total_score, SCORE_DEFINITIONS

def test_calculate_total_score_all_zeros():
    """Test with all scores as zero."""
    scores = {key: 0 for key in SCORE_DEFINITIONS}
    total, max_score, percentage = calculate_total_score(scores)
    
    # Reverse scores will contribute (10-0)*weight = 10*weight
    # Normal scores will contribute 0*weight = 0
    assert total > 0
    assert max_score > 0
    assert 0 < percentage < 100

def test_calculate_total_score_all_tens():
    """Test with all scores as ten."""
    scores = {key: 10 for key in SCORE_DEFINITIONS}
    total, max_score, percentage = calculate_total_score(scores)
    
    # Reverse scores will contribute (10-10)*weight = 0
    # Normal scores will contribute 10*weight
    assert total > 0
    assert max_score > 0
    assert 0 < percentage < 100

def test_calculate_total_score_partial():
    """Test with some missing scores."""
    scores = {
        'moat_score': 8,
        'disruption_risk': 2  # Reverse score, so (10-2)=8
    }
    total, max_score, percentage = calculate_total_score(scores)
    assert total > 0
    assert max_score > 0

def test_calculate_total_score_invalid_values():
    """Test with non-numeric values."""
    scores = {
        'moat_score': 'high',
        'disruption_risk': None
    }
    total, max_score, percentage = calculate_total_score(scores)
    # Should not crash, just treat as zero
    assert max_score > 0
