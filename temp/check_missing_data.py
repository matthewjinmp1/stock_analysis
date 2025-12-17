#!/usr/bin/env python3
"""
Script to identify stocks missing required data fields in the source data files.
This helps identify why certain stocks don't have financial scores.
"""

import json
import os
import sys
from typing import Dict, List, Optional, Set

# Add project root to path to import financial_scorer
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

try:
    from web_app.financial_scorer import _process_stock, METRICS
    CAN_TEST_METRICS = True
except ImportError:
    CAN_TEST_METRICS = False
    print("Warning: Could not import financial_scorer. Will only check data structure, not actual metric calculation.")

# Required fields for metric calculations
REQUIRED_FIELDS = {
    # Period dates (at least one must exist)
    "period_dates": ["period_end_date", "fiscal_quarter_key", "original_filing_date"],
    
    # Fields used by various metrics
    "operating_income": "operating_income",
    "ppe_net": "ppe_net",
    "revenue": "revenue",
    "cost_of_goods_sold": ["cost_of_goods_sold", "cogs"],  # Either one works
    "net_debt": "net_debt",
}

def get_period_dates(data: Dict) -> Optional[List]:
    """Extract period dates from data dictionary (same logic as financial_scorer)"""
    for date_key in ["period_end_date", "fiscal_quarter_key", "original_filing_date"]:
        if date_key in data and data[date_key]:
            return data[date_key]
    return None

def check_data_completeness(stock_data: Dict) -> Dict[str, any]:
    """
    Check if a stock has the required data fields for metric calculation.
    Returns a dictionary with missing fields and status.
    """
    symbol = stock_data.get("symbol", "UNKNOWN")
    company_name = stock_data.get("company_name", symbol)
    
    result = {
        "symbol": symbol,
        "company_name": company_name,
        "has_data_section": "data" in stock_data,
        "missing_fields": [],
        "has_period_dates": False,
        "data_field_status": {},
        "can_calculate_any_metric": False
    }
    
    # Check if data section exists
    if not result["has_data_section"]:
        result["missing_fields"].append("data section (entire)")
        return result
    
    data = stock_data.get("data", {})
    
    # Check period dates
    period_dates = get_period_dates(data)
    if period_dates and isinstance(period_dates, list) and len(period_dates) > 0:
        result["has_period_dates"] = True
    else:
        result["missing_fields"].append("period_dates (period_end_date, fiscal_quarter_key, or original_filing_date)")
    
    # Check each required field
    field_checks = {
        "operating_income": lambda d: isinstance(d.get("operating_income"), list) and len([x for x in d.get("operating_income", []) if x is not None]) > 0,
        "ppe_net": lambda d: isinstance(d.get("ppe_net"), list) and len([x for x in d.get("ppe_net", []) if x is not None]) > 0,
        "revenue": lambda d: isinstance(d.get("revenue"), list) and len([x for x in d.get("revenue", []) if x is not None]) > 0,
        "cost_of_goods_sold": lambda d: (isinstance(d.get("cost_of_goods_sold"), list) and len([x for x in d.get("cost_of_goods_sold", []) if x is not None]) > 0) or 
                                        (isinstance(d.get("cogs"), list) and len([x for x in d.get("cogs", []) if x is not None]) > 0),
        "net_debt": lambda d: isinstance(d.get("net_debt"), list) and len([x for x in d.get("net_debt", []) if x is not None]) > 0,
    }
    
    for field_name, check_func in field_checks.items():
        has_field = check_func(data)
        result["data_field_status"][field_name] = has_field
        if not has_field:
            result["missing_fields"].append(field_name)
    
    # Determine if any metric can be calculated
    # At minimum, we need period_dates and at least one of: operating_income+ppe_net, revenue, or revenue+cogs
    has_basic_data = (
        result["has_period_dates"] and
        (
            (result["data_field_status"].get("operating_income") and result["data_field_status"].get("ppe_net")) or
            (result["data_field_status"].get("revenue") and result["data_field_status"].get("cost_of_goods_sold")) or
            result["data_field_status"].get("revenue")
        )
    )
    result["can_calculate_any_metric"] = has_basic_data
    
    # If we can import the financial scorer, actually test if metrics can be calculated
    if CAN_TEST_METRICS:
        try:
            # Determine exchange (guess based on filename or default to NASDAQ)
            exchange = stock_data.get("exchange", "NASDAQ")
            processed = _process_stock(stock_data, exchange)
            result["actually_can_calculate"] = processed is not None
            if processed is None:
                result["missing_fields"].append("(actual metric calculation failed)")
        except Exception as e:
            result["actually_can_calculate"] = False
            result["calculation_error"] = str(e)
    
    return result

def analyze_data_file(filename: str) -> List[Dict]:
    """Analyze a JSONL file and return stocks with missing data"""
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found")
        return []
    
    missing_data_stocks = []
    total_stocks = 0
    
    print(f"\nAnalyzing {filename}...")
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                stock_data = json.loads(line)
                total_stocks += 1
                
                result = check_data_completeness(stock_data)
                
                # Include stocks that are missing data or can't calculate any metrics
                # If we tested actual calculation, use that; otherwise use the structure check
                if CAN_TEST_METRICS and "actually_can_calculate" in result:
                    if not result.get("actually_can_calculate", False):
                        missing_data_stocks.append(result)
                elif not result["can_calculate_any_metric"]:
                    missing_data_stocks.append(result)
                    
            except json.JSONDecodeError as e:
                print(f"  Warning: Skipping invalid JSON on line {line_num}: {e}")
                continue
            except Exception as e:
                print(f"  Warning: Error processing line {line_num}: {e}")
                continue
    
    print(f"  Total stocks: {total_stocks}")
    print(f"  Stocks with missing/incomplete data: {len(missing_data_stocks)}")
    
    return missing_data_stocks

def main():
    """Main function to check both data files"""
    print("=" * 80)
    print("Checking for stocks with missing data fields")
    print("=" * 80)
    
    # Determine project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "quantitative_stock_scorer", "data")
    
    nyse_file = os.path.join(data_dir, "nyse_data.jsonl")
    nasdaq_file = os.path.join(data_dir, "nasdaq_data.jsonl")
    
    # Analyze both files
    nyse_missing = analyze_data_file(nyse_file)
    nasdaq_missing = analyze_data_file(nasdaq_file)
    
    all_missing = nyse_missing + nasdaq_missing
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total stocks with missing/incomplete data: {len(all_missing)}")
    
    if all_missing:
        # Group by issue type
        no_data_section = [s for s in all_missing if not s["has_data_section"]]
        no_period_dates = [s for s in all_missing if s["has_data_section"] and not s["has_period_dates"]]
        missing_specific_fields = [s for s in all_missing if s["has_data_section"] and s["has_period_dates"]]
        
        print(f"\nBreakdown:")
        print(f"  - Missing entire 'data' section: {len(no_data_section)}")
        print(f"  - Missing period dates: {len(no_period_dates)}")
        print(f"  - Has data section but missing specific fields: {len(missing_specific_fields)}")
        
        # Print detailed list
        print("\n" + "=" * 80)
        print("DETAILED LIST OF STOCKS WITH MISSING DATA")
        print("=" * 80)
        
        # Sort by symbol
        all_missing.sort(key=lambda x: x["symbol"])
        
        for stock in all_missing:
            print(f"\n{stock['symbol']} - {stock['company_name']}")
            print(f"  Missing: {', '.join(stock['missing_fields']) if stock['missing_fields'] else 'None (but cannot calculate metrics)'}")
            print(f"  Has data section: {stock['has_data_section']}")
            if stock['has_data_section']:
                print(f"  Has period dates: {stock['has_period_dates']}")
                if CAN_TEST_METRICS and "actually_can_calculate" in stock:
                    print(f"  Actually can calculate metrics: {stock.get('actually_can_calculate', False)}")
                    if "calculation_error" in stock:
                        print(f"  Calculation error: {stock['calculation_error']}")
                print(f"  Field status:")
                for field, status in stock['data_field_status'].items():
                    status_str = "[OK]" if status else "[MISSING]"
                    print(f"    {status_str} {field}")
        
        # Save to file
        output_file = os.path.join(script_dir, "missing_data_stocks.json")
        with open(output_file, 'w') as f:
            json.dump(all_missing, f, indent=2)
        print(f"\n" + "=" * 80)
        print(f"Detailed results saved to: {output_file}")
    else:
        print("\nAll stocks have complete data!")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
