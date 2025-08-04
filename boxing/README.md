# DBs

```mermaid
graph LR
    DataLake[(Data Lake<br/>Postgres)] 
    Staging[(staging-mirror-db <br/>mirrors production-preview)]
    Preview[(boxingundefeated.com <br/> production-preview)]
    
    DataLake --> Staging
    Staging --> Preview
```

# Pipeline Flow

```mermaid
flowchart TD
    A[Input: CSV URLs] --> B["1: Scrape HTML via Zyte"]
    B --> C["2: Validate HTML"]
    C --> D{Valid?}
    D -->|No| E[Queue for Rescrape]
    D -->|Yes| F["3: Store in Data Lake"]
    F --> G["4: Extract Fields from HTML"]
    G --> H["5: Clean & Transform Data"]
    H --> I["6: Load to Staging Mirror"]
    I --> J["7: Bulk Validation"]
    J --> K{All Valid?}
    K -->|No| L[Manual Review]
    K -->|Yes| M["8: Schema Compatibility Check"]
    M --> N{Schemas Match?}
    N -->|No| O["Alert: Schema Mismatch!"]
    N -->|Yes| P["9: Manual Push to Preview"]
    P --> Q["10: Production Deploy<br/>Handled by Main Project"]
    
    click B "#step-1-scrape-html-via-zyte"
    click C "#steps-2-9-validation-through-preview-deployment"
    click F "#steps-2-9-validation-through-preview-deployment"
    click G "#steps-2-9-validation-through-preview-deployment"
    click H "#steps-2-9-validation-through-preview-deployment"
    click I "#steps-2-9-validation-through-preview-deployment"
    click J "#steps-2-9-validation-through-preview-deployment"
    click M "#steps-2-9-validation-through-preview-deployment"
    click P "#steps-2-9-validation-through-preview-deployment"
```

## Running the Pipeline

### Step 1: Scrape HTML via Zyte
```bash
cd /Users/devin/repos/projects/boxingundefeated-monorepo/data-pipelines
source .venv/bin/activate
python -m boxing.scrapers.boxrec.boxer 1000boxers.csv
```

### Step 2: Validate HTML
```bash
python -m boxing.run_validators
```

### Steps 3-9: Process, Validate, and Deploy

Before loading data, set up the database (only needed once):
```bash
python -m boxing.run_pipeline setup
```

Then run these commands:
```bash
cd /Users/devin/repos/projects/boxingundefeated-monorepo/data-pipelines
source .venv/bin/activate

# Load scraped HTML and extract data (Steps 2-6)
python -m boxing.run_pipeline load

# Run validation checks (Step 7)
python -m boxing.run_pipeline validate

# Deploy to preview (Step 9)
python -m boxing.run_pipeline deploy-preview
```

Available commands:
- `setup` - Set up staging mirror database (run once before first use)
- `load` - Load scraped HTML and extract data to staging (steps 2-6)
- `validate` - Run data validation checks (step 7)
- `deploy-preview` - Deploy to preview environment (step 9)
- `full` - Run complete pipeline

## TODOs

- **URL Normalization**: Handle mixed BoxRec URL patterns (`proboxer/` vs `box-pro/`). Should normalize to canonical format and store final redirected URL, not original input URL.
- **Field Normalization**: Data extracted from HTML needs normalization before loading to staging:
  - Date format: Convert `Apr 02` to `YYYY-MM-DD` format
  - Result values: Convert `win/loss` to `W/L` format expected by validation
  - Add transformation step between extraction and loading
