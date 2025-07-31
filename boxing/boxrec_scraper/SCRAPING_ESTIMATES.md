# BoxRec Scraping Time Estimates

## Summary

For scraping **67,000 boxer profiles** (plus their wiki pages):

- **Total Requests**: 134,000 (2 pages per boxer)
- **Time Required**: 
  - Running 24/7: **0.7 days** (17 hours)
  - Running 6h/day: **2.9 days**
- **Estimated Cost**: **$253.26** (Zyte API)

## Current Status

We have scraped:
- 98 boxer profiles
- 5 wiki pages
- Remaining: ~66,900 boxers to complete

## Time Breakdown

| Dataset Size | Requests | 24/7 Time | 6h/day Time | Cost |
|-------------|----------|-----------|-------------|------|
| 1,000 boxers | 2,000 | 6 hours | 1 day | $3.78 |
| 5,000 boxers | 10,000 | 1.2 days | 5 days | $18.90 |
| 10,000 boxers | 20,000 | 2.4 days | 10 days | $37.80 |
| 25,000 boxers | 50,000 | 6 days | 25 days | $94.50 |
| 67,000 boxers | 134,000 | 17 hours | 3 days | $253.26 |

## Assumptions

- **Zyte API Rate**: 2 requests/second
- **Concurrent Requests**: 10
- **Average Response Time**: 3 seconds
- **Retry Rate**: 5% of requests
- **Failure Rate**: 1% permanent failures

## Recommended Approach

1. **Batch Processing**: Process in batches of 1,000 URLs
   - Each batch takes ~20 minutes
   - Easy to monitor and resume from failures

2. **Incremental Updates**: Use the inventory system to:
   - Track what's been scraped
   - Resume from failures
   - Prioritize missing data

3. **Cost Optimization**:
   - Monitor actual API usage vs estimates
   - Cache responses to avoid re-scraping
   - Use RecentChanges to update only changed pages

## Next Steps

1. Complete scraping the current 99 boxers' wiki pages
2. Test with a 1,000 boxer batch to validate estimates
3. Plan full scraping based on actual performance metrics