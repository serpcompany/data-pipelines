import { config } from 'dotenv';
import { defineConfig } from 'drizzle-kit';

config({ path: '.env' });

export default defineConfig({
  schema: './drizzle/schema/*',
  out: './drizzle/migrations',
  dialect: 'turso',
  dbCredentials: {
    url: process.env.LIBSQL_CONNECTION_URL!,
    authToken: process.env.LIBSQL_AUTH_TOKEN!,
  },
});
