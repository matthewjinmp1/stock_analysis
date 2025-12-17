#!/usr/bin/env python3
"""
YFinance Revenue Growth Analyzer
Fetches future revenue growth analyst estimates for stocks using yfinance API.
"""

import yfinance as yf
import json
from typing import Dict, Optional, Tuple
import os
import sys

# Ensure project root is on path so we can import modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def calculate_past_5_year_revenue_growth(ticker_obj) -> Optional[float]:
    """
    Calculate the past 5-year revenue growth rate from financial statements.

    Args:
        ticker_obj: yfinance Ticker object

    Returns:
        Average annual revenue growth rate over past 5 years (as percentage), or None if unavailable
    """
    try:
        # Get income statement data
        income_stmt = ticker_obj.financials  # Annual financials

        if income_stmt is None or income_stmt.empty:
            return None

        # Look for total revenue row
        revenue_row = None
        possible_revenue_labels = ['Total Revenue', 'Revenue', 'Sales', 'Net Sales']

        for label in possible_revenue_labels:
            if label in income_stmt.index:
                revenue_row = income_stmt.loc[label]
                break

        if revenue_row is None or len(revenue_row) < 5:
            return None

        # Get the last 5 years of revenue data (most recent first)
        revenues = []
        for i in range(min(5, len(revenue_row))):
            rev = revenue_row.iloc[i]
            if rev is not None and not str(rev).lower() in ['nan', 'none', '']:
                revenues.append(float(rev))

        if len(revenues) < 2:
            return None

        # Calculate compound annual growth rate (CAGR)
        # CAGR = (Ending Value / Beginning Value)^(1/Number of Periods) - 1
        beginning_value = revenues[-1]  # Oldest value
        ending_value = revenues[0]     # Most recent value
        num_years = len(revenues) - 1

        if beginning_value > 0 and ending_value > 0:
            cagr = (ending_value / beginning_value) ** (1 / num_years) - 1
            return cagr * 100  # Convert to percentage

        return None

    except Exception as e:
        print(f"Error calculating past 5-year growth: {e}")
        return None


def get_revenue_growth_estimates(ticker: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Get revenue growth analyst estimates for a given ticker.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

    Returns:
        tuple: (data_dict, error_message)
            - data_dict: Dictionary containing revenue growth estimates or None
            - error_message: Error message string or None if successful

    The returned data includes:
    - current_year_growth: Current year revenue growth estimate (%)
    - next_year_growth: Next year revenue growth estimate (%)
    - next_5_years_growth: Next 5 years revenue growth estimate (%)
    - past_5_year_growth: Past 5 year actual revenue growth (%)
    - company_name: Company name from yfinance
    - analyst_count: Number of analysts providing estimates
    """
    try:
        # Create ticker object
        ticker_obj = yf.Ticker(ticker.upper())

        # Get growth estimates
        growth_estimates = ticker_obj.growth_estimates

        if growth_estimates is None or growth_estimates.empty:
            return None, "No growth estimates available for this ticker"

        # Get revenue estimate details
        revenue_estimate = ticker_obj.revenue_estimate

        # Get company info
        info = ticker_obj.info
        company_name = info.get('longName', ticker.upper())

        # Extract revenue growth data
        data = {
            'ticker': ticker.upper(),
            'company_name': company_name,
            'current_year_growth': None,
            'next_year_growth': None,
            'next_5_years_growth': None,
            'past_5_year_growth': None,
            'analyst_count': None,
            'source': 'yfinance'
        }

        # Extract data from revenue_estimate dataframe which contains the actual revenue growth estimates
        if revenue_estimate is not None and hasattr(revenue_estimate, 'loc'):
            try:
                # Get current year revenue growth estimate (0y row, growth column)
                if '0y' in revenue_estimate.index:
                    current_year_growth = revenue_estimate.loc['0y', 'growth']
                    if current_year_growth is not None and not str(current_year_growth).lower() in ['nan', 'none', '']:
                        data['current_year_growth'] = float(current_year_growth) * 100  # Convert to percentage
            except (KeyError, ValueError, TypeError):
                pass

            try:
                # Get next year revenue growth estimate (+1y row, growth column)
                if '+1y' in revenue_estimate.index:
                    next_year_growth = revenue_estimate.loc['+1y', 'growth']
                    if next_year_growth is not None and not str(next_year_growth).lower() in ['nan', 'none', '']:
                        data['next_year_growth'] = float(next_year_growth) * 100  # Convert to percentage
            except (KeyError, ValueError, TypeError):
                pass

            try:
                # For long-term growth, check if 'LTG' exists in growth_estimates
                if hasattr(growth_estimates, 'loc') and 'LTG' in growth_estimates.index:
                    ltg_growth = growth_estimates.loc['LTG', 'stockTrend']
                    if ltg_growth is not None and not str(ltg_growth).lower() in ['nan', 'none', '']:
                        data['next_5_years_growth'] = float(ltg_growth) * 100  # Convert to percentage
            except (KeyError, ValueError, TypeError):
                pass


        # Try to get analyst count from revenue_estimate or info
        if revenue_estimate is not None:
            try:
                analyst_count = revenue_estimate.get('numberOfAnalystOpinions')
                if analyst_count is not None:
                    data['analyst_count'] = int(analyst_count)
            except (ValueError, TypeError):
                pass

        # Alternative: try to get analyst count from the info dict
        if data['analyst_count'] is None and info:
            try:
                analyst_count = info.get('numberOfAnalystOpinions')
                if analyst_count is not None:
                    data['analyst_count'] = int(analyst_count)
            except (ValueError, TypeError):
                pass

        # If we don't have past 5-year growth, try to calculate it from financial statements
        if data['past_5_year_growth'] is None:
            try:
                past_growth = calculate_past_5_year_revenue_growth(ticker_obj)
                if past_growth is not None:
                    data['past_5_year_growth'] = past_growth
            except Exception as e:
                print(f"Warning: Could not calculate past 5-year growth: {e}")

        # If we got at least one growth estimate, return the data
        if any([data['current_year_growth'], data['next_year_growth'], data['next_5_years_growth'], data['past_5_year_growth']]):
            return data, None
        else:
            return None, "No revenue growth estimates found in the data"

    except Exception as e:
        error_msg = f"Error fetching revenue growth data for {ticker}: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return None, error_msg


def format_growth_data(data: Dict) -> str:
    """
    Format revenue growth data into a readable string.

    Args:
        data: Dictionary containing revenue growth estimates

    Returns:
        Formatted string with growth estimates
    """
    lines = []
    lines.append(f"Revenue Growth Estimates for {data['company_name']} ({data['ticker']})")
    lines.append("=" * 60)

    if data.get('past_5_year_growth') is not None:
        lines.append(f"Past 5 Year Growth:     {data['past_5_year_growth']:.1f}%")

    if data.get('current_year_growth') is not None:
        lines.append(f"Current Year Growth:    {data['current_year_growth']:.1f}%")

    if data.get('next_year_growth') is not None:
        lines.append(f"Next Year Growth:       {data['next_year_growth']:.1f}%")

    if data.get('next_5_years_growth') is not None:
        lines.append(f"Next 5 Years Growth:    {data['next_5_years_growth']:.1f}%")

    if data.get('analyst_count') is not None:
        lines.append(f"Number of Analysts:     {data['analyst_count']}")

    lines.append(f"Data Source:            {data['source']}")

    return "\n".join(lines)


def main():
    """Interactive command line interface for revenue growth estimates."""
    print("=" * 60)
    print("YFinance Revenue Growth Analyzer")
    print("=" * 60)
    print("Enter stock tickers to get revenue growth estimates.")
    print("Type 'quit', 'exit', or 'q' to exit the program.")
    print("-" * 60)

    while True:
        try:
            # Get user input
            ticker_input = input("\nEnter ticker symbol: ").strip()

            # Check for exit commands
            if ticker_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            # Validate input
            if not ticker_input:
                print("Please enter a ticker symbol.")
                continue

            # Convert to uppercase
            ticker = ticker_input.upper()

            print(f"\nFetching revenue growth estimates for {ticker}...")
            print("-" * 40)

            # Get data
            data, error = get_revenue_growth_estimates(ticker)

            if error:
                print(f"Error: {error}")
                continue

            if data:
                print(format_growth_data(data))
            else:
                print("No revenue growth data found for this ticker.")

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            continue


if __name__ == '__main__':
    main()