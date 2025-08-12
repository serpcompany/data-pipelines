#!/usr/bin/env python3
"""Batch load validated HTML files to Postgres data lake."""

import os
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
import logging
from ..utils.config import VALIDATED_HTML_DIR, LOG_DIR
from ..transform import normalize_boxer_id

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "data_lake_batch_loader.log"),
        logging.StreamHandler(),
    ],
)

# Database config
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DEFAULT_DB"),
}

BATCH_SIZE = 100


def extract_metadata(filename: str) -> Tuple[str, str, str]:
    """Extract boxer_id, url, and competition level from filename."""
    parts = filename.replace(".html", "").split("_")

    # Extract boxer ID and normalize it
    boxer_id_raw = parts[-1]
    # Extract only numeric part (handle cases like "872853.html" or "11677.sometext")
    numeric_id = ""
    for char in boxer_id_raw:
        if char.isdigit():
            numeric_id += char
        else:
            break

    boxer_id = normalize_boxer_id(numeric_id) if numeric_id else None
    if not boxer_id:
        raise ValueError(f"Could not extract boxer ID from {filename}")

    # Construct URL
    lang = parts[0] if parts else "en"
    page_type = parts[1] if len(parts) > 1 else "box-pro"
    url = f"https://boxrec.com/{lang}/{page_type}/{boxer_id}"

    # Competition level
    level = "amateur" if "box-am" in filename else "professional"

    return boxer_id, url, level


def load_batch_to_data_lake():
    """Load all validated HTML files in batches."""
    html_files = list(VALIDATED_HTML_DIR.glob("*.html"))

    if not html_files:
        logging.info("No validated HTML files found")
        return

    logging.info(f"Found {len(html_files)} validated HTML files")

    # Connect once
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Load existing IDs to check for duplicates
    cur.execute(
        """
        SELECT boxrec_id, competition_level 
        FROM "data_lake".boxrec
    """
    )
    existing = set((row[0], row[1]) for row in cur.fetchall())
    logging.info(f"Found {len(existing)} existing records")

    # Prepare batch data
    batch_data = []
    success_count = 0

    for html_file in html_files:
        try:
            with open(html_file, "r", encoding="utf-8") as f:
                html_content = f.read()

            boxer_id, url, level = extract_metadata(html_file.name)

            # Skip if exists
            if (boxer_id, level) in existing:
                continue

            batch_data.append(
                (
                    url,
                    boxer_id,
                    html_content,
                    level,
                    datetime.now(),
                    datetime.now(),
                    datetime.now(),
                )
            )

            # Insert batch when full
            if len(batch_data) >= BATCH_SIZE:
                execute_values(
                    cur,
                    """
                    INSERT INTO "data_lake".boxrec 
                    (boxrec_url, boxrec_id, html_file, competition_level, 
                     scraped_at, created_at, updated_at)
                    VALUES %s
                    """,
                    batch_data,
                )
                conn.commit()
                success_count += len(batch_data)
                logging.info(
                    f"Inserted batch of {len(batch_data)}, total: {success_count}"
                )
                batch_data = []

        except Exception as e:
            logging.error(f"Error processing {html_file.name}: {e}")

    # Insert remaining batch
    if batch_data:
        execute_values(
            cur,
            """
            INSERT INTO "data_lake".boxrec 
            (boxrec_url, boxrec_id, html_file, competition_level, 
             scraped_at, created_at, updated_at)
            VALUES %s
            """,
            batch_data,
        )
        conn.commit()
        success_count += len(batch_data)

    cur.close()
    conn.close()

    logging.info(f"Successfully loaded {success_count} new files to data lake")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    # Run the batch loader
    load_batch_to_data_lake()
