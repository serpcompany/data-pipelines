import type { Config } from 'drizzle-kit';

// For local staging mirror database
export default {
  dialect: 'sqlite',
  schema: './drizzle/schema/index.ts',
  out: './drizzle/migrations',
  dbCredentials: {
    url: '../data/output/staging_mirror.db'
  },
   introspect: {
    casing: 'camel',
  },
} satisfies Config;