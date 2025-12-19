import pytest
import math
from web_app.backend.core.financial_scorer import (
    _calc_ebit_ppe,
    _calc_gross_margin,
    _calc_operating_margin,
    _calc_revenue_growth,
    _calc_growth_consistency,
    _calc_operating_margin_consistency,
    _calc_operating_margin_growth,
    _calc_net_debt_to_ttm_operating_income,
    _get_period_dates,
    calculate_percentile,
    _process_stock,
    _rank_metric,
    _calculate_total_percentile,
    MetricConfig,
    METRICS
)

def test_calculate_percentile():
    assert calculate_percentile(1, 10) == 100.0
    assert calculate_percentile(10, 10) == 10.0
    assert calculate_percentile(1, 1) == 100.0
    assert calculate_percentile(1, 0) == 0.0

def test_process_stock():
    stock_data = {
        "symbol": "AAPL",
        "company_name": "Apple Inc",
        "data": {
            "period_end_date": ["2023-12-31"],
            "market_cap": [2000000000000.0],
            "operating_income": [100.0],
            "ppe_net": [50.0]
        }
    }
    result = _process_stock(stock_data, "NASDAQ")
    assert result["symbol"] == "AAPL"
    assert result["exchange"] == "NASDAQ"
    assert result["market_cap"] == 2000000000000.0
    assert result["ebit_ppe"] == 2.0
    assert result["period"] == "2023-12-31"

def test_rank_metric():
    all_stock_data = [
        {"ticker": "A", "val": 10.0},
        {"ticker": "B", "val": 20.0},
        {"ticker": "C", "val": None}
    ]
    # Update mock all_stock_data to match expected keys for _rank_metric
    for s in all_stock_data:
        s["test_metric"] = s["val"]
        
    metric = MetricConfig(
        key="test_metric",
        display_name="Test",
        description="Test",
        calculator=lambda x: None,
        sort_descending=True
    )
    
    _rank_metric(all_stock_data, metric)
    
    # B should be rank 1 (20.0), A should be rank 2 (10.0)
    assert next(s for s in all_stock_data if s["ticker"] == "B")["test_metric_rank"] == 1
    assert next(s for s in all_stock_data if s["ticker"] == "A")["test_metric_rank"] == 2
    assert next(s for s in all_stock_data if s["ticker"] == "C")["test_metric_rank"] is None

def test_calculate_total_percentile():
    # Mock METRICS to only include our test metrics
    m1 = MetricConfig(key="m1", display_name="M1", description="", calculator=lambda x: None)
    m2 = MetricConfig(key="m2", display_name="M2", description="", calculator=lambda x: None)
    
    import web_app.backend.core.financial_scorer as scorer
    original_metrics = scorer.METRICS
    scorer.METRICS = [m1, m2]
    
    try:
        all_stock_data = [
            {"m1": 10, "m1_rank": 1, "m2": 20, "m2_rank": 1}, # Avg rank 1
            {"m1": 5, "m1_rank": 2, "m2": 10, "m2_rank": 2},  # Avg rank 2
            {"m1": 1, "m1_rank": 3, "m2": None, "m2_rank": None} # Missing m2
        ]
        
        _calculate_total_percentile(all_stock_data)
        
        assert all_stock_data[0]["total_rank"] == 1
        assert all_stock_data[0]["total_percentile"] == 100.0
        assert all_stock_data[1]["total_rank"] == 2
        assert all_stock_data[1]["total_percentile"] == 50.0
        assert all_stock_data[2]["total_rank"] is None
    finally:
        scorer.METRICS = original_metrics

def test_load_save_scores(tmp_path):
    import web_app.backend.core.financial_scorer as scorer
    import json
    import os
    
    test_file = os.path.join(tmp_path, "test_scores.json")
    scores_data = [
        {"symbol": "AAPL", "company_name": "Apple", "total_percentile": 90.0}
    ]
    
    # Save
    scorer.save_scores_to_json(scores_data, test_file)
    assert os.path.exists(test_file)
    
    # Load
    loaded = scorer.load_scores_from_json(test_file)
    assert loaded["scores"][0]["symbol"] == "AAPL"
    
    # Lookup
    from unittest.mock import patch
    with patch('web_app.backend.core.financial_scorer.load_scores_from_json') as mock_load:
        mock_load.return_value = {"scores": scores_data}
        result = scorer.lookup_stock("AAPL")
        assert result["company_name"] == "Apple"
        
        result_none = scorer.lookup_stock("INVALID")
        assert result_none is None

def test_load_data_from_jsonl(tmp_path):
    import web_app.backend.core.financial_scorer as scorer
    import os
    
    test_file = os.path.join(tmp_path, "test.jsonl")
    with open(test_file, 'w') as f:
        f.write('{"symbol": "AAPL"}\n')
        f.write('{"symbol": "MSFT"}\n')
        f.write('invalid json\n')
        
    stocks = scorer.load_data_from_jsonl(test_file)
    assert len(stocks) == 2
    assert stocks[0]["symbol"] == "AAPL"
    assert stocks[1]["symbol"] == "MSFT"

def test_get_period_dates():
    data = {"period_end_date": ["2023-12-31"]}
    assert _get_period_dates(data) == ["2023-12-31"]
    
    data = {"fiscal_quarter_key": ["2023Q4"]}
    assert _get_period_dates(data) == ["2023Q4"]
    
    data = {"original_filing_date": ["2024-01-30"]}
    assert _get_period_dates(data) == ["2024-01-30"]
    
    data = {}
    assert _get_period_dates(data) is None

def test_calc_ebit_ppe():
    stock_data = {
        "symbol": "AAPL",
        "company_name": "Apple Inc",
        "data": {
            "period_end_date": ["2023-12-31"],
            "operating_income": [100.0],
            "ppe_net": [50.0]
        }
    }
    result = _calc_ebit_ppe(stock_data)
    assert result == ("AAPL", "Apple Inc", 2.0, "2023-12-31")

    # Test with missing data
    assert _calc_ebit_ppe({}) is None
    assert _calc_ebit_ppe({"data": {}}) is None

def test_calc_gross_margin():
    stock_data = {
        "symbol": "AAPL",
        "company_name": "Apple Inc",
        "data": {
            "period_end_date": ["2023-12-31"],
            "revenue": [200.0],
            "cost_of_goods_sold": [120.0]
        }
    }
    result = _calc_gross_margin(stock_data)
    # (200 - 120) / 200 = 80 / 200 = 0.4
    assert result == ("AAPL", "Apple Inc", 0.4, "2023-12-31")

def test_calc_operating_margin():
    stock_data = {
        "symbol": "AAPL",
        "company_name": "Apple Inc",
        "data": {
            "period_end_date": ["2023-12-31"],
            "revenue": [200.0],
            "operating_income": [40.0]
        }
    }
    result = _calc_operating_margin(stock_data)
    # 40 / 200 = 0.2
    assert result == ("AAPL", "Apple Inc", 0.2, "2023-12-31")

def test_calc_revenue_growth():
    revenue = [10.0] * 20 # 20 quarters of 10.0
    # Last 10 quarters (indices 10-19) sum = 100
    # First 10 quarters (indices 0-9) sum = 100
    # result = 100 / 100 = 1.0
    stock_data = {
        "symbol": "AAPL",
        "company_name": "Apple Inc",
        "data": {
            "period_end_date": [f"2023-Q{i}" for i in range(20)],
            "revenue": revenue
        }
    }
    result = _calc_revenue_growth(stock_data)
    assert result == ("AAPL", "Apple Inc", 1.0, "2023-Q19")

def test_calc_growth_consistency():
    # Constant revenue means constant YoY growth (0%)
    revenue = [100.0] * 20
    stock_data = {
        "symbol": "AAPL",
        "company_name": "Apple Inc",
        "data": {
            "period_end_date": [f"2023-Q{i}" for i in range(20)],
            "revenue": revenue
        }
    }
    result = _calc_growth_consistency(stock_data)
    assert result[2] == 0.0 # Standard deviation of 0

def test_calc_operating_margin_consistency():
    revenue = [100.0] * 20
    operating_income = [20.0] * 20
    stock_data = {
        "symbol": "AAPL",
        "company_name": "Apple Inc",
        "data": {
            "period_end_date": [f"2023-Q{i}" for i in range(20)],
            "revenue": revenue,
            "operating_income": operating_income
        }
    }
    result = _calc_operating_margin_consistency(stock_data)
    assert result[2] == 0.0 # Standard deviation of 0

def test_calc_operating_margin_growth():
    revenue = [100.0] * 20
    operating_income = [10.0] * 10 + [20.0] * 10
    # First 10 quarters margin: 10/100 = 0.1
    # Last 10 quarters margin: 20/100 = 0.2
    # Margin growth: 0.2 / 0.1 = 2.0
    stock_data = {
        "symbol": "AAPL",
        "company_name": "Apple Inc",
        "data": {
            "period_end_date": [f"2023-Q{i}" for i in range(20)],
            "revenue": revenue,
            "operating_income": operating_income
        }
    }
    result = _calc_operating_margin_growth(stock_data)
    assert result == ("AAPL", "Apple Inc", 2.0, "2023-Q19")

def test_calc_net_debt_to_ttm_operating_income():
    stock_data = {
        "symbol": "AAPL",
        "company_name": "Apple Inc",
        "data": {
            "period_end_date": ["2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4"],
            "net_debt": [0, 0, 0, 50.0],
            "operating_income": [10.0, 10.0, 10.0, 20.0]
        }
    }
    # TTM Operating Income = 10+10+10+20 = 50
    # Net Debt = 50
    # Ratio = 50 / 50 = 1.0
    result = _calc_net_debt_to_ttm_operating_income(stock_data)
    assert result == ("AAPL", "Apple Inc", 1.0, "2023-Q4")

    # Test edge cases
    # Case 1: Net cash + positive income
    stock_data["data"]["net_debt"][-1] = -10.0
    result = _calc_net_debt_to_ttm_operating_income(stock_data)
    assert result[2] == -10.0 / 50.0

    # Case 2: Net cash + negative income
    stock_data["data"]["operating_income"] = [-10.0] * 4
    result = _calc_net_debt_to_ttm_operating_income(stock_data)
    assert result[2] == 0.0

    # Case 6: Net debt + negative income
    stock_data["data"]["net_debt"][-1] = 50.0
    result = _calc_net_debt_to_ttm_operating_income(stock_data)
    assert result[2] == 50.0 / abs(-40.0) * 1000
