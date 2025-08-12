#!/usr/bin/env python3
"""Load validated HTML files to Postgres data lake."""

import os
import psycopg2
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging
from ..utils.config import VALIDATED_HTML_DIR, LOG_DIR
from ..transform import normalize_boxer_id

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "data_lake_loader.log"),
        logging.StreamHandler(),
    ],
)

# Load database credentials from environment
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DEFAULT_DB"),
}


def extract_boxer_id_from_filename(filename: str) -> Optional[str]:
    """Extract boxer ID from filename like 'en_box-pro_123456.html' or 'en_box-am_123456.html'."""
    parts = filename.replace(".html", "").split("_")
    if len(parts) >= 3 and ("box-pro" in parts[1] or "box-am" in parts[1]):
        # Extract only the numeric part of the ID
        boxer_id_part = parts[-1]
        # Find the first non-digit character and take everything before it
        numeric_id = ""
        for char in boxer_id_part:
            if char.isdigit():
                numeric_id += char
            else:
                break
        if numeric_id:
            # Apply transformation to normalize the ID
            return normalize_boxer_id(numeric_id)
        return None
    return None


def construct_boxrec_url(filename: str) -> Optional[str]:
    """Construct BoxRec URL from filename."""
    parts = filename.replace(".html", "").split("_")
    if len(parts) >= 3:
        lang = parts[0]
        page_type = parts[1]  # box-pro or box-am
        boxer_id = parts[-1]
        if page_type in ["box-pro", "box-am"]:
            return f"https://boxrec.com/{lang}/{page_type}/{boxer_id}"
    return None


def get_competition_level(filename: str) -> str:
    """Determine competition level from filename."""
    if "box-am" in filename:
        return "amateur"
    return "professional"


def prepare_file_data(html_file: Path) -> Optional[dict]:
    """Prepare data from a single HTML file for database insertion."""
    try:
        # Read HTML content
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Extract metadata from filename
        filename = html_file.name
        boxer_id = extract_boxer_id_from_filename(filename)
        boxrec_url = construct_boxrec_url(filename)
        competition_level = get_competition_level(filename)

        if not boxer_id or not boxrec_url:
            logging.warning(f"Could not extract metadata from {filename}")
            return None

        return {
            "boxer_id": boxer_id,
            "boxrec_url": boxrec_url,
            "html_content": html_content,
            "competition_level": competition_level,
            "filename": filename,
        }
    except Exception as e:
        logging.error(f"Error preparing {html_file.name}: {e}")
        return None


def load_all_validated_files(batch_size: int = 100):
    """Load all validated HTML files to the data lake using batch processing."""
    html_files = list(VALIDATED_HTML_DIR.glob("*.html"))

    if not html_files:
        logging.info("No validated HTML files found")
        return

    logging.info(f"Found {len(html_files)} validated HTML files")
    logging.info(f"Processing in batches of {batch_size}")

    # Prepare all file data first
    file_data = []
    for html_file in html_files:
        data = prepare_file_data(html_file)
        if data:
            file_data.append(data)

    if not file_data:
        logging.error("No valid files to process")
        return

    # Connect to database once
    conn = None
    cur = None
    success_count = 0

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Process in batches
        for i in range(0, len(file_data), batch_size):
            batch = file_data[i : i + batch_size]

            # Prepare batch data for UPSERT
            batch_values = []
            for data in batch:
                batch_values.append(
                    (
                        data["boxrec_url"],
                        data["boxer_id"],
                        data["html_content"],
                        data["competition_level"],
                        datetime.now(),
                        datetime.now(),
                        datetime.now(),
                    )
                )

            # Use INSERT ... ON CONFLICT DO UPDATE for efficient UPSERT
            # This assumes there's a unique constraint on (boxrec_id, competition_level)
            upsert_query = """
                INSERT INTO "data_lake".boxrec_boxer_raw_html 
                (boxrec_url, boxrec_id, html_file, competition_level, scraped_at, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (boxrec_id, competition_level) 
                DO UPDATE SET 
                    html_file = EXCLUDED.html_file,
                    boxrec_url = EXCLUDED.boxrec_url,
                    scraped_at = EXCLUDED.scraped_at,
                    updated_at = EXCLUDED.updated_at
            """

            # Execute batch upsert
            cur.executemany(upsert_query, batch_values)
            rows_affected = cur.rowcount
            success_count += len(batch)

            # Commit after each batch
            conn.commit()
            logging.info(
                f"Processed batch {i//batch_size + 1}/{(len(file_data) + batch_size - 1)//batch_size} - {rows_affected} rows affected"
            )

        logging.info(
            f"Successfully processed {success_count}/{len(file_data)} files to data lake"
        )

    except Exception as e:
        logging.error(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    # Run the loader
    load_all_validated_files()
