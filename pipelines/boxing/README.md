# Boxing Data Pipeline - New Structure

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
│ Queue URL    │  │ Store in Raw DB Table   │
│ for Rescrape │  │ (HTML + timestamp)      │
└──────────────┘  └───────────┬─────────────┘
                              ↓
                  ┌─────────────────────────┐
                  │ Delete Temp File        │
                  └───────────┬─────────────┘
                              ↓
                  ┌─────────────────────────┐
                  │ 3. Extract Fields        │
                  │    from HTML            │
                  └───────────┬─────────────┘
                              ↓
                  ┌─────────────────────────┐
                  │ 4. Clean & Validate     │
                  └───────────┬─────────────┘
                              ↓
                  ┌─────────────────────────┐
                  │ 5. Upload to Staging DB  │
                  │    (structured fields)  │
                  └───────────┬─────────────┘
                              ↓
                  ┌─────────────────────────┐
                  │ 6. Bulk Validation      │
                  │    (cross-record checks)│
                  └───────────┬─────────────┘
                              ↓
                         All Valid?
                        ↙         ↘
                      No           Yes
                      ↓             ↓
                ┌──────────┐  ┌─────────────────────────┐
                │  Manual  │  │ 7. Schema Compatibility │
                │  Review  │  │    Check                │
                └──────────┘  └───────────┬─────────────┘
                                          ↓
                                   Schemas Match?
                                  ↙            ↘
                                No              Yes
                                ↓                ↓
                        ┌─────────────┐  ┌─────────────────────┐
                        │ Alert:      │  │ 8. Push to Preview  │
                        │ Schema      │  │    Environment DB   │
                        │ Mismatch!   │  │ (staging.domain.com)│
                        └─────────────┘  └─────────────────────┘
```