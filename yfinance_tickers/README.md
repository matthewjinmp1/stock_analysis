# YFinance Ticker Collection

This folder contains scripts for collecting and validating stock tickers using the `yfinance` Python library.

## Important Note

**YFinance does NOT provide a method to get "all available tickers"** from global markets. It requires you to know ticker symbols beforehand. This collection demonstrates:

- How to validate known tickers using yfinance
- How to collect tickers from major indices (S&P 500, NASDAQ 100)
- How to extract company information for validated tickers

## Files

### Scripts
- `yfinance_ticker_collector.py` - Main script to collect and validate tickers
- `yfinance_db_manager.py` - Database manager for querying collected tickers

### Data
- `yfinance_tickers.db` - SQLite database with validated tickers and company info

## Usage

### Collect Tickers from Popular Stocks
```bash
python yfinance_ticker_collector.py --source popular
```

### Collect from S&P 500 Sample
```bash
python yfinance_ticker_collector.py --source sp500
```

### Collect from NASDAQ 100 Sample
```bash
python yfinance_ticker_collector.py --source nasdaq100
```

### Limit Number of Tickers
```bash
python yfinance_ticker_collector.py --source popular --limit 10
```

### Query the Database
```bash
python yfinance_db_manager.py stats
python yfinance_db_manager.py search --query APPLE
python yfinance_db_manager.py sample --limit 20
```

## Database Schema

```sql
CREATE TABLE tickers (
    ticker TEXT PRIMARY KEY,
    company_name TEXT,
    sector TEXT,
    industry TEXT,
    country TEXT DEFAULT 'US',
    source TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_valid BOOLEAN DEFAULT 1
);

CREATE TABLE ticker_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT UNIQUE,
    description TEXT,
    ticker_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Limitations

1. **No Complete Ticker List**: YFinance doesn't provide access to all available global tickers
2. **Manual Ticker Lists**: Requires predefined lists of tickers to validate
3. **Rate Limiting**: Subject to Yahoo Finance's rate limits
4. **US-Focused**: Primarily works with US-listed stocks

## Alternatives for Complete Ticker Lists

For comprehensive ticker collections, consider:
- **QuickFS API**: `get_supported_companies()` method (what we used in `quickfs_tickers/`)
- **Manual Sources**: Wikipedia, SEC filings, exchange websites
- **Commercial Data Providers**: Bloomberg, Refinitiv, etc.

## Integration with QuickFS

This YFinance collection can complement the QuickFS collection:
- Use QuickFS for comprehensive ticker discovery
- Use YFinance for company information validation
- Cross-reference data between sources

## Dependencies

```bash
pip install yfinance
```

The database uses standard SQLite, no additional dependencies required.