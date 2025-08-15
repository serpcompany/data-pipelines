import { sqliteTable, text } from 'drizzle-orm/sqlite-core'
import { sql } from 'drizzle-orm'

export const syncJobs = sqliteTable('sync_jobs', {
  name: text('name').primaryKey(),
  lastSyncTimestamp: text('last_sync_timestamp').notNull().default(sql`(datetime('now'))`),
})