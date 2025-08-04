# Issue: Optimize Data Lake Upload Performance

## Problem
The current data lake upload process is too slow for production use. Loading 916 files is taking several minutes, with each record being processed individually. At this rate, loading hundreds of thousands of records would be impractical.

## Current Implementation Issues
1. **Individual INSERT statements** - Each record is inserted one at a time
2. **Individual file reads** - Files are read and processed sequentially
3. **No connection pooling** - New database connection for each file
4. **No batch processing** - No grouping of operations

## Performance Metrics
- Current: ~2-3 records per second
- Needed: 100+ records per second minimum

## Proposed Optimizations

### 1. Batch Inserts
- Use `psycopg2.extras.execute_batch()` or `execute_values()`
- Group INSERTs into batches of 100-1000 records
- Use COPY command for bulk loading when possible

### 2. Connection Pooling
- Implement connection pooling to reuse database connections
- Reduce connection overhead

### 3. Parallel Processing
- Use multiprocessing or threading to process files in parallel
- Read multiple files concurrently
- Batch database operations from multiple workers

### 4. Optimized Duplicate Detection
- Load all existing boxer IDs into memory at start
- Use in-memory set for duplicate checking instead of individual SELECTs
- Only check database for updates when ID exists in memory

### 5. Transaction Management
- Group operations into larger transactions
- Commit every N records instead of after each record

## Example Implementation
```python
# Batch insert example
from psycopg2.extras import execute_values

def batch_insert_boxers(records, batch_size=1000):
    with connection_pool.getconn() as conn:
        with conn.cursor() as cur:
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                execute_values(
                    cur,
                    """
                    INSERT INTO "data-lake".boxrec_boxer_raw_html 
                    (boxrec_url, boxrec_id, html_file, competition_level, scraped_at, created_at, updated_at)
                    VALUES %s
                    ON CONFLICT (boxrec_id, competition_level) DO UPDATE
                    SET html_file = EXCLUDED.html_file,
                        scraped_at = EXCLUDED.scraped_at,
                        updated_at = EXCLUDED.updated_at
                    WHERE "data-lake".boxrec_boxer_raw_html.html_file != EXCLUDED.html_file
                    """,
                    batch
                )
            conn.commit()
```

## Priority
HIGH - This is a critical performance bottleneck that will only get worse with more data

## Acceptance Criteria
- Data lake upload should process at least 100 records per second
- Should handle 100,000+ records without timing out
- Maintain data integrity and duplicate detection
- Add progress reporting for large batches