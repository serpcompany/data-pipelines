# Push to Production Pipeline

This TypeScript pipeline pushes data from the staging PostgreSQL database to the production MySQL database using Drizzle ORM.

## Architecture

This pipeline uses **database introspection** to always match the production schema exactly. Instead of maintaining schema files manually, we pull the schema directly from the production database.

### Why Database-First?

1. **Always Accurate**: The schema always matches what's actually deployed
2. **No Sync Issues**: No risk of schema files being out of date
3. **Catches Manual Changes**: If someone made database changes outside of migrations, we'll see them
4. **Type Safety**: Still get full TypeScript types generated from the real schema

## Setup

### 1. Install Dependencies

```bash
cd push-to-production
pnpm install
```

### 2. Configure Database Access

The pipeline uses the same `.env` file as the parent project (located at `../.env`).

Make sure these variables are set:
```env
# Production Database (MySQL) - for introspection and pushing
DB_HOST=
DB_PORT=
DB_USERNAME=
DB_PASS=
DB_NAME=

# Staging Database (PostgreSQL) - for reading data
POSTGRES_HOST=
POSTGRES_PORT=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DEFAULT_DB=
```

### 3. Pull Production Schema

```bash
# This introspects the production database and generates TypeScript schema files
pnpm run pull-schema
```

This command:
- Connects to your production MySQL database
- Reads all table structures
- Generates TypeScript schema files in `src/schema/`
- Gives you full type safety for all database operations

**Note**: Run this whenever the production schema might have changed.

## Usage

```bash
# First time setup
pnpm run setup

# Update schema from production
pnpm run pull-schema

# Analyze staging vs production data
pnpm run analyze

# Dry run (preview what would be pushed)
pnpm run push:dry-run

# Push data to production
pnpm run push
```

## Workflow

1. **Pull Schema**: `pnpm run pull-schema` - Get latest schema from production
2. **Analyze**: `pnpm run analyze` - Compare staging data with production schema
3. **Test**: `pnpm run push:dry-run` - Preview changes
4. **Push**: `pnpm run push` - Push data to production

## Safety Features

- **Dry Run Mode**: Preview all changes before pushing
- **Schema Validation**: Data is validated against production schema
- **Idempotent Operations**: Safe to run multiple times
- **Transaction Support**: Changes are atomic

## Development

```bash
# Watch mode for development
pnpm run dev

# Type checking
pnpm run typecheck

# Build
pnpm run build
```