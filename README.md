# Starlink Webscraping Lab

This repository extracts daily data-usage values from the saved Starlink HTML page and exports them to CSV.

## Files
- `scrape_starlink.py` — reads the saved HTML page and writes the CSV
- `daily_usage.csv` — extracted output
- `requirements.txt` — Python dependency list

## How to run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the scraper:
   ```bash
   python scrape_starlink.py Starlink.html daily_usage.csv
   ```

## Notes
- The page only shows the usage bars in the chart; the x-axis day labels are not visible in the saved HTML.
- The script infers the date range from the page's `Last Updated` value and the number of visible bars.
