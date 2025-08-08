#!/usr/bin/env tsx

import { drizzle } from 'drizzle-orm/better-sqlite3';
import Database from 'better-sqlite3';
import path from 'path';
import { boxers, divisions } from './drizzle/schema/index.js';

async function clearStagingData() {
  const dbPath = path.join(__dirname, '../data/output/staging_mirror.db');

  console.log('Clearing staging mirror database...');

  const sqlite = new Database(dbPath);
  const db = drizzle(sqlite);

  // Clear all tables in dependency order
  await db.delete(boxers);  
  console.log('✓ Cleared boxers table');

  await db.delete(divisions);
  console.log('✓ Cleared divisions table');

  console.log('\n✅ Staging mirror database successfully cleared');
  console.log('Please refresh Drizzle Studio to see the changes.');

  sqlite.close();
}

clearStagingData().catch(console.error);