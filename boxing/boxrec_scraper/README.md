# BoxRec Scraper & Parser

A comprehensive Python pipeline for scraping BoxRec data and converting HTML to structured JSON with schema versioning and data validation.

- [boxrec.com urls for scraping spreadsheet](https://docs.google.com/spreadsheets/d/1lw0N35utzNS4m00qVYPfLtSXFM_0IKBxBNL8fmr6lKg/edit?gid=1#gid=1)

## Data Pipeline Architecture

```
┌─────────────────┐
│   BoxRec.com    │  ← Source Website
│  (Boxing Data)  │
└────────┬────────┘
         │ HTTP/Scrape
         ▼
┌─────────────────┐
│  Web Scraper    │  ← Python + BeautifulSoup
│  (robots.txt)   │    Rate limited, respectful
└────────┬────────┘
         │ Save HTML
         ▼
┌─────────────────┐
│   Raw HTML      │  ← data/raw/boxrec_html/
│   Storage       │    99 boxer profile pages
│  (.html files)  │    Preserved for reprocessing
└────────┬────────┘
         │ Parse
         ▼
┌─────────────────┐
│  HTML Parser    │  ← parse_boxer_v2.py
│   (v2.0.0)      │    Extract 40+ fields
│                 │    Opponent linking
└────────┬────────┘
         │ Extract
         ▼
┌─────────────────┐
│ Individual JSON │  ← data/raw/boxrec_json_v2/
│   Per Boxer     │    One JSON per boxer
│  (Validated)    │    Schema v2.0.0
└────────┬────────┘
         │ Process
         ▼
┌─────────────────┐
│ Data Processor  │  ← Migration scripts
│  & Migrations   │    v1 → v2 transforms
│                 │    Field mapping
└────────┬────────┘
         │ Combine
         ▼
┌─────────────────┐
│ Combined Dataset│  ← outputs/v2/combined_boxers.json
│  (Single JSON)  │    All boxers in one file
│   + Summary     │    Ready for frontend
└────────┬────────┘
         │
         └──────────────► Nuxt.js App (Direct Import)
```

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Or install manually
pip install requests python-dotenv beautifulsoup4 lxml jsonschema

# Set up environment (optional - for Zyte API)
echo "ZYTE_API_KEY=your_key_here" > ../.env
```

## Data Pipeline Flow

- [x] 1. Get URLs of boxers from boxrec site - [urls list here](https://docs.google.com/spreadsheets/d/1lw0N35utzNS4m00qVYPfLtSXFM_0IKBxBNL8fmr6lKg/edit?gid=1#gid=1)
- [x] 2. Run them through the HTML downloader (`scrape.py`)
- [x] 3. Convert HTML files to JSON using v2 parser (`parse_boxer_v2.py`)
- [x] 4. Extract opponent IDs and links for interlinking
- [x] 5. Combine individual JSONs into single dataset
- [x] 6. Create schema versioning and migrations (v1 → v2)
- [ ] 7. Implement database layer with Drizzle ORM
- [ ] 8. Add bout detail scraping (referees, judges, weights)
- [ ] 9. Add wiki page scraping for additional data

## Usage

### 1. Scraping HTML
```bash
# Scrape from urls.csv
python scripts/scrape.py data/raw/boxrec_html/urls.csv

# Features:
# - Progress tracking
# - Resume capability (skips existing files)
# - Error reporting in JSON summary
# - Parallel downloads (5 workers default)
```

### 2. Parse HTML to JSON (v2 Schema)
```bash
# Parse single file
python scripts/parse_boxer_v2.py data/raw/boxrec_html/en_box-pro_628407.html

# Batch parse all files
python scripts/process_all_v2.py

# Output goes to: data/raw/boxrec_json_v2/
```

### 3. Combine JSON Files
```bash
# Combine all boxers into single dataset
python scripts/combine_boxer_json_v2.py data/raw/boxrec_json_v2/ outputs/v2/combined_boxers.json

# With filters
python scripts/combine_boxer_json_v2.py data/raw/boxrec_json_v2/ outputs/v2/active_boxers.json --active-only --min-wins 10
```

### 4. Migrate Schemas
```bash
# Migrate from v1 to v2
python migrations/v1_to_v2.py data/processed/ data/processed/v2/
```

## File Structure
```
boxrec_scraper/
├── data/
│   ├── raw/
│   │   ├── boxrec_html/          # Downloaded HTML files
│   │   ├── boxrec_json/          # v1 parsed JSON (legacy)
│   │   └── boxrec_json_v2/       # v2 parsed JSON
│   └── processed/
│       └── v2/                   # Migrated/processed data
├── outputs/
│   └── v2/                       # Combined datasets
├── scripts/
│   ├── scrape.py                 # HTML downloader
│   ├── parse_boxer_v2.py         # v2 HTML→JSON parser
│   ├── process_all_v2.py         # Batch processor
│   └── combine_boxer_json_v2.py  # Data combiner
├── schema/
│   ├── v1.0.0.json              # Original schema
│   └── v2.0.0.json              # Current schema
├── migrations/
│   └── v1_to_v2.py              # Schema migration
├── docs/
│   ├── architecture.md          # Detailed architecture
│   └── pipeline-overview.txt    # Visual diagram
├── requirements.txt             # Python dependencies
├── CHANGELOG.md                 # Version history
└── README.md                    # This file
```

## JSON Output Format (v2.0.0)

```json
{
  "boxrec_id": "628407",
  "boxrec_url": "https://boxrec.com/en/box-pro/628407",
  "boxrec_wiki_url": "https://boxrec.com/wiki/index.php?title=Human:628407",
  "slug": "naoya-inoue",
  "full_name": "Naoya Inoue",
  "birth_name": "井上尚弥",
  "nickname": "Monster",
  "image_url": "https://boxrec.com/images/thumb/c/c5/628407.jpeg/200px-628407.jpeg",
  "residence": "Yokohama, Kanagawa, Japan",
  "birth_place": "Zama, Kanagawa, Japan",
  "date_of_birth": null,
  "gender": "male",
  "nationality": "Japan",
  "height": "5′ 5″ / 165cm",
  "reach": "67½″ / 171cm",
  "stance": "orthodox",
  "pro_wins": 30,
  "pro_losses": 0,
  "pro_draws": 0,
  "pro_wins_by_knockout": 27,
  "pro_total_bouts": 30,
  "bouts": [
    {
      "bout_date": "Sep 25",
      "opponent_name": "Murodjon Akhmadaliev",
      "opponent_id": "828415",
      "opponent_url": "https://boxrec.com/en/box-pro/828415",
      "opponent_record": "14-1-0",
      "venue_name": "IG Arena, Nagoya",
      "result": "win",
      "result_method": "ko",
      "result_round": 3,
      "event_page_link": "https://boxrec.com/en/event/926864",
      "bout_page_link": "https://boxrec.com/en/event/926864/3396038",
      "bout_rating": 5
    }
    // ... more bouts
  ],
  "created_at": "2025-07-31T04:15:18.991621Z",
  "updated_at": "2025-07-31T04:15:18.991833Z"
}
```

## Key Features

1. **Schema Versioning**: Explicit v2.0.0 schema with migration support
2. **Data Preservation**: Raw HTML saved for reprocessing
3. **Opponent Linking**: BoxRec IDs enable fight network analysis
4. **Comprehensive Fields**: 40+ boxer fields, 15+ bout fields
5. **Data Validation**: JSON Schema validation
6. **Batch Processing**: Parallel processing with progress tracking
7. **Flexible Filtering**: Combine data with various filters

## Schema Changes (v2.0.0)

### New Fields
- `image_url` - Profile image URLs
- `event_page_link` - Links to event pages
- `bout_page_link` - Links to specific bout pages
- `result_method` - KO, TKO, decision, etc.
- `result_round` - Round number for stoppages
- Complete amateur record fields (placeholders)
- Timestamps (`created_at`, `updated_at`)

### Renamed Fields
- `name` → `full_name`
- `alias` → `nickname`
- `sex` → `gender`
- `wiki` → `boxrec_wiki_url`
- `date` → `bout_date` (in bouts)
- `opponent` → `opponent_name` (in bouts)

## Performance

- **Dataset**: 99 boxers, ~3,000 fights
- **Processing Time**: ~1 minute for full pipeline
- **Storage**: ~50MB HTML, ~10MB processed JSON
- **Scalability**: Ready for 10,000+ boxer profiles

## Next Steps

1. **Database Integration**: Implement Drizzle ORM for structured queries
2. **Bout Details**: Scrape individual bout pages for referee, judges, weights
3. **Wiki Scraping**: Extract additional data from BoxRec wiki pages
4. **API Development**: Create REST endpoints for the Nuxt frontend
5. **Real-time Updates**: Implement incremental scraping for live data
6. **Data Quality**: Add monitoring and validation pipelines

## Contributing

1. Follow existing code style and conventions
2. Update schema version for breaking changes
3. Create migration scripts for schema updates
4. Test with `simple_validate.py` before committing
5. Update documentation for significant changes

## License

This project is for educational and research purposes. Please respect BoxRec's terms of service and robots.txt when scraping.