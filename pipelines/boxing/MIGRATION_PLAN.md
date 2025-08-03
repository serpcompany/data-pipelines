# Migration Plan: Boxing-v1 → Boxing

## Pipeline Step Mapping

### 1. Scrape HTML (Zyte)
**Old Location**: `boxing-v1/boxrec_scraper/scripts/scrape/scrape_boxers_html.py`
**New Location**: `boxing/scrapers/boxrec.py`
**Action**: 
- Extract core Zyte API logic
- Remove hardcoded paths
- Add proper error handling
- Keep CSV input format

### 2. Validate HTML
**Old Location**: `boxing-v1/boxrec_scraper/scripts/utils/login_detector.py`
**New Location**: `boxing/validators/login_detector.py`
**Action**: 
- Copy as-is (it's already clean)
- Add tests

### 3. Store in Raw DB Table
**Old Location**: `boxing-v1/boxrec_scraper/scripts/upload/upload_boxer_html_to_db.py`
**New Location**: `boxing/database/raw_storage.ts`
**Action**: 
- Rewrite in TypeScript
- Use Drizzle ORM
- Add timestamp and hash fields
- Switch from PostgreSQL to SQLite

### 4. Extract Fields
**Old Location**: `boxing-v1/boxrec_scraper/scripts/extract/` (50+ files)
**New Location**: `boxing/extractors/fields/`
**Action**: 
- Group related extractors:
  - `professional.py` - All pro stats
  - `amateur.py` - All amateur stats  
  - `physical.py` - Height, reach, stance
  - `identity.py` - Name, birth info, nationality
  - `team.py` - Trainers, managers, promoters
- Keep extraction logic, consolidate files

### 5. Clean & Validate
**Old Location**: Scattered validation in extractors
**New Location**: `boxing/validators/field_validator.py`
**Action**: 
- Create new centralized validator
- Add type checking
- Add business logic validation

### 6. Upload to Staging DB
**Old Location**: Various upload scripts
**New Location**: `boxing/database/staging_upload.ts`
**Action**: 
- New TypeScript file
- Use Drizzle ORM
- Batch inserts

### 7. Schema Compatibility Check
**Old Location**: `boxing-v1/push-to-production/scripts/pull-production-schema.sh`
**New Location**: `boxing/database/schema_check.ts`
**Action**: 
- Adapt existing Drizzle introspection
- Compare local vs remote schemas

### 8. Push to Preview
**Old Location**: `boxing-v1/push-to-production/src/push-to-production.ts`
**New Location**: `boxing/database/push_to_preview.ts`
**Action**: 
- Adapt for CloudFlare D1
- Keep dry-run capability

## Discovery Sources (URL Generators)
- `extract_opponent_urls.py` → `boxing/scrapers/discovery/opponents.py`
- `extract_bout_urls.py` → `boxing/scrapers/discovery/bouts.py`
- `scrape_recent_changes.py` → `boxing/scrapers/discovery/changes.py`

## Priority Order
1. **Scraper** - Need this first to get data
2. **Login Detector** - Need to validate scraped data
3. **Field Extractors** - Core business logic
4. **Database Storage** - Store processed data
5. **Schema Tools** - Ensure compatibility

## Key Changes
1. **Database**: PostgreSQL → SQLite (for D1 compatibility)
2. **Language Split**: Database ops in TypeScript, parsing in Python
3. **Consolidation**: 50+ extractors → 5-6 grouped files
4. **Path Management**: Hardcoded paths → Config-based