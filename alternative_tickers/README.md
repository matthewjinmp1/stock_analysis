# Alternative Ticker Sources

This folder contains scripts for collecting stock tickers from various alternative sources beyond QuickFS and yfinance.

## Sources Included

### 📰 **Wikipedia-Based Collections**
- **S&P 500**: All 500+ companies from the S&P 500 index
- **NASDAQ 100**: Technology-heavy index constituents
- **Russell 2000**: Small-cap sample (full list requires paid service)

### 🌐 **API-Based Sources**
- **EOD Historical Data**: Free tier samples
- **Finnhub**: Free API (requires API key setup)

### 📊 **Data Structure**
Each ticker includes:
- Ticker symbol
- Company name
- Source identifier
- Source URL
- Collection timestamp

## Usage

### Collect from All Sources
```bash
python ticker_collector.py --source all
```

### Collect from Specific Sources
```bash
# S&P 500 companies
python ticker_collector.py --source sp500

# NASDAQ 100 companies
python ticker_collector.py --source nasdaq100

# Russell 2000 sample
python ticker_collector.py --source russell2000
```

### Query the Database
```bash
# Database statistics
python db_manager.py stats

# Show sample tickers
python db_manager.py sample --limit 20

# Search for companies
python db_manager.py search --query "Apple"

# Export to JSON
python db_manager.py export --output tickers.json
```

## Database Schema

```sql
CREATE TABLE tickers (
    ticker TEXT PRIMARY KEY,
    company_name TEXT,
    source TEXT,
    source_url TEXT,
    collected_date TIMESTAMP,
    is_valid BOOLEAN DEFAULT 1
);

CREATE TABLE sources (
    source_name TEXT UNIQUE,
    description TEXT,
    url TEXT,
    ticker_count INTEGER,
    last_updated TIMESTAMP
);
```

## Comparison with Other Systems

| Feature | Alternative Tickers | QuickFS | YFinance |
|---------|-------------------|---------|----------|
| **Cost** | Free | Credits required | Free |
| **Coverage** | Major indices | 17,278+ global | Manual lists only |
| **Company Names** | Included | API call required | API provides |
| **Update Frequency** | Manual | Real-time | Real-time |
| **Geographic Focus** | US indices | Global | Global |

## Advantages

1. **Zero Cost**: No API credits or subscriptions required
2. **Reliable Sources**: Wikipedia and official index data
3. **Index Coverage**: Complete major US market indices
4. **Company Names**: Included at collection time
5. **Extensible**: Easy to add new sources

## Limitations

1. **US-Focused**: Primarily covers US-listed companies
2. **Manual Updates**: Requires running scripts to refresh data
3. **Limited Coverage**: Only major indices, not comprehensive global coverage
4. **No Financial Data**: Only provides tickers and company names

## Integration

This system complements the QuickFS and YFinance systems:

- **QuickFS**: Comprehensive global coverage (but costs credits)
- **YFinance**: Real-time validation and metadata
- **Alternative Tickers**: Free index-based collections

Use this for cost-free ticker discovery, then validate/enrich with the other systems as needed.

## Dependencies

```bash
pip install requests beautifulsoup4
```

The database uses standard SQLite, no additional dependencies required.