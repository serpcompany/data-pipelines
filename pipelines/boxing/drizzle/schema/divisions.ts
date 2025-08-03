import { sqliteTable, text, real } from 'drizzle-orm/sqlite-core';

export const divisions = sqliteTable('divisions', {
  id: text('id').primaryKey().notNull(),
  slug: text('slug').notNull(),
  name: text('name').notNull(),
  alternativeNames: text('alternativeNames'),
  weightLimitPounds: real('weightLimitPounds').notNull(),
  weightLimitKilograms: real('weightLimitKilograms').notNull(),
  weightLimitStone: text('weightLimitStone'),
  createdAt: text('createdAt').default('CURRENT_TIMESTAMP').notNull(),
  updatedAt: text('updatedAt').default('CURRENT_TIMESTAMP').notNull(),
});