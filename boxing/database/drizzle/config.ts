import type { Config } from 'drizzle-kit';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config({ path: '../../.env' });

export default {
  schema: './schema/*',
  out: './migrations',
  driver: 'better-sqlite',
  dbCredentials: {
    url: './staging.db', // Local SQLite file for staging
  },
} satisfies Config;

// For D1 production/preview
export const d1Config = {
  schema: './schema/*',
  out: './migrations',
  driver: 'd1',
  dbCredentials: {
    wranglerConfigPath: '../wrangler.toml',
    dbName: 'boxingundefeated-com',
  },
} satisfies Config;