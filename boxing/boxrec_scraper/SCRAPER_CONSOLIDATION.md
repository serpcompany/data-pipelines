# Scraper Consolidation Plan

## Current Problem (Not DRY)
- **scrape.py** - Original basic scraper  
- **scrape_concurrent.py** - Optimized version with better features
- **scrape_batch.py** - Unnecessary wrapper

## Solution: Keep One Good Scraper

**Recommend keeping `scrape_concurrent.py`** because it has:
- Better performance (20+ workers)
- Rate limiting 
- Real-time stats
- Resume capability
- Better error handling
- Configurable parameters

## Files to Remove:
- `scripts/scrape.py` - Replace with concurrent version
- `scripts/scrape_batch.py` - Unnecessary wrapper

## Single Command:
```bash
python scripts/scrape_concurrent.py --csv data/first_1000_urls.csv --workers 25
```

This gives us one well-designed scraper instead of 3 overlapping ones.