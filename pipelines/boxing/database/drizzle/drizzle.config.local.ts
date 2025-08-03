import type { Config } from 'drizzle-kit';
import path from 'path';

// For local staging mirror database
export default {
  dialect: 'sqlite',
  schema: path.join(__dirname, './schema/index.ts'),
  out: path.join(__dirname, './migrations'),
  dbCredentials: {
    url: path.join(__dirname, '../../data/output/staging_mirror.db')
  }
} satisfies Config;