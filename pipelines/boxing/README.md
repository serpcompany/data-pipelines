# Boxing Data Pipeline - New Structure

## Pipeline Flow

### Database Architecture

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   Data Lake         │     │   Staging DB        │     │   Production        │
│   (Postgres)        │ →   │   (Local SQLite)    │ →   │   (CloudFlare D1)   │
├─────────────────────┤     ├─────────────────────┤     ├─────────────────────┤
│ • raw_html_files    │     │ • boxers            │     │ • boxers            │
│ • scrape_metadata   │     │ • fights            │     │ • fights            │
│ • change_tracking   │     │ • [mirrors prod]    │     │ • [production data] │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
         ↓                           ↓                            ↓
    Raw Storage              Schema Validation            Preview → Prod
                                    ↓
                            ┌─────────────────────┐
                            │ Production-Preview  │
                            │ (CloudFlare D1)     │
                            │ staging.domain.com  │
                            └─────────────────────┘
```

## Pipeline Flow

```
Discovery Sources:
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Initial CSV List │ │ Opponent URLs    │ │ Recent Changes   │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
┌────────┴─────────┐ ┌────────┴─────────┐ ┌────────┴─────────┐
│ Event Pages      │ │ Weight Classes   │ │ Other Sources    │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
         └────────────────────┴────────────────────┘
                              ↓
                    All URLs feed into...
                              ↓
┌─────────────────────────┐
│ Input: CSV with URLs    │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│ 1. Scrape HTML (Zyte)   │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│ Store as File (temp)    │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│ 2. Validate HTML        │
└───────────┬─────────────┘
            ↓
        Login Page?
       ↙         ↘
     Yes          No
      ↓            ↓
┌──────────────┐  ┌─────────────────────────┐
│ Queue URL    │  │ 3. Store in Data Lake   │
│ for Rescrape │  │    (Postgres)           │
│              │  │    • HTML content       │
│              │  │    • URL                │
│              │  │    • Timestamp          │
│              │  │    • Change tracking    │
└──────────────┘  └───────────┬─────────────┘
                              ↓
                  ┌─────────────────────────┐
                  │ Delete Temp File        │
                  │ (cleanup only)          │
                  └─────────────────────────┘
                              
                  ┌─────────────────────────┐
                  │ 4. Extract Fields        │
                  │    (from Data Lake)     │◄──── Query HTML from
                  └───────────┬─────────────┘      Postgres as needed
                              ↓
                  ┌─────────────────────────┐
                  │ 5. Clean & Transform    │
                  │    (extracted data)     │
                  └───────────┬─────────────┘
                              ↓
                  ┌─────────────────────────┐
                  │ 6. Load to Staging DB    │
                  │    (Local SQLite)       │
                  │    • Structured fields  │
                  │    • Mirrors prod schema│
                  └───────────┬─────────────┘
                              ↓
                  ┌─────────────────────────┐
                  │ 7. Bulk Validation      │
                  │    (cross-record checks)│
                  └───────────┬─────────────┘
                              ↓
                         All Valid?
                        ↙         ↘
                      No           Yes
                      ↓             ↓
                ┌──────────┐  ┌─────────────────────────┐
                │  Manual  │  │ 8. Schema Compatibility │
                │  Review  │  │    Check                │
                └──────────┘  └───────────┬─────────────┘
                                          ↓
                                   Schemas Match?
                                  ↙            ↘
                                No              Yes
                                ↓                ↓
                        ┌─────────────┐  ┌─────────────────────────┐
                        │ Alert:      │  │ 9. Push to Preview      │
                        │ Schema      │  │    (CloudFlare D1)      │
                        │ Mismatch!   │  │    staging.domain.com   │
                        └─────────────┘  └───────────┬─────────────┘
                                                     ↓
                                         ┌─────────────────────────┐
                                         │ 10. Manual Approval     │
                                         │     & Push to Prod      │
                                         │     (CloudFlare D1)     │
                                         └─────────────────────────┘
```

## Current Implementation Status

### ✅ Completed
- **Step 1: Scrape HTML** - `scrapers/boxrec/boxer.py` using Zyte API
- **Step 2: Validate HTML** - Modular validators in `validators/`
  - `login_page.py` - Detect BoxRec login pages
  - `file_size.py` - Check minimum file size
  - `error_page.py` - Detect 404/403 errors
  - `rate_limit.py` - Detect rate limiting
  - `pages/boxer.py` - Validate boxer page content
- **Step 4: Extract Fields** - 38 extractors in `extract/page/boxer/fields/`
  - Professional stats: `wins_pro.py`, `losses_pro.py`, etc.
  - Amateur stats: `wins_amateur.py`, `losses_amateur.py`, etc.
  - Profile data: `name.py`, `nationality.py`, `height.py`, etc.
  - Fight history: `bouts.py`
- **Step 5: Transform** - `transform/slug.py` for derived values

### 🚧 In Progress
- **Step 3: Store in Data Lake** - Postgres schema for raw HTML storage
- **Step 6: Load to Staging DB** - SQLite database setup

### ❌ Not Started
- **Step 7: Bulk Validation** - Cross-record validation logic
- **Step 8: Schema Compatibility** - Drizzle schema comparison
- **Step 9: Push to Preview** - CloudFlare D1 integration
- **Step 10: Production Push** - Manual approval workflow