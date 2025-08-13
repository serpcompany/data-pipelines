import { sqliteTable, text, index, unique } from 'drizzle-orm/sqlite-core'
import { sql } from 'drizzle-orm'

export const events = sqliteTable('events', {
  boxrecId: text('boxrecId').notNull().unique(),

  eventName: text('eventName'),
  location: text('location'),
  commission: text('commission'),
  promoter: text('promoter', { mode: 'json' }),
  matchmaker: text('matchmaker', { mode: 'json' }),
  inspector: text('inspector', { mode: 'json' }),
  doctor: text('doctor', { mode: 'json' }),
  watchLink: text('watchLink'),

  bouts: text('bouts', { mode: 'json' }),

  createdAt: text('createdAt').notNull().default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text('updatedAt').notNull().default(sql`CURRENT_TIMESTAMP`),
})

export const bouts = sqliteTable('bouts', {
  boxrecEventId: text('boxrecEventId').notNull(),
  boxrecBoutId: text('boxrecBoutId').notNull(),

  boutDivision: text('boutDivision'),
  boutRoundsScheduled: text('boutRoundsScheduled'),
  titles: text('titles', { mode: 'json' }),

  boutResult: text('boutResult'),
  boutResultMethod: text('boutResultMethod'),
  boutRoundsActual: text('boutRoundsActual'),
  scorecards: text('scorecards', { mode: 'json' }),
  stoppageReason: text('stoppageReason'),

  referee: text('referee', { mode: 'json' }),
  judges: text('judges', { mode: 'json' }),
  promoter: text('promoter', { mode: 'json' }),
  matchmaker: text('matchmaker', { mode: 'json' }),
  inspector: text('inspector', { mode: 'json' }),
  doctor: text('doctor', { mode: 'json' }),

  boxerASide: text('boxerASide', { mode: 'json' }),
  boxerBSide: text('boxerBSide', { mode: 'json' }),

  boxerASideRating: text('boxerASideRating'),
  boxerASideRecord: text('boxerASideRecord'),
  boxerASideAge: text('boxerASideAge'),
  boxerASideStance: text('boxerASideStance'),
  boxerASideHeight: text('boxerASideHeight'),
  boxerASideReach: text('boxerASideReach'),

  boxerBSideRating: text('boxerBSideRating'),
  boxerBSideRecord: text('boxerBSideRecord'),
  boxerBSideAge: text('boxerBSideAge'),
  boxerBSideStance: text('boxerBSideStance'),
  boxerBSideHeight: text('boxerBSideHeight'),
  boxerBSideReach: text('boxerBSideReach'),

  competitionLevel: text('competitionLevel'),

  createdAt: text('createdAt').notNull().default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text('updatedAt').notNull().default(sql`CURRENT_TIMESTAMP`),
}, (table) => ({
  // Unique constraint on event_id + bout_id combination
  eventBoutUnique: unique('boutsEventBoutUniqueIdx').on(table.boxrecEventId, table.boxrecBoutId),
}))