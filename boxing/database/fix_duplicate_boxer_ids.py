#!/usr/bin/env python3
"""Fix duplicate boxer IDs by removing entries with leading zeros."""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from boxing.transform import normalize_boxer_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_duplicate_boxer_ids_in_data_lake():
    """Remove duplicate boxer IDs with leading zeros from data lake."""
    import psycopg2
    import os

    DB_CONFIG = {
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "database": os.getenv("POSTGRES_DEFAULT_DB"),
    }

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Find all IDs with leading zeros
        cursor.execute(
            """
            SELECT DISTINCT boxrec_id, competition_level
            FROM "data_lake".boxrec 
            WHERE boxrec_id ~ '^0+[0-9]+$'
        """
        )

        ids_with_zeros = cursor.fetchall()
        logger.info(f"Found {len(ids_with_zeros)} boxer IDs with leading zeros")

        deleted_count = 0
        kept_count = 0

        for boxer_id, competition_level in ids_with_zeros:
            normalized = normalize_boxer_id(boxer_id)

            # Check if normalized version exists
            cursor.execute(
                """
                SELECT COUNT(*) 
                FROM "data_lake".boxrec 
                WHERE boxrec_id = %s AND competition_level = %s
            """,
                (normalized, competition_level),
            )

            if cursor.fetchone()[0] > 0:
                # Normalized version exists, delete the one with zeros
                logger.info(f"Deleting duplicate: {boxer_id} (keeping {normalized})")
                cursor.execute(
                    """
                    DELETE FROM "data_lake".boxrec 
                    WHERE boxrec_id = %s AND competition_level = %s
                """,
                    (boxer_id, competition_level),
                )
                deleted_count += 1
            else:
                # No normalized version, keep this one but fix the ID
                logger.info(f"Keeping and normalizing: {boxer_id} -> {normalized}")
                cursor.execute(
                    """
                    UPDATE "data_lake".boxrec 
                    SET boxrec_id = %s 
                    WHERE boxrec_id = %s AND competition_level = %s
                """,
                    (normalized, boxer_id, competition_level),
                )
                kept_count += 1

        conn.commit()
        logger.info(
            f"Deleted {deleted_count} duplicates, normalized {kept_count} unique records"
        )

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error fixing duplicate IDs: {e}")
        raise


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    logger.info("Fixing duplicate boxer IDs in data lake...")
    fix_duplicate_boxer_ids_in_data_lake()
    logger.info("Done!")
