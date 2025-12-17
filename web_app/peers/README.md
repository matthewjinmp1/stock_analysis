# AI Peer Finder & Results Database

This folder contains tools for finding comparable companies (peers) using AI analysis and storing the results in a database.

## Files

- `test_peer_finder.py` - Interactive command-line tool for testing peer finding
- `peers_results_db.py` - Database functions for storing peer analysis results
- `peers_results.db` - SQLite database containing all peer analysis results
- `README.md` - This documentation file

## Features

### AI Peer Finding
- Uses Grok-4-1-fast-reasoning model for peer analysis
- Analyzes industry, business model, products, and market overlap
- Returns 10 most comparable companies ranked by similarity

### Database Storage
- **SQLite Database**: Structured storage for querying and analysis

### Cost Tracking
- Token usage monitoring (prompt, completion, thinking tokens)
- Cost calculation in cents
- Performance metrics (response time)

## Database Schema

The `peers_results.db` contains a `peer_results` table with **one peer per row** for better performance:

```sql
CREATE TABLE peer_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    company_name TEXT,
    peer_name TEXT NOT NULL,        -- Individual peer company name
    peer_rank INTEGER NOT NULL,     -- Position in peer list (1-10)
    token_usage_json TEXT,          -- JSON object with token usage details
    estimated_cost_cents REAL,      -- Cost per analysis (duplicated across peers)
    analysis_timestamp TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, peer_name, analysis_timestamp)
);
```

### Indexes
- `idx_peer_results_ticker` - Fast ticker lookups
- `idx_peer_results_timestamp` - Time-based queries
- `idx_peer_results_peer_name` - Peer frequency analysis
- `idx_peer_results_rank` - Rank-based filtering

## Usage

### Running the Test Script

```bash
cd web_app/peers
python test_peer_finder.py

### Database Management

Initialize/update the database:
```bash
python peers_results_db.py
```

Migrate from old JSON schema (if upgrading):
```bash
python peers_results_db.py --migrate
```
```

The script will prompt you to enter ticker symbols. For each ticker, it will:
1. Look up the company name from cached data
2. Query AI to find 10 comparable companies
3. Display results with timing and cost information
4. Ask if you want to save to the database

### Example Session

```
AI Peer Finder Test
==================================================
Results will be saved as JSON files and to the database in the peers folder.
AI modules imported successfully

==================================================
Enter ticker symbol (or 'quit' to exit): AAPL

Testing peer finding for: AAPL
Fetching company data...
Found company: Apple Inc.
Finding peers for: AAPL (Apple Inc.)
Querying AI for peer recommendations...
AI query completed in 28.45 seconds
Estimated cost: 0.2633 cents
Token usage: {'prompt_tokens': 456, 'completion_tokens': 2560, 'total_tokens': 3016, 'thinking_tokens': 2523, 'output_tokens': 2560}

AI-Generated Peer Recommendations:
----------------------------------------
 1. Samsung Electronics Co., Ltd.
 2. Alphabet Inc.
 3. Microsoft Corporation
 4. Amazon.com, Inc.
 5. Meta Platforms, Inc.
 6. Sony Group Corporation
 7. NVIDIA Corporation
 8. Dell Technologies Inc.
 9. HP Inc.
10. Lenovo Group Limited

Total peers found: 10
Test completed successfully!

Save results to database? (y/n): y

Results saved to database successfully!
```

## Database Queries

### Get analysis history for a ticker:
```python
from peers_results_db import get_peer_analysis
results = get_peer_analysis("AAPL", limit=5)
for result in results:
    print(f"{result['ticker']}: {result['peer_count']} peers, ${result['estimated_cost_cents']:.4f} cents")
    print(f"Top peers: {', '.join(result['peers'][:3])}")
```

### Advanced Queries with New Schema:

```python
# Find most common peers across all analyses
from peers_results_db import get_all_peer_analyses
import collections

all_results = get_all_peer_analyses(limit=1000)
peer_counts = collections.Counter()
for result in all_results:
    peer_counts.update(result['peers'])

print("Most common peers:")
for peer, count in peer_counts.most_common(10):
    print(f"{peer}: {count} appearances")
```

### Get database statistics:
```python
from peers_results_db import get_peer_analysis_stats
stats = get_peer_analysis_stats()
print(f"Total analyses: {stats['total_analyses']}")
print(f"Total peer relationships: {stats['total_peer_relationships']}")
print(f"Total cost: ${stats['total_cost_dollars']:.4f}")
```

## File Naming

### Database Records
- Primary key: auto-incrementing ID
- Unique constraint: (ticker, analysis_timestamp)
- Allows multiple analyses per ticker over time


## Cost Information

- **Input tokens**: $0.20 per million
- **Output tokens**: $0.50 per million (includes thinking tokens)
- **Typical cost**: ~0.25-0.30 cents per analysis
- **Token breakdown**: ~25% input, ~75% output/thinking

## Requirements

- Valid XAI API key in config
- Access to company data cache
- Python dependencies installed
- Write permissions for database

## Database Maintenance

The database automatically:
- Creates tables and indexes on first use
- Prevents duplicate analyses (same ticker + timestamp)
- Maintains analysis history for trend analysis
- Supports efficient queries by ticker and timestamp