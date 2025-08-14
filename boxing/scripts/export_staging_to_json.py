#!/usr/bin/env python3
"""
Export Staging Data to JSON Script

Exports data from staging SQLite/libsql database tables to JSON files.
Supports boxers, events, and bouts entities.

Usage:
    python export_staging_to_json.py --entity boxer --limit 100 --output my_boxers.json
    python export_staging_to_json.py --entity event
    python export_staging_to_json.py --entity bout --limit 50
"""

import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path to import boxing modules
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.staging_mirror import get_connection as get_staging_connection

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def export_data_to_json(
    entity: str, limit: int = None, output_filename: str = None
) -> Dict[str, Any]:
    """Export staging data to JSON file."""

    # Determine table name
    if entity.lower() in ["boxer", "boxers"]:
        table_name = "boxers"
        entity = "boxer"
    elif entity.lower() in ["event", "events"]:
        table_name = "events"
        entity = "event"
    elif entity.lower() in ["bout", "bouts", "fight", "fights"]:
        table_name = "bouts"
        entity = "bout"
    else:
        raise ValueError(f"Unsupported entity type: {entity}")

    # Connect to staging database
    logger.info(f"Connecting to staging database...")
    staging_conn = get_staging_connection()
    cursor = staging_conn.cursor()

    # Check total records
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_records = cursor.fetchone()[0]

    if total_records == 0:
        staging_conn.close()
        return {
            "status": "skipped",
            "message": f"No {entity} records found in staging database",
            "records_exported": 0,
            "file_path": None,
        }

    logger.info(f"Found {total_records} {entity} records in staging database")

    # Build query with optional limit
    query = f"SELECT * FROM {table_name} ORDER BY createdAt"
    if limit:
        query += f" LIMIT {int(limit)}"
        logger.info(f"Limiting export to {limit} records")

    cursor.execute(query)
    raw_rows = cursor.fetchall()

    # Convert rows to dictionaries manually
    columns = [desc[0] for desc in cursor.description]
    rows = [dict(zip(columns, row)) for row in raw_rows]
    staging_conn.close()

    logger.info(f"Retrieved {len(rows)} records from database")

    # Process rows to handle JSON fields
    processed_rows = []
    for row in rows:
        processed_row = {}
        for key, value in row.items():
            # Try to parse JSON fields
            if value and isinstance(value, str):
                # Common JSON field names
                json_fields = [
                    "bouts",
                    "promoters",
                    "trainers",
                    "managers",
                    "titles",
                    "scorecards",
                    "judges",
                    "promoter",
                    "matchmaker",
                    "inspector",
                    "doctor",
                    "referee",
                    "boxerASide",
                    "boxerBSide",
                ]
                if key in json_fields:
                    try:
                        processed_row[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        processed_row[key] = value
                else:
                    processed_row[key] = value
            else:
                processed_row[key] = value
        processed_rows.append(processed_row)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if output_filename:
        filename = (
            output_filename
            if output_filename.endswith(".json")
            else f"{output_filename}.json"
        )
    else:
        filename = f"{entity}_export_{timestamp}.json"
        if limit:
            filename = f"{entity}_export_{timestamp}_limit_{limit}.json"

    # Use current directory as output
    file_path = Path.cwd() / filename

    logger.info(f"Writing {len(processed_rows)} records to {file_path}")

    # Write JSON file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(processed_rows, f, indent=2, ensure_ascii=False, default=str)

    file_size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)

    return {
        "status": "success",
        "entity": entity,
        "records_exported": len(processed_rows),
        "total_available": total_records,
        "file_path": str(file_path),
        "filename": filename,
        "file_size_mb": file_size_mb,
    }


def main():
    parser = argparse.ArgumentParser(description="Export staging database data to JSON")
    parser.add_argument(
        "--entity",
        required=True,
        choices=[
            "boxer",
            "boxers",
            "event",
            "events",
            "bout",
            "bouts",
            "fight",
            "fights",
        ],
        help="Entity type to export",
    )
    parser.add_argument("--limit", type=int, help="Limit number of records to export")
    parser.add_argument("--output", help="Output filename (without .json extension)")

    args = parser.parse_args()

    try:
        result = export_data_to_json(
            entity=args.entity, limit=args.limit, output_filename=args.output
        )

        print("\n" + "=" * 60)
        print("JSON EXPORT REPORT")
        print("=" * 60)
        print(f"Entity: {result.get('entity', 'N/A')}")
        print(f"Total records in staging: {result.get('total_available', 'N/A')}")

        if result["status"] == "success":
            print(f"Records exported: {result['records_exported']}")
            print(f"Output file: {result['filename']}")
            print(f"File size: {result['file_size_mb']} MB")
            print(f"Full path: {result['file_path']}")

            if result["records_exported"] < result["total_available"]:
                print(
                    f"Note: Limited export ({result['records_exported']}/{result['total_available']} records)"
                )
        else:
            print(f"Export skipped: {result.get('message', 'Unknown error')}")

        print("=" * 60)

    except Exception as e:
        logger.error(f"Export failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
