# BoxRec Scraper - Next Steps

Generated: 2025-07-30 22:48:09

## Immediate Actions:

1. **scrape_wiki_pages**
   ```bash
   python scripts/scrape_wiki_zyte.py
   ```
   - Items: 20
   - Time: 30-60 minutes

2. **parse_wiki_pages**
   ```bash
   python scripts/parse_wiki.py data/raw/boxrec_wiki/
   ```
   - Items: All
   - Time: 5 minutes

3. **combine_all_data**
   ```bash
   python scripts/combine_boxer_json_v2.py
   ```
   - Items: All
   - Time: 2 minutes


## Current Status:
- Total Boxers: 98
- Wiki Coverage: 5/98 (5.1%)
- Completeness Score: 70.6%
