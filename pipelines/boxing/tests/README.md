# Pipeline Tests

## Test Structure

```
tests/
├── scrapers/      # Test Zyte API responses, error handling
├── parsers/       # Test HTML parsing with sample files
├── extractors/    # Test field extraction accuracy
├── validators/    # Test login detection, data validation
└── database/      # Test DB operations, schema compatibility
```

## What to Test

1. **Scrapers**: Mock Zyte API responses, handle timeouts
2. **Parsers**: Use sample HTML files, test edge cases
3. **Extractors**: Verify correct data extraction
4. **Validators**: Test login page detection
5. **Database**: Test schema compatibility, data integrity

## Running Tests

```bash
# Python tests
pytest src/tests/

# TypeScript tests  
npm test
```