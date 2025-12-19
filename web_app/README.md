# Glassdoor Rating Web App

A simple web application to search for company Glassdoor ratings by ticker symbol.

## Features

- 🔍 Search for Glassdoor ratings by ticker symbol
- ⭐ Beautiful, modern UI with gradient design
- 📊 Display rating, number of reviews, and company information
- 🔗 Direct links to Glassdoor company pages
- 📱 Responsive design that works on all devices

## Installation

1. Install Flask (if not already installed):
```bash
pip install flask
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

## Running the App

1. Navigate to the web_app directory:
```bash
cd web_app
```

2. Start the Flask server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

3. Enter a ticker symbol (e.g., AAPL, MSFT, GOOGL) and click Search!

## API Endpoints

- `GET /` - Main search page
- `GET /api/search/<ticker>` - Search for a specific ticker's Glassdoor rating
- `GET /api/list` - List all available tickers in the database

## Testing

To run the automated test suite:

1. Install test dependencies:
```bash
python -m pip install pytest pytest-mock pytest-xdist pytest-cov
```

2. Run tests from the root directory:
```bash
python -m pytest -n auto
```

Or run the provided `run_tests.bat` script on Windows (which runs in parallel by default).

3. Run coverage analysis (in parallel):
```bash
python -m pytest -n auto --cov=web_app --cov-report=term-missing
```

Or run the provided `run_coverage.bat` script on Windows. This will also generate a detailed HTML report in the `htmlcov` directory.

### Test Coverage
- **Smoke Tests**: Verifies all services and repositories can be imported and initialized.
- **API Tests**: Checks that Flask endpoints return correct JSON structures.
- **Calculation Tests**: Verifies math for Adjusted PE, Annualized Growth, and Forward PE.
- **Mock Tests**: Tests logic by mocking external API responses from YFinance.

## Example Usage

Search for Apple's Glassdoor rating:
```
http://localhost:5000/api/search/AAPL
```

## Data Source

The app reads from `web_app/data/glassdoor.json` which contains Glassdoor ratings for various companies. The data file is included in this directory for easy deployment.

## Notes

- The app runs on port 5000 by default
- Set `debug=False` in production
- The data file is loaded on each request (consider caching for better performance)

