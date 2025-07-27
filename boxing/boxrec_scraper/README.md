# BoxRec Scraper & Parser

A Python pipeline for scraping BoxRec data and converting HTML to structured JSON.

- [boxrec.com urls for scraping spreadsheet](https://docs.google.com/spreadsheets/d/1lw0N35utzNS4m00qVYPfLtSXFM_0IKBxBNL8fmr6lKg/edit?gid=1#gid=1)

## Setup

```bash
# Install dependencies
pip install requests python-dotenv tqdm beautifulsoup4 lxml

# Set up environment (get API key from Zyte.com)
echo "ZYTE_API_KEY=your_key_here" > ../.env
```

## Data Pipeline Flow

- [x] 1. Get URLs of boxers from boxrec site (manual) - [urls list here](https://docs.google.com/spreadsheets/d/1lw0N35utzNS4m00qVYPfLtSXFM_0IKBxBNL8fmr6lKg/edit?gid=1#gid=1)
- [x] 2. Run them through the HTML downloader (`scrape.py`)
- [x] 3. Convert the 'boxer single' HTML files -> JSON objects (`parse_boxer_final.py`)
- [ ] 4. From the JSON, get the data (urls) needed to run scrapes for other entities (fights, etc.)
- [ ] 5. data normalization for fields like:
```
"date": "Sep 25",
"height": "5\u2032 8\u2033 / 173cm",
"birth_place": "Decatur, Georgia, USA",
```
- [ ] 6. db schema & setup
- [ ] 7. populate db & launch to site

## Usage

### 1. Scraping HTML
```bash
# Scrape from urls.csv
python scrape.py urls.csv

# Features:
# - Progress tracking with tqdm
# - Resume capability (skips existing files)
# - Error reporting in JSON summary
# - Parallel downloads (5 workers default)
```

### 2. Parse HTML to JSON
```bash
# Parse single file
python parse_boxer_final.py boxrec_html/en_box-pro_352.html

# Batch parse all files (parallel processing)
python batch_parse.py
```

## File Structure
```
boxrec_scraper/
├── scrape.py              # Downloads HTML from BoxRec via Zyte API
├── parse_boxer_final.py   # Converts HTML to JSON
├── batch_parse.py         # Batch processing with progress
├── urls.csv              # URLs to scrape
├── boxrec_html/          # Downloaded HTML files
├── boxrec_json/          # Parsed JSON files
└── README.md             # This file
```

## JSON Output Format
```json
{
  "boxrec_id": "352",
  "name": "Floyd Mayweather Jr",
  "birth_name": "Floyd Joy Sinclair",
  "alias": "Money, Pretty Boy",
  "birth_place": "Grand Rapids, Michigan, USA",
  "nationality": "USA",
  "stance": "orthodox",
  "height": "5′ 8″ / 173cm",
  "reach": "72″ / 183cm",
  "record": {
    "wins": 50,
    "losses": 0,
    "draws": 0,
    "kos": 27,
    "total_fights": 50
  },
  "division": "welter",
  "residence": "Las Vegas, Nevada, USA",
  "status": "inactive",
  "career": "1996-2017",
  "debut": "1996-10-11",
  "sex": "male",
  "bouts": [
    {
      "date": "Aug 17",
      "opponent": "Conor McGregor",
      "result": "W",
      "method": null,
      "rounds": null,
      "venue": "T-Mobile Arena, Las Vegas"
    }
    // ... more bouts
  ]
}
```


## Next Steps

- Extract event/bout URLs from boxer pages
- Scrape event and bout details
- Build comprehensive fight database