#!/usr/bin/env tsx

import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as dotenv from 'dotenv';
import { sql } from 'drizzle-orm';

// Load environment
dotenv.config({ path: '../.env' });

async function dropBoxersTable() {
  console.log('🗑️  Dropping boxers table...\n');

  const connectionString = `postgresql://${process.env.POSTGRES_USER}:${process.env.POSTGRES_PASSWORD}@${process.env.POSTGRES_HOST}:${process.env.POSTGRES_PORT}/${process.env.POSTGRES_DEFAULT_DB}`;
  
  const client = postgres(connectionString);
  const db = drizzle(client);

  try {
    await db.execute(sql`DROP TABLE IF EXISTS "data-pipelines-staging"."boxers" CASCADE`);
    console.log('✅ Dropped boxers table successfully\n');
  } catch (error) {
    console.error('❌ Error dropping table:', error);
  } finally {
    await client.end();
  }
}

dropBoxersTable().catch(console.error);