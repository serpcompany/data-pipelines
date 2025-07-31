# BOXREC DATA PIPELINE OVERVIEW

## Pipeline Order:

1. **Scrape Boxer HTML** → 2. **Scrape Wiki Pages** → 3. **Validate HTML** → 4. **Upload All HTML to DB** → 5. **Extract Additional URLs** → 6. **Scrape & Upload Additional Pages**

## Detailed Flow:

```
┌─────────────────┐
│   BoxRec.com    │  ← Source Website
│  (Boxing Data)  │
└────────┬────────┘
         │ 
         ▼
┌─────────────────────────────────────┐
│         STEP 1: Scrape Boxer HTML    │
│                                      │
│  scrape_boxers.py                    │  ← Downloads boxer profile pages
│  Input: CSV with boxer URLs          │    Uses Zyte API
│  Output: HTML files in local dir     │    Parallel processing
└────────────────┬─────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│         STEP 2: Scrape Wiki Pages   │
│                                      │
│  scrape_wiki_zyte.py                 │  ← Downloads boxer wiki pages
│  Input: Boxer IDs from step 1        │    Additional biographical data
│  Output: Wiki HTML files             │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│      STEP 3: Validate HTML Files    │
│                                      │
│  validate_scrapes.py                 │  ← Quality check before DB
│  Input: Directory of HTML files      │    Checks for login pages
│  Output: Validation report           │    Identifies bad scrapes
└────────────────┬─────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│    STEP 4: Upload HTML to Database  │
│                                      │
│  upload_html_to_db.py                │  ← Uploads validated HTML
│  Input: Directory of HTML files      │    
│  Output: Records in DB tables:       │
│  - boxrec_boxer (profiles + wikis)   │
│  - boxrec_event                      │
│  - boxrec_bout                       │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   STEP 5: Extract Additional URLs   │
│                                      │
│  Extract scripts:                    │  ← Parse HTML for more URLs
│  - extract_bout_urls.py              │    Find events/bouts
│  - extract_opponent_urls.py          │    Find opponent boxers
│  Output: CSV files with new URLs     │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  STEP 6: Scrape Additional Pages    │
│                                      │
│  scrape_to_staging_db.py             │  ← Direct to DB scraping
│  Input: URLs from step 5             │    Events, bouts, opponents
│  Output: Direct to DB tables         │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌─────────────────┐
│  PostgreSQL DB  │  ← Final storage
│  Staging Tables │    All HTML stored
│                 │    Ready for processing
└─────────────────┘
```

## Optional: JSON Export Pipeline

```
┌─────────────────┐
│  HTML in DB/    │  ← Starting point
│  Local Files    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HTML Parser    │  ← parse_boxer_v2.py
│   (v2.0.0)      │    Extract structured data
│                 │    40+ fields per boxer
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Individual JSON │  ← data/raw/boxrec_json_v2/
│   Per Boxer     │    One JSON per boxer
│  (Validated)    │    Schema v2.0.0
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Combiner   │  ← combine_boxer_json_v2.py
│                 │    Merge all boxers
│                 │    Apply filters
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Combined Dataset│  ← outputs/v2/combined_boxers.json
│  (Single JSON)  │    All boxers in one file
│                 │    Ready for frontend
└─────────────────┘
```

## Key Scripts:

### Core Pipeline:
- `scrape_boxers.py` - Scrape boxer profiles to files
- `scrape_wiki_zyte.py` - Scrape wiki pages
- `upload_html_to_db.py` - Upload HTML files to database
- `extract_bout_urls.py` - Extract event/bout URLs
- `extract_opponent_urls.py` - Extract opponent URLs
- `scrape_to_staging_db.py` - Scrape directly to database

### Optional JSON Processing:
- `parse_boxer_v2.py` - Parse HTML to JSON
- `process_all_v2.py` - Batch parse all HTML
- `combine_boxer_json_v2.py` - Combine JSONs

### Database Tables:
- `boxrec_boxer` - Boxer profiles and wiki pages
- `boxrec_event` - Event/card pages
- `boxrec_bout` - Individual bout pages