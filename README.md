# Cricket Chatbot Project

A RAG-based cricket chatbot with intelligent data routing using MCP tools.

## ESPNCricinfo Scraper

### Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the scraper:**
```bash
python espncricinfo_scraper.py
```

3. **Test the scraper:**
```bash
python test_scraper.py
```

### Features

- **2025 Season Data**: Scrapes series and match information
- **Live Scores**: Real-time match data
- **Respectful Scraping**: Follows robots.txt guidelines
- **Error Handling**: Retry logic and graceful failures
- **Multiple Formats**: Saves data as JSON and CSV

### Output Files

- `espncricinfo_2025_season.json` - Complete season data
- `espncricinfo_live_scores.json` - Current live matches
- `series_espncricinfo_2025.csv` - Series data in CSV
- `matches_espncricinfo_2025.csv` - Matches data in CSV

### Usage Examples

```python
from espncricinfo_scraper import ESPNCricinfoScraper

scraper = ESPNCricinfoScraper()

# Scrape 2025 season
season_data = scraper.scrape_2025_season()

# Scrape live scores
live_matches = scraper.scrape_live_scores()

# Save data
scraper.save_data(season_data, 'my_data.json')
```

### Notes

- Respects ESPNCricinfo's robots.txt
- Includes 2-second delays between requests
- Handles 403 errors and connection issues
- Extracts series IDs and match IDs for future use

## Next Steps

1. Set up vector database for RAG
2. Implement MCP tools for data routing
3. Create FastAPI backend
4. Build chatbot interface

## Project Structure

```
cricket-chatbot/
├── espncricinfo_scraper.py    # Main scraper
├── test_scraper.py            # Test script
├── requirements.txt           # Dependencies
├── README.md                  # This file
└── data/                      # Output directory (created automatically)
    ├── espncricinfo_2025_season.json
    ├── espncricinfo_live_scores.json
    └── *.csv files
```