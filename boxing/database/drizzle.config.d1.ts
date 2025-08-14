import type { Config } from 'drizzle-kit';

export default {
  dialect: 'sqlite',
  driver: 'd1-http',
  schema: './schema/*',
  out: './migrations_d1',
  dbCredentials: {
    accountId: 'cec5f04e1d18bcc65f2be0aefb04f059',
    databaseId: '6b463a07-05a9-4da1-9637-f8331d40b36c',
    token: process.env.CLOUDFLARE_D1_TOKEN || ''
  },
  introspect: {
    casing: 'camel',
  }
} satisfies Config;