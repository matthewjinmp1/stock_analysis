# QuickFS Tickers Collection

This folder contains scripts and data for collecting all available stock tickers from the QuickFS API.

## Files

### Scripts
- `get_all_quickfs_tickers.py` - Main script to fetch all tickers from supported exchanges
- `test_quickfs_companies.py` - Test script to examine the raw output from QuickFS API

### Data Files
- `quickfs_all_tickers.json` - Complete list of 11,970+ tickers from all supported exchanges
- `quickfs_companies_raw.json` - Raw output from get_supported_companies for NYSE (3,591 tickers)
- `quickfs_companies_sample.json` - Sample of first 10 tickers from NYSE to show data format

## Key Findings

1. **QuickFS API Structure**: The `get_supported_companies()` method returns simple ticker strings in format "TICKER:COUNTRY" (e.g., "AAPL:US")

2. **No Company Names**: The ticker list API does not include company names - these must be fetched separately using `get_data_full()` for individual tickers

3. **Supported Exchanges**: Successfully collected tickers from:
   - NYSE: 3,591 tickers
   - NASDAQ: 5,904 tickers
   - ASX (Australia): 3,405 tickers
   - NZX (New Zealand): 167 tickers
   - Total: 11,970 unique tickers

4. **Known Issues**: Some exchanges (CA/TSX, LN/LSE, MM/YSX) fail due to a bug in the QuickFS Python library where it expects dictionary responses but receives lists. Direct API calls also timeout, suggesting these exchanges may not be fully supported or have different API endpoints.

5. **Coverage**: The working exchanges cover the major US and international markets. The missing exchanges (Canada, UK, Myanmar) represent a small portion of global market capitalization.

## Usage

Run the main script:
```bash
python get_all_quickfs_tickers.py
```

For verbose output:
```bash
python get_all_quickfs_tickers.py --verbose
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