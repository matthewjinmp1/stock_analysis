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

1. Start the Flask server:
```bash
python web_app.py
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

## Example Usage

Search for Apple's Glassdoor rating:
```
http://localhost:5000/api/search/AAPL
```

## Data Source

The app reads from `data/glassdoor.json` which contains Glassdoor ratings for various companies. Make sure this file exists and is populated with data.

## Notes

- The app runs on port 5000 by default
- Set `debug=False` in production
- The data file is loaded on each request (consider caching for better performance)

