# BOXREC DATA PIPELINE OVERVIEW

## Pipeline Steps

### Batch Option: Run Steps 1-4 Together
```bash
# Run scraping and validation in one go:
python boxrec_scraper/scripts/batch_scrape_and_validate.py
```

### Individual Steps

#### 1. Scrape Boxer HTML files
```bash
python boxrec_scraper/scripts/scrape/scrape_boxers_html.py boxrec_scraper/data/5000boxers.csv
```

#### 2. Scrape Wiki Pages
```bash
python boxrec_scraper/scripts/scrape/scrape_wiki_html.py
```

#### 3. Validate HTML
```bash
python boxrec_scraper/scripts/validate/validate_scrapes.py
```

#### 4. Detect and cleanup login pages
```bash
python boxrec_scraper/scripts/cleaning/cleanup_login_files.py
# Or with delete flag:
python boxrec_scraper/scripts/cleaning/cleanup_login_files.py --delete
```
- Generates `login_blocked_urls.csv` for re-scraping
- Optional `--delete` flag to remove login files

### 5. Upload HTML to Database
```bash
python boxrec_scraper/scripts/upload/upload_boxer_html_to_db.py
```

### 6. Extract Additional URLs
```bash
python boxrec_scraper/scripts/extract_urls_from_raw_html/extract_opponent_urls.py
python boxrec_scraper/scripts/extract_urls_from_raw_html/extract_bout_urls.py
```

### 7. Scrape Additional Pages
```bash
python boxrec_scraper/scripts/scrape/scrape_boxers_html.py boxrec_scraper/data/opponent_urls.csv
python boxrec_scraper/scripts/scrape/scrape_boxers_html.py boxrec_scraper/data/bout_urls.csv
```

### 8. Parse HTML to JSON
```bash
# Single file:
python boxrec_scraper/scripts/parse_boxer.py boxrec_scraper/data/raw/boxrec_html/en_box-pro_352.html

# Batch processing:
python boxrec_scraper/scripts/batch_parse_boxers.py
```

### 9. Extract Individual Fields
```bash
# Run all extractors at once:
python boxrec_scraper/scripts/extract/run_all_extractors.py

# Or run individual extractors:
python boxrec_scraper/scripts/extract/extract_name.py
python boxrec_scraper/scripts/extract/extract_pro_wins.py
# etc...
```

## Field Extractors

### Professional Record
- `extract_pro_wins.py`
- `extract_pro_wins_by_knockout.py`
- `extract_pro_losses.py`
- `extract_pro_losses_by_knockout.py`
- `extract_pro_draws.py`
- `extract_pro_status.py`
- `extract_pro_total_bouts.py`
- `extract_pro_total_rounds.py`
- `extract_pro_debut_date.py`
- `extract_pro_division.py`

### Amateur Record
- `extract_amateur_wins.py`
- `extract_amateur_wins_by_knockout.py`
- `extract_amateur_losses.py`
- `extract_amateur_losses_by_knockout.py`
- `extract_amateur_draws.py`
- `extract_amateur_status.py`
- `extract_amateur_total_bouts.py`
- `extract_amateur_total_rounds.py`
- `extract_amateur_debut_date.py`
- `extract_amateur_division.py`

### Basic Information
- `extract_name.py`
- `extract_birth_name.py`
- `extract_nicknames.py`
- `extract_birth_date.py`
- `extract_birth_place.py`
- `extract_nationality.py`
- `extract_gender.py`
- `extract_residence.py`

### Physical Attributes
- `extract_height.py`
- `extract_reach.py`
- `extract_stance.py`

### Professional Information
- `extract_promoters.py`
- `extract_trainers.py`
- `extract_managers.py`
- `extract_gym.py`

### URLs and IDs
- `extract_id.py`
- `extract_boxrec_id.py`
- `extract_boxrec_url.py`
- `extract_boxrec_wiki_url.py`
- `extract_slug.py`

### Other Fields
- `extract_avatar_image.py`
- `extract_bio.py`
- `extract_bouts.py`

## Utility Modules
- `scripts/utils/login_detector.py` - Detects login pages