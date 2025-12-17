# QuickFS Tickers Collection

This folder contains scripts and data for collecting all available stock tickers from the QuickFS API.

## Files

### Scripts
- `get_all_quickfs_tickers.py` - Main script to fetch all tickers from supported exchanges
- `get_all_tickers_improved.py` - Improved version with fallback to direct API calls
- `create_quickfs_tickers_db.py` - Creates SQLite database from collected tickers
- `quickfs_tickers_db.py` - Database manager for querying tickers
- `test_quickfs_companies.py` - Test script to examine the raw output from QuickFS API

### Data Files
- `quickfs_all_tickers.json` - Complete list of 11,970+ tickers from initial exchanges
- `remaining_exchanges_tickers.json` - Additional 7,941 tickers from remaining exchanges
- `quickfs_companies_raw.json` - Raw output from get_supported_companies for NYSE (3,591 tickers)
- `quickfs_companies_sample.json` - Sample of first 10 tickers from NYSE to show data format

### Database
- `quickfs_tickers.db` - SQLite database with all 17,278 QuickFS tickers

## Key Findings

1. **QuickFS API Structure**: The `get_supported_companies()` method returns simple ticker strings in format "TICKER:COUNTRY" (e.g., "AAPL:US")

2. **No Company Names**: The ticker list API does not include company names - these must be fetched separately using `get_data_full()` for individual tickers

3. **Supported Exchanges**: Successfully collected tickers from:
   - NYSE: 3,591 tickers
   - NASDAQ: 5,904 tickers
   - ASX (Australia): 3,405 tickers
   - NZX (New Zealand): 167 tickers
   - **Additional exchanges**: TORONTO (1,367), TSXVENTURE (3,013), CSE (1,092), LONDON (2,551), BMV (124), NYSEARCA (7), BATS (2), NYSEAMERICAN (455)
   - **Total**: 17,278 unique tickers in database

4. **Known Issues**: Some exchanges (CA/TSX, LN/LSE, MM/YSX) fail due to a bug in the QuickFS Python library where it expects dictionary responses but receives lists. Direct API calls also timeout, suggesting these exchanges may not be fully supported or have different API endpoints.

5. **Coverage**: The working exchanges cover the major US and international markets. The missing exchanges (Canada, UK, Myanmar) represent a small portion of global market capitalization.

## Usage

### Collecting Tickers
Run the main script:
```bash
python get_all_quickfs_tickers.py
```

For verbose output:
```bash
python get_all_quickfs_tickers.py --verbose
```

### Database Management
Create/update the database:
```bash
python create_quickfs_tickers_db.py
```

Query the database:
```bash
# Show statistics
python quickfs_tickers_db.py stats

# Show sample tickers
python quickfs_tickers_db.py sample --limit 20

# Search for tickers
python quickfs_tickers_db.py search --query AAPL

# Export to JSON
python quickfs_tickers_db.py export --output export.json
```

### Database Schema
```sql
CREATE TABLE tickers (
    ticker TEXT PRIMARY KEY,
    company_name TEXT,  -- NULL for QuickFS (names not provided)
    source TEXT DEFAULT 'quickfs'
);

-- Indexes for performance
CREATE INDEX idx_ticker ON tickers(ticker);
CREATE INDEX idx_source ON tickers(source);
```

## API Key Required

Requires QuickFS API key in `config.py` or `QUICKFS_API_KEY` environment variable.

## Related Files in Project

The project uses these tickers with company names from other sources:
- `ticker_definitions.json` - Manual company name mappings
- `tickers.db` - SQLite database with ticker-company mappings
- `src/scrapers/glassdoor_scraper.py` - Functions to lookup company names from tickers</contents>
</xai:function_call"Write">
<parameter name="path">c:\Users\matth\stock_analysis\quickfs_tickers\README.md