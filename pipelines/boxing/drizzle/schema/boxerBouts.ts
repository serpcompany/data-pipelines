import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
import { boxers } from './boxers';

export const boxerBouts = sqliteTable('boxerBouts', {
  id: integer('id').primaryKey({ autoIncrement: true }).notNull(),
  boxerId: text('boxerId').notNull().references(() => boxers.id, { onDelete: 'cascade' }),
  boxrecId: text('boxrecId'),
  boutDate: text('boutDate').notNull(),
  opponentName: text('opponentName').notNull(),
  opponentWeight: text('opponentWeight'),
  opponentRecord: text('opponentRecord'),
  eventName: text('eventName'),
  refereeName: text('refereeName'),
  judge1Name: text('judge1Name'),
  judge1Score: text('judge1Score'),
  judge2Name: text('judge2Name'),
  judge2Score: text('judge2Score'),
  judge3Name: text('judge3Name'),
  judge3Score: text('judge3Score'),
  numRoundsScheduled: integer('numRoundsScheduled'),
  result: text('result').notNull(),
  resultMethod: text('resultMethod'),
  resultRound: integer('resultRound'),
  eventPageLink: text('eventPageLink'),
  boutPageLink: text('boutPageLink'),
  scorecardsPageLink: text('scorecardsPageLink'),
  titleFight: integer('titleFight').default(0), // SQLite uses 0/1 for boolean
  createdAt: text('createdAt').default('CURRENT_TIMESTAMP').notNull(),
});