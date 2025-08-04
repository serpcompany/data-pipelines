# Boxing Pipeline Tests

## Test Structure

Tests are organized to mirror the source code structure:

```
tests/
├── load/
│   └── test_to_staging_db.py      # Tests for pipelines/boxing/load/to_staging_db.py
├── extract/
│   ├── test_orchestrator.py       # Tests for pipelines/boxing/extract/orchestrator.py
│   └── page/boxer/fields/
│       └── test_bouts.py          # Tests for pipelines/boxing/extract/page/boxer/fields/bouts.py
├── scrapers/
│   └── test_boxrec.py            # Tests for pipelines/boxing/scrapers/boxrec/
└── test_integration.py           # End-to-end integration tests
```

## Running Tests

### Manual Testing
```bash
# Run all tests
python run_pipeline.py test

# Run specific test file
python -m pytest tests/load/test_to_staging_db.py -v

# Run with coverage
python -m pytest --cov=pipelines.boxing tests/
```

### Watch Mode
```bash
# Run tests in watch mode (auto-reruns on file changes)
python run_pipeline.py test-watch

# Or directly with pytest-watch
python -m pytest-watch
```

### Integration with Pipeline

Tests are automatically run:
1. After data loading in the `full` pipeline command
2. Can be manually triggered with `python run_pipeline.py test`
3. Should be run before deploying to preview

## Test Naming Convention

- Test files should be named `test_<module_name>.py`
- Test classes should be named `Test<ClassName>`
- Test functions should be named `test_<what_is_being_tested>`

## Writing Tests

When adding new functionality:
1. Create test file mirroring the source file path
2. Write tests for the expected behavior
3. Run tests to see them fail (TDD)
4. Implement the functionality
5. Run tests to see them pass