# Push to Production Pipeline Architecture

## Overview

This pipeline follows a **schema-first** approach where the production schema drives the entire data flow:

```
HTML Files → Staging DB (production schema) → Production DB (Cloudflare D1)
                         ↓
                    JSON export (optional)
```

## Key Benefits

1. **Single Schema Definition**: Production schema (Drizzle) is the only schema definition
2. **Type Safety**: Same TypeScript types used throughout the pipeline
3. **Direct Parsing**: HTML is parsed directly into the correct schema format
4. **Less Transformation**: No intermediate JSON files or schema conversions needed

## Pipeline Steps

### 1. Fetch Production Schema
```bash
pnpm run fetch-schema
```
- Uses GitHub CLI to fetch latest schema from private repo
- Stores schema files in `src/schema/`
- Always up-to-date with production

### 2. Setup Staging Database
```bash
pnpm run setup-staging
```
- Creates staging tables in PostgreSQL matching production schema
- Includes additional fields for tracking (html_file, parse_errors, etc.)
- Migrates any existing HTML data

### 3. Parse HTML to Database Fields
```bash
pnpm run parse-html
```
- Parses BoxRec HTML files using Cheerio
- Extracts all boxer fields defined in production schema
- Updates staging database with parsed data
- Tracks parsing errors and timestamps

### 4. Push to Production
```bash
pnpm run push:dry-run  # Preview changes
pnpm run push          # Actually push data
```
- Validates data against production schema
- Pushes from staging PostgreSQL to production Cloudflare D1
- Idempotent operations (safe to run multiple times)

## Database Schema

The staging database mirrors the production schema with these tables:

- **boxers**: Main boxer information
- **boxerBouts**: Fight records (linked to boxers)
- **divisions**: Weight divisions reference

Additional staging fields:
- `html_file`: Raw HTML storage
- `html_parsed_at`: When HTML was parsed
- `parse_errors`: Any parsing errors

## Data Flow Example

1. **Scraper** downloads HTML: `en_box-pro_628407.html`
2. **Uploader** stores in staging: `boxrec_boxer` table
3. **Parser** extracts fields: Name, record, bio, etc.
4. **Staging DB** holds structured data matching production schema
5. **Push script** validates and sends to production D1

## Configuration

Environment variables (inherited from parent `.env`):
- `POSTGRES_*`: Staging database
- `DB_*`: Production database (when D1 is deployed)
- `GITHUB_TOKEN`: For private repo access (optional)

## Next Steps

1. Deploy Cloudflare D1 database to production
2. Update push script with D1 credentials
3. Set up scheduled runs (cron/GitHub Actions)
4. Add monitoring and alerts