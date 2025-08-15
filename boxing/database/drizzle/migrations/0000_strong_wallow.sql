CREATE TABLE `boxers` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`boxrecId` text NOT NULL,
	`boxrecUrl` text NOT NULL,
	`boxrecWikiUrl` text,
	`slug` text NOT NULL,
	`name` text NOT NULL,
	`birthName` text,
	`nicknames` text,
	`avatarImage` text,
	`residence` text,
	`birthPlace` text,
	`dateOfBirth` text,
	`gender` text,
	`nationality` text,
	`height` text,
	`reach` text,
	`stance` text,
	`bio` text,
	`promoters` text,
	`trainers` text,
	`managers` text,
	`gym` text,
	`proDebutDate` text,
	`proDivision` text,
	`proWins` integer DEFAULT 0 NOT NULL,
	`proWinsByKnockout` integer DEFAULT 0 NOT NULL,
	`proLosses` integer DEFAULT 0 NOT NULL,
	`proLossesByKnockout` integer DEFAULT 0 NOT NULL,
	`proDraws` integer DEFAULT 0 NOT NULL,
	`proStatus` text,
	`proTotalBouts` integer,
	`proTotalRounds` integer,
	`amateurDebutDate` text,
	`amateurDivision` text,
	`amateurWins` integer,
	`amateurWinsByKnockout` integer,
	`amateurLosses` integer,
	`amateurLossesByKnockout` integer,
	`amateurDraws` integer,
	`amateurStatus` text,
	`amateurTotalBouts` integer,
	`amateurTotalRounds` integer,
	`bouts` text,
	`createdAt` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updatedAt` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `boxers_boxrecId_unique` ON `boxers` (`boxrecId`);--> statement-breakpoint
CREATE UNIQUE INDEX `boxers_boxrecUrl_unique` ON `boxers` (`boxrecUrl`);--> statement-breakpoint
CREATE UNIQUE INDEX `boxers_slug_unique` ON `boxers` (`slug`);--> statement-breakpoint
CREATE INDEX `boxersSlugIdx` ON `boxers` (`slug`);--> statement-breakpoint
CREATE INDEX `boxersBoxrecIdIdx` ON `boxers` (`boxrecId`);--> statement-breakpoint
CREATE INDEX `boxersNationalityIdx` ON `boxers` (`nationality`);--> statement-breakpoint
CREATE INDEX `boxersDivisionIdx` ON `boxers` (`proDivision`);--> statement-breakpoint
CREATE INDEX `boxersStatusIdx` ON `boxers` (`proStatus`);--> statement-breakpoint
CREATE TABLE `divisions` (
	`id` text PRIMARY KEY NOT NULL,
	`slug` text NOT NULL,
	`name` text NOT NULL,
	`shortName` text,
	`alternativeNames` text,
	`weightLimitPounds` real NOT NULL,
	`weightLimitKilograms` real NOT NULL,
	`weightLimitStone` text,
	`createdAt` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updatedAt` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `divisions_slug_unique` ON `divisions` (`slug`);--> statement-breakpoint
CREATE INDEX `divisionsSlugIdx` ON `divisions` (`slug`);--> statement-breakpoint
CREATE INDEX `divisionsShortNameIdx` ON `divisions` (`shortName`);--> statement-breakpoint
CREATE TABLE `bouts` (
	`boxrecEventId` text NOT NULL,
	`boxrecBoutId` text NOT NULL,
	`boutDivision` text,
	`boutRoundsScheduled` text,
	`titles` text,
	`boutResult` text,
	`boutResultMethod` text,
	`boutRoundsActual` text,
	`scorecards` text,
	`stoppageReason` text,
	`referee` text,
	`judges` text,
	`promoter` text,
	`matchmaker` text,
	`inspector` text,
	`doctor` text,
	`boxerASide` text,
	`boxerBSide` text,
	`boxerASideRating` text,
	`boxerASideRecord` text,
	`boxerASideAge` text,
	`boxerASideStance` text,
	`boxerASideHeight` text,
	`boxerASideReach` text,
	`boxerBSideRating` text,
	`boxerBSideRecord` text,
	`boxerBSideAge` text,
	`boxerBSideStance` text,
	`boxerBSideHeight` text,
	`boxerBSideReach` text,
	`competitionLevel` text,
	`createdAt` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updatedAt` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `boutsEventBoutUniqueIdx` ON `bouts` (`boxrecEventId`,`boxrecBoutId`);--> statement-breakpoint
CREATE TABLE `events` (
	`boxrecId` text NOT NULL,
	`eventName` text,
	`location` text,
	`commission` text,
	`promoter` text,
	`matchmaker` text,
	`inspector` text,
	`doctor` text,
	`watchLink` text,
	`bouts` text,
	`createdAt` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updatedAt` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `events_boxrecId_unique` ON `events` (`boxrecId`);--> statement-breakpoint
CREATE TABLE `sync_jobs` (
	`name` text PRIMARY KEY NOT NULL,
	`last_sync_timestamp` text DEFAULT (datetime('now')) NOT NULL
);
