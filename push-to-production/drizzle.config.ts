import type { Config } from 'drizzle-kit';
import * as dotenv from 'dotenv';

dotenv.config({ path: '../.env' });

export default {
  schema: './src/schema/*',
  out: './drizzle',
  driver: 'mysql2',
  dbCredentials: {
    host: process.env.DB_HOST!,
    port: parseInt(process.env.DB_PORT || '3306'),
    user: process.env.DB_USERNAME!,
    password: process.env.DB_PASS!,
    database: process.env.DB_NAME!,
  },
  // Introspect config - pull schema from production
  introspect: {
    casing: 'camel',
  },
} satisfies Config;