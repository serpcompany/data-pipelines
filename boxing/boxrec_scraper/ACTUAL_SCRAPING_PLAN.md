# Actual Scraping Plan - 24,176 Boxers

Based on the database extraction, we have **24,176 boxers** with BoxRec URLs and slug mappings.

## Time Estimates (24,176 boxers)

### With Current Setup (5 workers):
- **Profile pages**: 24,176 requests
- **Wiki pages**: 24,176 requests  
- **Total requests**: 48,352
- **Time needed**: ~6.7 hours (24/7) or ~1.7 days (6h/day)

### With Optimized Setup (20 workers):
- **Time needed**: ~1.7 hours (24/7) or ~5.7 hours (6h/day)

## Data We Have

✅ **URL → Slug Mapping**: 24,176 entries saved to `data/boxrec_url_slug_mapping.json`
✅ **URLs for Scraping**: Ready in `data/existing_boxers_urls.csv`
✅ **Boxer Names & IDs**: All extracted successfully

## Current Status vs New Data

| Current Status | New Database Data |
|----------------|-------------------|
| 98 boxers scraped | 24,176 boxers available |
| 5 wiki pages | 24,176 wiki pages needed |
| URLs in different format | URLs use `/proboxer/` format |

## Key Differences

1. **URL Format**: Database uses `/proboxer/` while we've been using `/box-pro/`
2. **Scale**: 24,176 vs previous estimate of 67,000
3. **Valuable Mappings**: We now have slug mappings to preserve website URLs

## Next Steps

1. **Convert URLs**: Database URLs use `/proboxer/` - need to convert to `/box-pro/` format
2. **Priority Scraping**: Focus on boxers that already have website presence
3. **Preserve Mappings**: Ensure scraped data maintains URL → slug relationships

## URL Conversion Needed

Database format: `https://boxrec.com/en/proboxer/92636`
Scraping format: `https://boxrec.com/en/box-pro/92636`

Need to convert URLs for scraping while preserving the slug mappings.

## Recommendation

Start with a **1,000 boxer test batch** to:
- Validate URL conversion works
- Test scraping performance  
- Verify data quality
- Estimate real-world timing

This would take ~20 minutes and cost ~$4 to validate the entire pipeline.