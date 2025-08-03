# Main Project Configuration Reference

This document contains all the configuration and schema information from the main BoxingUndefeated.com project that the data pipeline needs.

## CloudFlare D1 Database Configuration

### Production Database
- **Database Name**: `boxingundefeated-com`
- **Database ID**: `6b463a07-05a9-4da1-9637-f8331d40b36c`
- **Status**: Production data (17 divisions, 2,721 boxers, 84,038 bouts)

### Preview Database  
- **Database Name**: `boxingundefeated-com-preview`
- **Database ID**: `9dde6ccf-fc52-41a3-9268-1a92dabaafb7`
- **Status**: Preview/staging data

### CloudFlare Account
- **Account ID**: `cec5f04e1d18bcc65f2be0aefb04f059`

## Database Schema (from server/database/schema/)

### Divisions Table
```typescript
import { sqliteTable, text, real } from 'drizzle-orm/sqlite-core';

export const divisions = sqliteTable('divisions', {
  id: text().primaryKey(),
  slug: text().notNull().unique(),
  name: text().notNull(),
  alternativeNames: text(),
  weightLimitPounds: real().notNull(),
  weightLimitKilograms: real().notNull(),
  weightLimitStone: text(),
  shortName: text(), // Added in migration 0002
  createdAt: text().default('CURRENT_TIMESTAMP').notNull(),
  updatedAt: text().default('CURRENT_TIMESTAMP').notNull(),
});
```

### Boxers Table
```typescript
import { sqliteTable, text, integer, index } from 'drizzle-orm/sqlite-core';
import { sql } from 'drizzle-orm';

export const boxers = sqliteTable('boxers', {
  id: text().primaryKey(),
  boxrecId: text().notNull().unique(),
  boxrecUrl: text().notNull().unique(),
  boxrecWikiUrl: text(),
  slug: text().notNull().unique(),
  
  name: text().notNull(),
  birthName: text(),
  nicknames: text(),
  
  avatarImage: text(),
  
  residence: text(),
  birthPlace: text(),
  dateOfBirth: text(),
  gender: text(), // 'M' | 'F'
  nationality: text(),
  
  height: text(), // cm by default
  reach: text(), // cm by default
  stance: text(), // 'orthodox' | 'southpaw'
  
  bio: text(),
  
  promoters: text(), // JSON array stored as text
  trainers: text(), // JSON array stored as text
  managers: text(), // JSON array stored as text
  gym: text(),
  
  proDebutDate: text(),
  proDivision: text(),
  proWins: integer().notNull().default(0),
  proWinsByKnockout: integer().notNull().default(0),
  proLosses: integer().notNull().default(0),
  proLossesByKnockout: integer().notNull().default(0),
  proDraws: integer().notNull().default(0),
  proStatus: text(), // 'active' | 'inactive'
  proTotalBouts: integer(),
  proTotalRounds: integer(),
  
  amateurDebutDate: text(),
  amateurDivision: text(),
  amateurWins: integer(),
  amateurWinsByKnockout: integer(),
  amateurLosses: integer(),
  amateurLossesByKnockout: integer(),
  amateurDraws: integer(),
  amateurStatus: text(), // 'active' | 'inactive'
  amateurTotalBouts: integer(),
  amateurTotalRounds: integer(),
  
  createdAt: text().notNull().default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text().notNull().default(sql`CURRENT_TIMESTAMP`),
}, (table) => ({
  slugIdx: index('boxersSlugIdx').on(table.slug),
  boxrecIdIdx: index('boxersBoxrecIdIdx').on(table.boxrecId),
  nationalityIdx: index('boxersNationalityIdx').on(table.nationality),
  divisionIdx: index('boxersDivisionIdx').on(table.proDivision),
  statusIdx: index('boxersStatusIdx').on(table.proStatus),
}));
```

### BoxerBouts Table
```typescript
import { sqliteTable, text, integer, index } from 'drizzle-orm/sqlite-core';

export const boxerBouts = sqliteTable('boxerBouts', {
  id: text().primaryKey(),
  boxerId: text().notNull().references(() => boxers.id),
  
  date: text(),
  opponent: text(),
  opponentUrl: text(),
  location: text(),
  result: text(),
  resultType: text(),
  rounds: integer(),
  time: text(),
  division: text(),
  titles: text(),
  
  // Fight details
  firstBoxerWeight: text(),
  secondBoxerWeight: text(),
  referee: text(),
  judges: text(), // JSON array stored as text
  
  // Metadata
  boutType: text(), // 'pro' | 'amateur'
  boutOrder: integer(),
  
  createdAt: text().notNull().default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text().notNull().default(sql`CURRENT_TIMESTAMP`),
}, (table) => ({
  boxerIdx: index('boutsBoxerIdx').on(table.boxerId),
  dateIdx: index('boutsDateIdx').on(table.date),
  resultIdx: index('boutsResultIdx').on(table.result),
}));
```

## API Endpoints

### Main Application
- **Production**: https://boxingundefeated.com
- **Preview**: https://[deployment-hash].boxingundefeated-com.pages.dev

### Seed Endpoint
- **Path**: `/api/admin/seed`
- **Method**: POST
- **Auth**: Requires `x-seed-secret-key` header (production only)

## Drizzle Configuration

From `drizzle.config.ts`:
```typescript
import { defineConfig } from 'drizzle-kit'

export default defineConfig({
  dialect: 'sqlite',
  schema: './server/database/schema/index.ts',
  out: './server/database/migrations',
  dbCredentials: {
    url: process.env.DRIZZLE_DB_URL || ''
  }
})
```

## Wrangler Configuration

From `wrangler.toml`:
```toml
[[d1_databases]]
binding = "D1"
database_name = "boxingundefeated-com"
database_id = "6b463a07-05a9-4da1-9637-f8331d40b36c"
preview_database_id = "9dde6ccf-fc52-41a3-9268-1a92dabaafb7"
migrations_dir = "server/database/migrations"
```

## Migration History

As of last sync, both production and preview have 17 migrations:
- 0000_small_norman_osborn.sql (initial schema)
- 0001_melodic_sentinel.sql
- 0002_sweet_argent.sql (adds shortName to divisions)
- 0003_worried_songbird.sql
- 0004_seed-initial-data.sql
- 0005_seed-boxers-part1.sql through 0015_seed-boxers-part11.sql
- 0016_seed-boxer-bouts-compressed.sql

## Data Counts (Current)

- **Divisions**: 17
- **Boxers**: 2,721
- **Boxer Bouts**: 84,038

## Environment Variables Required

For pipeline operations that interact with the main project:

```bash
# CloudFlare
CLOUDFLARE_ACCOUNT_ID=cec5f04e1d18bcc65f2be0aefb04f059
CLOUDFLARE_D1_ID_BOXINGUNDEFEATED_PRODUCTON=6b463a07-05a9-4da1-9637-f8331d40b36c
CLOUDFLARE_D1_DBNAME_BOXINGUNDEFEATED_PRODUCTON=boxingundefeated-com

# GitHub (for schema comparison)
GITHUB_PAT=<your-github-pat>
GITHUB_MAIN_PROJECT_REPO=serpcompany/boxingundefeated.com
```

## NPM Scripts from Main Project

Relevant database scripts:
- `npm run db:generate` - Generate migrations from schema changes
- `npm run db:migrate` - Apply migrations
- `npm run db:push` - Push schema changes
- `npm run db:studio` - Open Drizzle Studio
- `npm run db:seed` - Run seed task
- `npm run db:compare` - Compare schemas between environments

## Notes

1. The main project uses Nuxt Hub which provides `hubDatabase()` for database access
2. D1 is SQLite-based in all environments (local, preview, production)
3. Migrations are tracked in `_hub_migrations` table
4. The schema comparison script is at `main-project/scripts/compare-schemas.cjs`
5. All seed data is included in migrations 0004-0016