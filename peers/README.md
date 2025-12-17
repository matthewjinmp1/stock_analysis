# AI Peer Finder

This folder contains tools for finding comparable companies (peers) using AI analysis.

## Files

- `test_peer_finder.py` - Interactive command-line tool for testing peer finding
- `README.md` - This documentation file

## Usage

### Running the Test Script

```bash
cd peers
python test_peer_finder.py
```

The script will prompt you to enter ticker symbols. For each ticker, it will:
1. Look up the company name
2. Query AI to find 10 comparable companies
3. Display the results with timing and cost information
4. Ask if you want to save the results to a JSON file

### Example Session

```
AI Peer Finder Test
==================================================
AI modules imported successfully

==================================================
Enter ticker symbol (or 'quit' to exit): AAPL

Testing peer finding for: AAPL
Fetching company data...
Found company: Apple Inc.
Finding peers for: AAPL (Apple Inc.)
Querying AI for peer recommendations...
AI query completed in 32.45 seconds
Estimated cost: 0.2633 cents
Token usage: {'prompt_tokens': 456, 'completion_tokens': 2560, 'total_tokens': 3016, 'thinking_tokens': 2523, 'output_tokens': 2560}

AI-Generated Peer Recommendations:
----------------------------------------
 1. Samsung Electronics Co., Ltd.
 2. Alphabet Inc.
 3. Microsoft Corporation
 4. Amazon.com, Inc.
 5. Sony Group Corporation
 6. Dell Technologies Inc.
 7. HP Inc.
 8. Lenovo Group Limited
 9. Meta Platforms, Inc.
10. Qualcomm Incorporated

Total peers found: 10
Test completed successfully!

Save results to JSON file? (y/n): y

Results saved to: peers_AAPL_20241220_143052.json
```

## JSON Output Format

When you choose to save results, they are stored as JSON files with timestamps:

```json
{
  "timestamp": "2024-12-20T14:30:52.123456",
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "peers": [
    "Samsung Electronics Co., Ltd.",
    "Alphabet Inc.",
    "Microsoft Corporation",
    "Amazon.com, Inc.",
    "Sony Group Corporation",
    "Dell Technologies Inc.",
    "HP Inc.",
    "Lenovo Group Limited",
    "Meta Platforms, Inc.",
    "Qualcomm Incorporated"
  ],
  "peer_count": 10,
  "token_usage": {
    "prompt_tokens": 456,
    "completion_tokens": 2560,
    "total_tokens": 3016,
    "thinking_tokens": 2523,
    "output_tokens": 2560
  },
  "estimated_cost_cents": 0.2633
}
```

## Cost Information

- **Input tokens**: 456 tokens @ $0.20 per million = ~0.009 cents
- **Output tokens**: 2560 tokens @ $0.50 per million = ~0.128 cents
- **Thinking tokens**: 2523 tokens @ $0.50 per million = ~0.126 cents
- **Total cost**: ~0.263 cents per query

## Requirements

- Valid XAI API key in config
- Access to company data cache
- Python dependencies installed

## File Naming

Saved JSON files follow this pattern:
```
peers_{TICKER}_{YYYYMMDD_HHMMSS}.json
```

Example: `peers_AAPL_20241220_143052.json`