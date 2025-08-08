CREATE TABLE `boxers` (
	`id` text PRIMARY KEY NOT NULL,
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
CREATE TABLE `divisions` (
	`id` text PRIMARY KEY NOT NULL,
	`slug` text NOT NULL,
	`name` text NOT NULL,
	`short_name` text,
	`alternative_names` text,
	`weight_limit_pounds` real NOT NULL,
	`weight_limit_kilograms` real NOT NULL,
	`weight_limit_stone` text,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
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
CREATE UNIQUE INDEX `divisions_slug_unique` ON `divisions` (`slug`);--> statement-breakpoint
CREATE INDEX `divisions_slug_idx` ON `divisions` (`slug`);--> statement-breakpoint
CREATE INDEX `divisions_short_name_idx` ON `divisions` (`short_name`);