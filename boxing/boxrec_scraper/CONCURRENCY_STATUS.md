# Concurrency Status

## Current Setup

### Existing Scripts (Limited Concurrency)
- `scrape.py`: **5 workers**
- `scrape_wiki_zyte.py`: **5 workers**
- `process_all_v2.py`: **4 workers**

This is **very conservative** and limits throughput significantly.

## Optimized Setup

### New Script: `scrape_concurrent.py`
- **20 workers** (default, configurable)
- **Rate limiting**: 10 requests/second
- **Progress tracking**: Real-time stats
- **Error handling**: Retries and failure tracking
- **Resume capability**: Skips already downloaded files

## Time Impact

With proper concurrency:

| Workers | 67,000 Boxers Time | Speed |
|---------|-------------------|--------|
| 5 (current) | ~17 hours | ~1.1 req/s |
| 20 (optimized) | ~4.5 hours | ~4.1 req/s |
| 50 (aggressive) | ~2 hours | ~9.3 req/s |

## Usage

```bash
# Test with 5 boxers
python scripts/scrape_concurrent.py

# Scrape from CSV with custom workers
python scripts/scrape_concurrent.py --csv data/raw/urls.csv --workers 30

# Scrape specific boxer IDs
python scripts/scrape_concurrent.py --boxer-ids 628407,348759,474 --workers 20
```

## Recommendations

1. **Start with 20 workers** - Safe default that won't overwhelm Zyte
2. **Monitor actual throughput** - Adjust based on response times
3. **Check Zyte plan limits** - Some plans allow 100+ concurrent requests
4. **Use rate limiting** - Prevents hitting API limits

## Next Steps

1. Test the concurrent scraper with a small batch
2. Monitor Zyte API response times and errors
3. Adjust workers based on performance
4. Scale up to full 67,000 boxer dataset