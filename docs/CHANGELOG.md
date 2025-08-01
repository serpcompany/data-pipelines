# BoxRec Scraper Changelog

## v2.0.0 (2025-07-31)

### Major Changes
- **Breaking**: Updated schema from v1.0.0 to v2.0.0 with expanded field set
- **Breaking**: Renamed several fields for consistency:
  - `name` → `full_name`
  - `alias` → `nickname`
  - `sex` → `gender`
  - `wiki` → `boxrec_wiki_url`
  - `manager_agent` → `manager`
  - `date` → `bout_date` (in bouts)
  - `opponent` → `opponent_name` (in bouts)
  - `venue` → `venue_name` (in bouts)
  - `method` → `result_method` (in bouts)
  - `rounds` → `result_round` (in bouts)

### New Features
- Added v2 parser (`parse_boxer_v2.py`) with enhanced field extraction
- Added migration script (`migrations/v1_to_v2.py`) for upgrading existing data
- Added new boxer profile fields:
  - `image_url` - Profile image URL
  - `date_of_birth` - Birth date
  - `weight` - Current weight/weight class
  - `bio` - Biography text
  - `trainer` - Current trainer
  - `gym` - Boxing gym
  - `pro_losses_by_knockout` - KO losses count
  - Complete amateur record fields (debut, wins, losses, etc.)
  - Timestamps (`created_at`, `updated_at`)

- Added new bout fields:
  - `event_page_link` - Link to event page
  - `bout_page_link` - Link to specific bout page
  - `opponent_weight` - Opponent's weight for the fight
  - `referee_name` - Referee for the bout
  - Judge names and scores (3 judges)
  - `num_rounds_scheduled` - Scheduled rounds
  - `scorecards_page_link` - Link to scorecards
  - `title_fight` - Whether it was a title fight

### Improvements
- Better result method extraction (KO, TKO, decision, etc.)
- Extract round number for knockouts
- Improved opponent interlinking with BoxRec IDs
- Enhanced combine script with v2 schema support
- Better error handling and logging

### Data Quality
- All 99 boxer HTML files successfully parsed with v2 parser
- Migration script successfully converts v1 data to v2 format
- Schema validation available (requires jsonschema package)

### Known Limitations
Some fields require additional page scraping not yet implemented:
- Detailed bout information (referee, judges, weights)
- Amateur record data
- Biography text
- Birth dates
- Some trainer/gym information

These fields are included in the schema for future enhancement.

## v1.0.0 (Initial Release)

### Features
- Basic boxer data extraction from BoxRec HTML
- JSON Schema validation
- Combine script for creating datasets
- Opponent interlinking support
- Concurrent processing