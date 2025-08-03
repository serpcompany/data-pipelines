#!/usr/bin/env tsx

import { drizzle } from 'drizzle-orm/postgres-js';
import { migrate } from 'drizzle-orm/postgres-js/migrator';
import postgres from 'postgres';
import * as dotenv from 'dotenv';
import { sql } from 'drizzle-orm';

// Load environment
dotenv.config({ path: '../.env' });

// Import production schema
import { boxers } from './schema/boxers';
import { boxerBouts } from './schema/boxerBouts';
import { divisions } from './schema/divisions';

async function setupStagingDatabase() {
  console.log('🔧 Setting up staging database with production schema...\n');

  const connectionString = `postgresql://${process.env.POSTGRES_USER}:${process.env.POSTGRES_PASSWORD}@${process.env.POSTGRES_HOST}:${process.env.POSTGRES_PORT}/${process.env.POSTGRES_DEFAULT_DB}`;
  
  const client = postgres(connectionString);
  const db = drizzle(client);

  try {
    // Create staging schema if it doesn't exist
    await db.execute(sql`CREATE SCHEMA IF NOT EXISTS "data-pipelines-staging"`);
    console.log('✅ Created staging schema\n');

    // Create tables using production schema structure
    // Note: We'll create these as regular tables in PostgreSQL, not SQLite
    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS "data-pipelines-staging"."boxers" (
        id TEXT PRIMARY KEY,
        boxrec_id TEXT NOT NULL UNIQUE,
        boxrec_url TEXT NOT NULL,
        slug TEXT NOT NULL UNIQUE,
        
        full_name TEXT NOT NULL,
        birth_name TEXT,
        nickname TEXT,
        gender TEXT,
        
        avatar_image TEXT,
        
        residence TEXT,
        birth_place TEXT,
        date_of_birth TEXT,
        nationality TEXT,
        
        height TEXT,
        reach TEXT,
        weight TEXT,
        stance TEXT,
        
        bio TEXT,
        
        promoter TEXT,
        trainer TEXT,
        manager TEXT,
        gym TEXT,
        
        pro_debut_date TEXT,
        pro_division TEXT,
        pro_wins INTEGER NOT NULL DEFAULT 0,
        pro_wins_by_knockout INTEGER NOT NULL DEFAULT 0,
        pro_losses INTEGER NOT NULL DEFAULT 0,
        pro_losses_by_knockout INTEGER NOT NULL DEFAULT 0,
        pro_draws INTEGER NOT NULL DEFAULT 0,
        pro_status TEXT,
        pro_total_bouts INTEGER NOT NULL DEFAULT 0,
        pro_total_rounds INTEGER NOT NULL DEFAULT 0,
        
        amateur_debut_date TEXT,
        amateur_division TEXT,
        amateur_wins INTEGER NOT NULL DEFAULT 0,
        amateur_wins_by_knockout INTEGER NOT NULL DEFAULT 0,
        amateur_losses INTEGER NOT NULL DEFAULT 0,
        amateur_losses_by_knockout INTEGER NOT NULL DEFAULT 0,
        amateur_draws INTEGER NOT NULL DEFAULT 0,
        amateur_status TEXT,
        amateur_total_bouts INTEGER NOT NULL DEFAULT 0,
        amateur_total_rounds INTEGER NOT NULL DEFAULT 0,
        
        is_champion BOOLEAN,
        ranking INTEGER,
        
        -- Additional staging fields
        html_file TEXT,
        html_parsed_at TIMESTAMP,
        parse_errors TEXT,
        
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
    `);
    console.log('✅ Created boxers table\n');

    // Create indexes
    await db.execute(sql`
      CREATE INDEX IF NOT EXISTS boxer_slug_idx ON "data-pipelines-staging"."boxers" (slug);
      CREATE INDEX IF NOT EXISTS boxer_boxrec_id_idx ON "data-pipelines-staging"."boxers" (boxrec_id);
      CREATE INDEX IF NOT EXISTS boxer_nationality_idx ON "data-pipelines-staging"."boxers" (nationality);
      CREATE INDEX IF NOT EXISTS boxer_division_idx ON "data-pipelines-staging"."boxers" (pro_division);
      CREATE INDEX IF NOT EXISTS boxer_status_idx ON "data-pipelines-staging"."boxers" (pro_status);
    `);
    console.log('✅ Created indexes\n');

    // Create boxer_bouts table
    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS "data-pipelines-staging"."boxer_bouts" (
        id TEXT PRIMARY KEY,
        boxer_id TEXT NOT NULL REFERENCES "data-pipelines-staging"."boxers"(id),
        opponent_boxer_id TEXT,
        
        date TEXT,
        location TEXT,
        venue TEXT,
        
        result TEXT,
        result_method TEXT,
        rounds TEXT,
        scheduled_rounds INTEGER,
        
        division TEXT,
        titles TEXT,
        
        is_professional BOOLEAN DEFAULT true,
        
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
    `);
    console.log('✅ Created boxer_bouts table\n');

    // Create divisions table
    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS "data-pipelines-staging"."divisions" (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        weight_limit_lbs INTEGER,
        weight_limit_kg REAL,
        
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
    `);
    console.log('✅ Created divisions table\n');

    // Check if old table exists and migrate data
    try {
      const existingData = await db.execute(sql`
        SELECT COUNT(*) as count FROM "data-pipelines-staging"."boxrec_boxer"
      `);

      if (existingData.rows && existingData.rows[0] && existingData.rows[0].count > 0) {
      console.log(`📊 Found ${existingData.rows[0].count} existing records to migrate\n`);
      
      // Create migration to preserve existing HTML files
      await db.execute(sql`
        INSERT INTO "data-pipelines-staging"."boxers" (
          id,
          boxrec_id,
          boxrec_url,
          slug,
          full_name,
          bio,
          html_file,
          created_at
        )
        SELECT 
          gen_random_uuid(),
          boxrec_id,
          boxrec_url,
          COALESCE(matched_slug, LOWER(REPLACE(boxer_name, ' ', '-'))),
          boxer_name,
          bio,
          html_file,
          created_at
        FROM "data-pipelines-staging"."boxrec_boxer"
        WHERE boxrec_id IS NOT NULL
        ON CONFLICT (boxrec_id) DO NOTHING
      `);
      
        console.log('✅ Migrated existing HTML data to new schema\n');
      }
    } catch (error) {
      // Table doesn't exist, that's fine
      console.log('📝 No existing data to migrate\n');
    }

    console.log('🎉 Staging database setup complete!\n');
    console.log('Next steps:');
    console.log('1. Run HTML parser to extract boxer details');
    console.log('2. Update the boxers table with parsed data');
    console.log('3. Push to production when ready');

  } catch (error) {
    console.error('❌ Error setting up staging database:', error);
    throw error;
  } finally {
    await client.end();
  }
}

// Run the setup
setupStagingDatabase().catch(console.error);