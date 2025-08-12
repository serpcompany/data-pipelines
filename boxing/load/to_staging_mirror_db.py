#!/usr/bin/env python3
"""
Load extracted data from HTML to staging mirror database.
This is the main ETL script that processes HTML files and populates the staging mirror DB.
"""

import json
import logging
import re
import sqlite3
import traceback
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import psycopg2

from ..utils.config import get_postgres_connection, OUTPUT_DIR
from ..database.staging_mirror import get_connection as get_staging_connection
from ..extract.orchestrator import ExtractionOrchestrator
from ..transform import generate_unique_bout_id

logger = logging.getLogger(__name__)

current_dir = Path(__file__).parent.resolve()
parent_dir = current_dir.parent


class StagingLoader:
    """Load extracted boxer data into staging mirror database."""

    def __init__(self):
        self.staging_conn = None
        self.extractor = ExtractionOrchestrator()
        self.bio_data = self._load_bio_data()

    def __enter__(self):
        self.staging_conn = get_staging_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.staging_conn:
            self.staging_conn.close()

    def _load_bio_data(self) -> Dict[str, str]:
        """Load bio data from CSV file."""
        bio_data = {}
        csv_path = parent_dir / "data" / "input" / "boxer-articles.csv"

        if csv_path.exists():
            try:
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        boxrec_id = row.get("boxrec_id", "").strip()
                        bio = row.get("bio", "").strip()
                        if boxrec_id and bio:
                            bio_data[boxrec_id] = bio
                logger.info(f"Loaded {len(bio_data)} boxer bios from CSV")
            except Exception as e:
                logger.error(f"Error loading bio data from CSV: {e}")
        else:
            logger.info("No boxer-articles.csv file found, skipping bio data")

        return bio_data

    def load_boxer(self, boxer_data: Dict[str, Any]) -> bool:
        """Load a single boxer's data into staging mirror database."""
        cursor = self.staging_conn.cursor()

        try:
            # Start transaction
            cursor.execute("BEGIN")

            # Prepare boxer data
            boxer_id = boxer_data.get("boxrec_id", "").replace("/", "-")

            # Get bio from CSV if available, otherwise use extracted bio
            bio = self.bio_data.get(boxer_id, boxer_data.get("bio"))

            # Prepare bouts data for JSON storage BEFORE the INSERT
            bouts = boxer_data.get("bouts", [])
            bouts_json = []

            for i, bout in enumerate(bouts):
                # Generate unique bout ID
                bout_id = generate_unique_bout_id(boxer_id, i)

                # Extract judges information if available
                judges = bout.get("judges", [])
                judge1_name = (
                    judges[0]["name"]
                    if len(judges) > 0 and isinstance(judges[0], dict)
                    else None
                )
                judge1_score = (
                    judges[0]["score"]
                    if len(judges) > 0 and isinstance(judges[0], dict)
                    else None
                )
                judge2_name = (
                    judges[1]["name"]
                    if len(judges) > 1 and isinstance(judges[1], dict)
                    else None
                )
                judge2_score = (
                    judges[1]["score"]
                    if len(judges) > 1 and isinstance(judges[1], dict)
                    else None
                )
                judge3_name = (
                    judges[2]["name"]
                    if len(judges) > 2 and isinstance(judges[2], dict)
                    else None
                )
                judge3_score = (
                    judges[2]["score"]
                    if len(judges) > 2 and isinstance(judges[2], dict)
                    else None
                )

                # Determine if this is a title fight
                is_title_fight = bool(bout.get("titles"))

                # Create bout object for JSON
                bout_obj = {
                    "boxerId": boxer_id,
                    "boxrecId": bout.get("bout_id"),
                    "boutDate": bout.get("date"),
                    "opponentName": bout.get("opponent_name"),
                    "opponentWeight": bout.get("second_boxer_weight"),
                    "opponentRecord": None,
                    "eventName": bout.get("venue"),
                    "refereeName": bout.get("referee"),
                    "judge1Name": judge1_name,
                    "judge1Score": judge1_score,
                    "judge2Name": judge2_name,
                    "judge2Score": judge2_score,
                    "judge3Name": judge3_name,
                    "judge3Score": judge3_score,
                    "numRoundsScheduled": bout.get("rounds"),
                    "result": bout.get("result"),
                    "resultMethod": bout.get("result_type"),
                    "resultRound": None,
                    "eventPageLink": None,
                    "boutPageLink": bout.get("bout_link"),
                    "scorecardsPageLink": None,
                    "titleFight": is_title_fight,
                }
                bouts_json.append(bout_obj)

            # Insert or update boxer with bouts included
            cursor.execute(
                """
                INSERT OR REPLACE INTO boxers (
                    boxrecId, boxrecUrl, boxrecWikiUrl, slug, name,
                    birthName, nicknames, avatarImage, residence, birthPlace,
                    dateOfBirth, gender, nationality, height, reach, stance,
                    bio, promoters, trainers, managers, gym,
                    proDebutDate, proDivision, proWins, proWinsByKnockout,
                    proLosses, proLossesByKnockout, proDraws, proStatus,
                    proTotalBouts, proTotalRounds,
                    amateurDebutDate, amateurDivision, amateurWins, amateurWinsByKnockout,
                    amateurLosses, amateurLossesByKnockout, amateurDraws, amateurStatus,
                    amateurTotalBouts, amateurTotalRounds, bouts,
                    createdAt, updatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    boxer_data.get("boxrec_id"),
                    boxer_data.get("url"),
                    boxer_data.get("wiki_url"),
                    re.sub(r"[^a-z0-9]+", "-", boxer_data["name"].lower()).strip("-"),
                    boxer_data.get("name"),
                    boxer_data.get("birth_name"),
                    (
                        json.dumps(boxer_data.get("nicknames", []))
                        if boxer_data.get("nicknames")
                        else None
                    ),
                    boxer_data.get("avatar_image"),
                    boxer_data.get("residence"),
                    boxer_data.get("birth_place"),
                    boxer_data.get("date_of_birth"),
                    boxer_data.get("gender"),
                    boxer_data.get("nationality"),
                    boxer_data.get("height"),
                    boxer_data.get("reach"),
                    boxer_data.get("stance"),
                    bio,  # Use bio from CSV or extracted
                    (
                        json.dumps(boxer_data.get("promoters", []))
                        if boxer_data.get("promoters")
                        else None
                    ),
                    (
                        json.dumps(boxer_data.get("trainers", []))
                        if boxer_data.get("trainers")
                        else None
                    ),
                    (
                        json.dumps(boxer_data.get("managers", []))
                        if boxer_data.get("managers")
                        else None
                    ),
                    boxer_data.get("gym"),
                    boxer_data.get("debut_date_pro"),  # From pro page extractor
                    boxer_data.get("division_pro"),
                    boxer_data.get("wins_pro", 0),
                    boxer_data.get("ko_wins_pro", 0),
                    boxer_data.get("losses_pro", 0),
                    boxer_data.get("ko_losses_pro", 0),
                    boxer_data.get("draws_pro", 0),
                    boxer_data.get("status_pro"),
                    # Calculate total bouts from wins + losses + draws
                    (
                        (
                            boxer_data.get("wins_pro", 0)
                            + boxer_data.get("losses_pro", 0)
                            + boxer_data.get("draws_pro", 0)
                        )
                        if boxer_data.get("wins_pro") is not None
                        else None
                    ),
                    boxer_data.get("rounds_pro"),
                    boxer_data.get("debut_date_amateur"),
                    boxer_data.get("division_amateur"),
                    boxer_data.get("wins_amateur"),
                    boxer_data.get("ko_wins_amateur"),
                    boxer_data.get("losses_amateur"),
                    boxer_data.get("ko_losses_amateur"),
                    boxer_data.get("draws_amateur"),
                    boxer_data.get("status_amateur"),
                    # Calculate amateur total bouts from wins + losses + draws
                    (
                        (
                            boxer_data.get("wins_amateur", 0)
                            + boxer_data.get("losses_amateur", 0)
                            + boxer_data.get("draws_amateur", 0)
                        )
                        if boxer_data.get("wins_amateur") is not None
                        else None
                    ),
                    boxer_data.get("rounds_amateur"),
                    (
                        json.dumps(bouts_json) if bouts_json else None
                    ),  # Include bouts JSON in INSERT
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )

            # Commit transaction
            cursor.execute("COMMIT")

            logger.info(
                f"Loaded boxer {boxer_data.get('name')} with {len(bouts)} bouts"
            )
            return True

        except Exception as e:
            cursor.execute("ROLLBACK")
            logger.error(
                f"Error loading boxer {boxer_data.get('boxrec_id')}: {e}\n{traceback.format_exc()}"
            )
            return False

    def process_boxer_with_both_records(
        self,
        boxer_id: str,
        pro_url: str,
        pro_html: str,
        amateur_html: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Extract data from both professional and amateur HTML and load to staging."""
        try:
            # Extract professional data (primary record)
            logger.info(f"Extracting professional data for boxer {boxer_id}")
            pro_data = self.extractor.extract_all(pro_html)

            if not pro_data:
                logger.warning(f"No professional data extracted for boxer {boxer_id}")
                return None

            # Add URL and ID to professional data
            pro_data["url"] = pro_url
            pro_data["boxrec_id"] = boxer_id

            # Extract amateur data if available
            if amateur_html:
                logger.info(f"Extracting amateur data for boxer {boxer_id}")
                try:
                    amateur_data = self.extractor.extract_all(amateur_html)

                    if amateur_data:
                        # Merge amateur-specific fields into main data structure
                        # Amateur extractors already have _amateur suffix
                        pro_data.update(amateur_data)

                        # Set flag indicating this boxer has amateur record
                        pro_data["has_amateur_record"] = True
                        logger.info(
                            f"Successfully extracted amateur data for boxer {boxer_id}"
                        )
                    else:
                        logger.warning(
                            f"No amateur data extracted for boxer {boxer_id}"
                        )
                        pro_data["has_amateur_record"] = False

                except Exception as e:
                    logger.error(
                        f"Error extracting amateur data for boxer {boxer_id}: {e}"
                    )
                    pro_data["has_amateur_record"] = False
            else:
                # No amateur HTML provided
                pro_data["has_amateur_record"] = False

            # Load combined data to staging
            success = self.load_boxer(pro_data)

            return pro_data if success else None

        except Exception as e:
            logger.error(f"Error processing boxer {boxer_id}: {e}")
            return None

    def load_from_data_lake(self, limit: Optional[int] = None) -> Dict:
        """Load unprocessed HTML files from data lake to staging."""
        logger.info("Loading data from data lake to staging database")

        # Get Postgres connection
        pg_conn = get_postgres_connection()
        pg_cursor = pg_conn.cursor()

        # Find boxer records not yet in staging
        staging_cursor = self.staging_conn.cursor()
        staging_cursor.execute("SELECT boxrecId FROM boxers")
        existing_ids = {row[0] for row in staging_cursor.fetchall()}

        # Get unprocessed records from data lake (both pro and amateur)
        query = """
            SELECT boxrec_url, boxrec_id, html_file, competition_level
            FROM "data_lake".boxrec
            ORDER BY boxrec_id, competition_level DESC  -- Pro first, then amateur
        """
        if limit:
            query += f" LIMIT {limit}"

        pg_cursor.execute(query)
        all_records = pg_cursor.fetchall()

        # Group by boxer ID to get both pro and amateur HTML
        boxer_records = {}
        for url, boxer_id, html, comp_level in all_records:
            if boxer_id not in boxer_records:
                boxer_records[boxer_id] = {}
            boxer_records[boxer_id][comp_level] = (url, html)

        new_boxers = len([bid for bid in boxer_records if bid not in existing_ids])
        updates = len([bid for bid in boxer_records if bid in existing_ids])
        logger.info(
            f"Found {new_boxers} NEW boxers and {updates} to UPDATE (total: {len(boxer_records)})"
        )

        if not boxer_records:
            return {"processed": 0, "successful": 0, "failed": 0}

        processed = 0
        successful = 0
        failed = 0

        for boxer_id, html_data in boxer_records.items():
            try:
                # Get professional HTML (required)
                if "professional" not in html_data:
                    logger.warning(
                        f"No professional HTML for boxer {boxer_id}, skipping"
                    )
                    continue

                pro_url, pro_html = html_data["professional"]

                # Get amateur HTML (optional)
                amateur_html = None
                if "amateur" in html_data:
                    _, amateur_html = html_data["amateur"]

                # Process and load with both HTML versions
                extracted_data = self.process_boxer_with_both_records(
                    boxer_id=boxer_id,
                    pro_url=pro_url,
                    pro_html=pro_html,
                    amateur_html=amateur_html,
                )

                processed += 1

                if extracted_data:
                    successful += 1
                else:
                    failed += 1

                # Log progress
                if processed % 10 == 0:
                    logger.info(f"Progress: {processed}/{len(boxer_records)} processed")

            except Exception as e:
                logger.error(f"Error processing boxer {boxer_id}: {e}")
                failed += 1

        pg_conn.close()

        summary = {
            "processed": processed,
            "successful": successful,
            "failed": failed,
            "total_unprocessed": len(boxer_records),
        }

        logger.info(f"Loading complete: {summary}")

        return summary

    def get_staging_stats(self) -> Dict:
        """Get statistics about the staging database."""
        cursor = self.staging_conn.cursor()

        stats = {}

        # Count boxers
        cursor.execute("SELECT COUNT(*) FROM boxers")
        stats["total_boxers"] = cursor.fetchone()[0]

        # Count bouts
        cursor.execute(
            "SELECT SUM(json_array_length(bouts)) FROM boxers WHERE bouts IS NOT NULL"
        )
        result = cursor.fetchone()[0]
        stats["total_bouts"] = result if result else 0

        # Count by status
        cursor.execute(
            """
            SELECT proStatus, COUNT(*) 
            FROM boxers 
            WHERE proStatus IS NOT NULL 
            GROUP BY proStatus
        """
        )
        stats["boxers_by_status"] = dict(cursor.fetchall())

        # Count by division
        cursor.execute(
            """
            SELECT proDivision, COUNT(*) 
            FROM boxers 
            WHERE proDivision IS NOT NULL 
            GROUP BY proDivision
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """
        )
        stats["top_divisions"] = dict(cursor.fetchall())

        return stats

    def load_event(self, event_data: Dict[str, Any]) -> bool:
        """Load a single event's data into staging mirror database."""
        cursor = self.staging_conn.cursor()

        try:
            # Start transaction
            cursor.execute("BEGIN")

            # Prepare event data
            boxrec_id = event_data.get("boxrec_id", "")

            # Prepare JSON fields for storage
            bouts = event_data.get("bouts", [])
            bouts_json = json.dumps(bouts) if bouts else None
            promoter_json = (
                json.dumps(event_data.get("promoter"))
                if event_data.get("promoter")
                else None
            )
            matchmaker_json = (
                json.dumps(event_data.get("matchmaker"))
                if event_data.get("matchmaker")
                else None
            )
            inspector_json = (
                json.dumps(event_data.get("inspector"))
                if event_data.get("inspector")
                else None
            )
            doctor_json = (
                json.dumps(event_data.get("doctor"))
                if event_data.get("doctor")
                else None
            )

            # Insert/update event
            upsert_query = """
                INSERT INTO events (
                    boxrecId, eventName, location, commission, promoter, 
                    matchmaker, inspector, doctor, watchLink, bouts,
                    createdAt, updatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(boxrecId) DO UPDATE SET 
                    eventName = EXCLUDED.eventName,
                    location = EXCLUDED.location,
                    commission = EXCLUDED.commission,
                    promoter = EXCLUDED.promoter,
                    matchmaker = EXCLUDED.matchmaker,
                    inspector = EXCLUDED.inspector,
                    doctor = EXCLUDED.doctor,
                    watchLink = EXCLUDED.watchLink,
                    bouts = EXCLUDED.bouts,
                    updatedAt = EXCLUDED.updatedAt
            """

            cursor.execute(
                upsert_query,
                (
                    boxrec_id,
                    event_data.get("event_name"),
                    event_data.get("location"),
                    event_data.get("commission"),
                    promoter_json,
                    matchmaker_json,
                    inspector_json,
                    doctor_json,
                    event_data.get("watch_link"),
                    bouts_json,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )

            # Commit transaction
            cursor.execute("COMMIT")
            logger.info(f"Successfully loaded event {boxrec_id}")
            return True

        except Exception as e:
            cursor.execute("ROLLBACK")
            logger.error(f"Error loading event {boxrec_id}: {e}")
            logger.error(traceback.format_exc())
            return False

    def load_bout(self, bout_data: Dict[str, Any]) -> bool:
        """Load a single bout's data into staging mirror database."""
        cursor = self.staging_conn.cursor()

        try:
            # Start transaction
            cursor.execute("BEGIN")

            # Prepare bout data
            event_id = bout_data.get("boxrec_event_id", "")
            bout_id = bout_data.get("boxrec_bout_id", "")

            # Prepare JSON fields
            titles_json = (
                json.dumps(bout_data.get("titles", []))
                if bout_data.get("titles")
                else None
            )
            scorecards_json = (
                json.dumps(bout_data.get("scorecards", []))
                if bout_data.get("scorecards")
                else None
            )
            judges_json = (
                json.dumps(bout_data.get("judges", []))
                if bout_data.get("judges")
                else None
            )
            boxer_a_side_json = (
                json.dumps(bout_data.get("boxer_a_side"))
                if bout_data.get("boxer_a_side")
                else None
            )
            boxer_b_side_json = (
                json.dumps(bout_data.get("boxer_b_side"))
                if bout_data.get("boxer_b_side")
                else None
            )
            referee_json = (
                json.dumps(bout_data.get("referee"))
                if bout_data.get("referee")
                else None
            )
            promoter_json = (
                json.dumps(bout_data.get("promoter"))
                if bout_data.get("promoter")
                else None
            )
            matchmaker_json = (
                json.dumps(bout_data.get("matchmaker"))
                if bout_data.get("matchmaker")
                else None
            )
            inspector_json = (
                json.dumps(bout_data.get("inspector"))
                if bout_data.get("inspector")
                else None
            )
            doctor_json = (
                json.dumps(bout_data.get("doctor"))
                if bout_data.get("doctor")
                else None
            )

            # Insert/update bout
            upsert_query = """
                INSERT INTO bouts (
                    boxrecEventId, boxrecBoutId, boxerASide, boxerBSide,
                    boutDivision, boutRoundsScheduled, titles, boutResult,
                    boutResultMethod, boutRoundsActual, scorecards, stoppageReason,
                    referee, judges, promoter, matchmaker, inspector, doctor,
                    boxerASideRating, boxerASideRecord, boxerASideAge, boxerASideStance,
                    boxerASideHeight, boxerASideReach,
                    boxerBSideRating, boxerBSideRecord, boxerBSideAge, boxerBSideStance,
                    boxerBSideHeight, boxerBSideReach,
                    competitionLevel, createdAt, updatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(boxrecEventId, boxrecBoutId) DO UPDATE SET 
                    boxerASide = EXCLUDED.boxerASide,
                    boxerBSide = EXCLUDED.boxerBSide,
                    boutDivision = EXCLUDED.boutDivision,
                    boutRoundsScheduled = EXCLUDED.boutRoundsScheduled,
                    titles = EXCLUDED.titles,
                    boutResult = EXCLUDED.boutResult,
                    boutResultMethod = EXCLUDED.boutResultMethod,
                    boutRoundsActual = EXCLUDED.boutRoundsActual,
                    scorecards = EXCLUDED.scorecards,
                    stoppageReason = EXCLUDED.stoppageReason,
                    referee = EXCLUDED.referee,
                    judges = EXCLUDED.judges,
                    promoter = EXCLUDED.promoter,
                    matchmaker = EXCLUDED.matchmaker,
                    inspector = EXCLUDED.inspector,
                    doctor = EXCLUDED.doctor,
                    boxerASideRating = EXCLUDED.boxerASideRating,
                    boxerASideRecord = EXCLUDED.boxerASideRecord,
                    boxerASideAge = EXCLUDED.boxerASideAge,
                    boxerASideStance = EXCLUDED.boxerASideStance,
                    boxerASideHeight = EXCLUDED.boxerASideHeight,
                    boxerASideReach = EXCLUDED.boxerASideReach,
                    boxerBSideRating = EXCLUDED.boxerBSideRating,
                    boxerBSideRecord = EXCLUDED.boxerBSideRecord,
                    boxerBSideAge = EXCLUDED.boxerBSideAge,
                    boxerBSideStance = EXCLUDED.boxerBSideStance,
                    boxerBSideHeight = EXCLUDED.boxerBSideHeight,
                    boxerBSideReach = EXCLUDED.boxerBSideReach,
                    competitionLevel = EXCLUDED.competitionLevel,
                    updatedAt = EXCLUDED.updatedAt
            """

            cursor.execute(
                upsert_query,
                (
                    event_id,
                    bout_id,
                    boxer_a_side_json,
                    boxer_b_side_json,
                    bout_data.get("bout_division"),
                    bout_data.get("bout_rounds_scheduled"),
                    titles_json,
                    bout_data.get("bout_result"),
                    bout_data.get("bout_result_method"),
                    bout_data.get("bout_rounds_actual"),
                    scorecards_json,
                    bout_data.get("stoppage_reason"),
                    referee_json,
                    judges_json,
                    promoter_json,
                    matchmaker_json,
                    inspector_json,
                    doctor_json,
                    bout_data.get("boxer_a_side_rating"),
                    bout_data.get("boxer_a_side_record"),
                    bout_data.get("boxer_a_side_age"),
                    bout_data.get("boxer_a_side_stance"),
                    bout_data.get("boxer_a_side_height"),
                    bout_data.get("boxer_a_side_reach"),
                    bout_data.get("boxer_b_side_rating"),
                    bout_data.get("boxer_b_side_record"),
                    bout_data.get("boxer_b_side_age"),
                    bout_data.get("boxer_b_side_stance"),
                    bout_data.get("boxer_b_side_height"),
                    bout_data.get("boxer_b_side_reach"),
                    bout_data.get("competition_level", "professional"),
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )

            # Commit transaction
            cursor.execute("COMMIT")
            logger.info(f"Successfully loaded bout {event_id}_{bout_id}")
            return True

        except Exception as e:
            cursor.execute("ROLLBACK")
            logger.error(f"Error loading bout {event_id}_{bout_id}: {e}")
            logger.error(traceback.format_exc())
            return False

    def process_event_with_html(
        self, event_id: str, event_url: str, html_content: str
    ) -> Optional[Dict[str, Any]]:
        """Process event HTML and extract data."""
        from ..extract.event_orchestrator import EventExtractionOrchestrator

        try:
            # Extract event data
            extractor = EventExtractionOrchestrator()
            event_data = extractor.extract_event_data(html_content)
            event_data["boxrec_id"] = event_id
            event_data["boxrec_url"] = event_url

            # Load to staging
            success = self.load_event(event_data)
            return event_data if success else None

        except Exception as e:
            logger.error(f"Error processing event {event_id}: {e}")
            return None

    def process_bout_with_html(
        self, event_id: str, bout_id: str, bout_url: str, html_content: str
    ) -> Optional[Dict[str, Any]]:
        """Process bout HTML and extract data."""
        from ..extract.event_orchestrator import EventExtractionOrchestrator

        try:
            # Extract bout data
            extractor = EventExtractionOrchestrator()
            bout_data = extractor.extract_bout_data(html_content, event_id, bout_id)
            bout_data["boxrec_url"] = bout_url

            # Load to staging
            success = self.load_bout(bout_data)
            return bout_data if success else None

        except Exception as e:
            logger.error(f"Error processing bout {event_id}_{bout_id}: {e}")
            return None


def run_staging_load(limit: Optional[int] = None):
    """Run the staging load process."""
    logger.info("Starting staging load process")

    with StagingLoader() as loader:
        # Load from data lake
        summary = loader.load_from_data_lake(limit=limit)

        # Get final stats
        stats = loader.get_staging_stats()

        logger.info(f"Staging database stats: {stats}")

        return {"load_summary": summary, "staging_stats": stats}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test loading with a small batch
    result = run_staging_load(limit=5)

    print("\nStaging Load Results:")
    print(json.dumps(result, indent=2))
