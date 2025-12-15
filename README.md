# Stock Analysis Suite

A comprehensive stock analysis toolkit that combines AI-powered competitive moat analysis with quantitative financial metrics evaluation and backtesting capabilities.

## Overview

This project merges two complementary approaches to stock analysis:

1. **AI-Powered Competitive Moat Analysis** - Uses xAI's Grok LLM to evaluate companies across multiple competitive advantage dimensions
2. **Quantitative Financial Analysis** - Analyzes stocks based on financial metrics, correlations, and forward returns with backtesting

## Features

### AI-Powered Analysis
- **Competitive Moat Scoring**: Evaluates companies across 20+ dimensions including:
  - Competitive Moat, Barriers to Entry, Disruption Risk
  - Switching Cost, Brand Strength, Competition Intensity
  - Network Effect, Product Differentiation, Innovativeness
  - Growth Opportunity, Riskiness, Pricing Power
  - And more...
- **Persistent Storage**: Saves all scores to avoid redundant API calls
- **Interactive Mode**: Enter company names to get instant moat analysis
- **Credit Management**: Built-in tools to check API credit availability

### Quantitative Analysis
- **Financial Metrics**: Calculate and analyze various financial ratios and metrics
- **Correlation Analysis**: Find relationships between metrics and forward returns
- **Backtesting**: Test investment strategies with historical data
- **Data Collection**: Automated collection of stock data from NYSE, NASDAQ, and S&P 500
- **Glassdoor Integration**: Analyze company culture data from Glassdoor Best Places to Work

## Project Structure

```
stock_analysis/
├── src/
│   ├── analysis/           # Analysis and correlation scripts
│   ├── backtesting/        # Backtesting scripts
│   ├── clients/            # API clients (Grok, OpenRouter)
│   ├── data_collection/    # Scripts for fetching stock data
│   ├── scoring/            # AI-powered scoring modules
│   ├── scrapers/           # Web scraping scripts
│   └── utils/              # Utility and debug scripts
├── data/                   # Data files (JSON, JSONL, TXT)
├── glassdoor/              # Glassdoor analysis scripts and data
├── company_keywords/       # Company keyword generation and evaluation
├── tests/                  # Test files
├── backtest_results/       # Backtest visualization results
├── rebalancing_backtest_results/  # Rebalancing backtest results
├── config.py              # Configuration file (API keys, etc.)
├── config.example.py      # Example configuration
├── requirements.txt       # Python dependencies
└── run_scorer.py         # Main entry point for AI scorer
```

## Prerequisites

- Python 3.7 or higher
- API keys for:
  - xAI Grok API (get one from [https://console.x.ai/](https://console.x.ai/))
  - OpenRouter API (optional, for alternative AI models)
  - QuickFS API (for financial data)
  - SerpAPI (optional, for Google Search)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd stock_analysis
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy the config template and add your API keys:
```bash
cp config.example.py config.py
```

4. Edit `config.py` and add your API keys:
```python
XAI_API_KEY = "your_xai_api_key_here"
OPENROUTER_KEY = "your_openrouter_key_here"
QUICKFS_API_KEY = "your_quickfs_api_key_here"
SERP_API_KEY = "your_serp_api_key_here"
```

**Note**: `config.py` is in `.gitignore` to protect your API keys.

## Usage

### AI-Powered Competitive Moat Scorer

Run the main scoring application:

```bash
python run_scorer.py
```

Then enter ticker symbols or company names when prompted. The tool will:
- Check if the company has been scored before
- Query Grok for missing scores
- Display all metrics (0-10 scale)
- Save scores to `data/scores.json`

**Example interaction:**
```
Enter ticker or company name (or 'view'/'fill'/'quit'): TSLA
Analyzing TSLA...
Querying Competitive Moat...
Competitive Moat Score: 8/10
...
```

### Quantitative Analysis

#### Data Collection

1. **Get stock lists:**
   ```bash
   python src/data_collection/get_nasdaq_stocks.py
   python src/data_collection/get_nyse_stocks.py
   ```

2. **Fetch stock data:**
   ```bash
   python src/data_collection/get_data.py
   ```

3. **Calculate metrics:**
   ```bash
   python src/data_collection/get_metrics.py
   ```

#### Analysis

```bash
python src/analysis/correlations.py
python src/analysis/scorer.py calc              # Calculate scores for all stocks
python src/analysis/scorer.py AAPL              # Look up percentile for AAPL
python src/analysis/scorer.py view 50           # View top 50 stocks
python src/analysis/scorer.py view 50 over 10   # View top 50 with market cap > $10B
```

#### Backtesting

```bash
python src/backtesting/backtester.py
python src/backtesting/rebalancing_backtester.py
```

#### Glassdoor Analysis

```bash
# Scrape Glassdoor Best Places to Work list for a specific year (2009-2025)
python glassdoor/scrape_glassdoor.py 2009
python glassdoor/scrape_glassdoor.py 2015
python glassdoor/scrape_glassdoor.py 2020
```

### Utility Scripts

```bash
# Check QuickFS API credits
python src/utils/check_credits.py

# Check xAI/Grok API credits (from AI scorer)
python src/utils/check_credits.py
```

### Running Tests

```bash
python tests/run_tests.py
python tests/run_coverage.py
```

## Competitive Moat Scoring Details

### What are Competitive Moats?

A competitive moat refers to a company's sustainable competitive advantages that protect it from competitors. This tool evaluates:

1. **Competitive Moat** - Overall strength across all dimensions
2. **Barriers to Entry** - Regulatory, capital, or technological hurdles
3. **Disruption Risk** - Vulnerability to new technologies or business models
4. **Switching Cost** - Lock-in effects (vendor switching, retraining, data migration)
5. **Brand Strength** - Customer loyalty, recognition, and pricing power
6. **Competition Intensity** - Market competition level and aggressiveness
7. **Network Effect** - Platform, marketplace, or ecosystem benefits
8. **Product Differentiation** - Product uniqueness vs commoditization
9. And many more dimensions...

### Interpreting Scores

- **0-3**: Weak competitive position
- **4-6**: Moderate competitive position
- **7-8**: Strong competitive position
- **9-10**: Exceptional competitive position (rare)

## Quantitative Metrics

The quantitative scorer evaluates stocks based on various financial metrics including:
- EBIT/PPE (Operating Income / Property, Plant & Equipment)
- Operating Margin
- Gross Margin
- 5-Year Revenue CAGR
- EV/EBIT (Enterprise Value / EBIT)
- ROA (Return on Assets)
- Price-to-Book Ratio
- And many more...

Each metric is calculated as a percentile rank relative to all stocks in the dataset.

## API Usage & Costs

This tool uses multiple APIs:
- **xAI Grok API**: For AI-powered competitive moat analysis
- **QuickFS API**: For financial data collection
- **OpenRouter API**: Alternative AI model access
- **SerpAPI**: For web search capabilities

Each company analysis requires multiple API calls, so:
- Use credit checking scripts to monitor availability
- Consider costs when analyzing many companies
- Scores are cached to avoid duplicate API calls

## Troubleshooting

### "API key is required" error
1. Check that `config.py` exists
2. Verify your API keys are set correctly
3. Ensure you have API credits available

### Company scores not updating
- Try deleting the company entry from `data/scores.json`
- Or manually edit the JSON to remove specific score fields

### API Rate Limiting
- Wait between queries if you hit rate limits
- The tool uses `grok-4-fast` for speed and cost efficiency

### Import Errors
- Make sure you're running scripts from the project root directory
- Check that all dependencies are installed: `pip install -r requirements.txt`

## Contributing

Contributions welcome! Areas for improvement:
- Additional scoring dimensions
- Historical score tracking
- Batch analysis of multiple companies
- Export to CSV/Excel
- Web interface
- Additional financial metrics
- Enhanced backtesting capabilities

## License

MIT License - See LICENSE file for details.

## Support

For issues or questions:
- Open an issue on GitHub
- For xAI API issues, see [xAI documentation](https://docs.x.ai/)
- For QuickFS API issues, see [QuickFS documentation](https://quickfs.net/)

