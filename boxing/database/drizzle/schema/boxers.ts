import { sqliteTable, text, integer, index } from 'drizzle-orm/sqlite-core'
import { sql } from 'drizzle-orm'

export const boxers = sqliteTable('boxers', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  boxrecId: text('boxrecId').notNull().unique(),
  boxrecUrl: text('boxrecUrl').notNull().unique(),
  boxrecWikiUrl: text('boxrecWikiUrl'),
  slug: text('slug').notNull().unique(),
  
  name: text('name').notNull(),
  birthName: text('birthName'),
  nicknames: text('nicknames'),
  
  avatarImage: text('avatarImage'),
  
  residence: text('residence'),
  birthPlace: text('birthPlace'),
  dateOfBirth: text('dateOfBirth'),
  gender: text('gender'), // 'M' | 'F'
  nationality: text('nationality'),
  
  height: text('height'), // cm by default
  reach: text('reach'),
  stance: text('stance'), // 'orthodox' | 'southpaw'
  
  bio: text('bio'),
  
  promoters: text('promoters'), // JSON array stored as text
  trainers: text('trainers'), // JSON array stored as text
  managers: text('managers'), // JSON array stored as text
  gym: text('gym'), // TODO: FK to gyms table
  
  proDebutDate: text('proDebutDate'),
  proDivision: text('proDivision'),
  proWins: integer('proWins').notNull().default(0),
  proWinsByKnockout: integer('proWinsByKnockout').notNull().default(0),
  proLosses: integer('proLosses').notNull().default(0),
  proLossesByKnockout: integer('proLossesByKnockout').notNull().default(0),
  proDraws: integer('proDraws').notNull().default(0),
  proStatus: text('proStatus'), // 'active' | 'inactive'
  proTotalBouts: integer('proTotalBouts'),
  proTotalRounds: integer('proTotalRounds'),
  
  amateurDebutDate: text('amateurDebutDate'),
  amateurDivision: text('amateurDivision'),
  amateurWins: integer('amateurWins'),
  amateurWinsByKnockout: integer('amateurWinsByKnockout'),
  amateurLosses: integer('amateurLosses'),
  amateurLossesByKnockout: integer('amateurLossesByKnockout'),
  amateurDraws: integer('amateurDraws'),
  amateurStatus: text('amateurStatus'), // 'active' | 'inactive'
  amateurTotalBouts: integer('amateurTotalBouts'),
  amateurTotalRounds: integer('amateurTotalRounds'),

  bouts: text('bouts', { mode: 'json' }),
  
  createdAt: text('createdAt').notNull().default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text('updatedAt').notNull().default(sql`CURRENT_TIMESTAMP`),
}, (table) => ({
  slugIdx: index('boxersSlugIdx').on(table.slug),
  boxrecIdIdx: index('boxersBoxrecIdIdx').on(table.boxrecId),
  nationalityIdx: index('boxersNationalityIdx').on(table.nationality),
  divisionIdx: index('boxersDivisionIdx').on(table.proDivision),
  statusIdx: index('boxersStatusIdx').on(table.proStatus),
}))