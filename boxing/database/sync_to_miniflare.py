#!/usr/bin/env python3
"""
Sync staging_mirror.db to local miniflare D1 database
"""

import sqlite3
import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path to import boxing modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.staging_mirror import get_connection as get_staging_connection

# Configuration
DEFAULT_MINIFLARE_DB = Path(
    "/Users/devin/repos/projects/boxingundefeated.com/.data/hub/d1/miniflare-D1DatabaseObject/7b8799eb95f0bb5448e259812996a461ce40142dacbdea254ea597e307767f45.sqlite"
)


def sync_databases(miniflare_db_path: Path = None):
    """Sync data from staging_mirror.db to miniflare D1 database"""

    if miniflare_db_path is None:
        miniflare_db_path = DEFAULT_MINIFLARE_DB

    # Check if target database exists
    if not miniflare_db_path.exists():
        print(f"Error: Target miniflare database not found at {miniflare_db_path}")
        sys.exit(1)

    print(f"Starting sync from staging to miniflare D1 at {miniflare_db_path}...")

    # Connect to target database
    target_conn = sqlite3.connect(miniflare_db_path)

    try:
        target_cursor = target_conn.cursor()

        # Tables to sync
        tables = ["boxers", "divisions", "bouts"]

        for table in tables:
            # Create fresh connection for each table to avoid timeout
            source_conn = get_staging_connection()
            source_cursor = source_conn.cursor()
            print(f"\nSyncing {table} table...")

            # Clear existing data in target
            target_cursor.execute(f"DELETE FROM {table}")
            print(f"  Cleared existing {table} data")

            # Get column names
            source_cursor.execute(f"PRAGMA table_info(`{table}`)")
            columns = [col[1] for col in source_cursor.fetchall()]

            # Get data from source
            source_cursor.execute(f"SELECT * FROM {table}")
            rows = source_cursor.fetchall()

            if rows:
                # Convert rows to plain tuples for SQLite insertion
                converted_rows = []
                for row in rows:
                    if hasattr(row, "keys"):
                        # Row object with keys (sqlite3.Row or libsql.Row)
                        converted_rows.append(tuple(row[col] for col in columns))
                    else:
                        # Plain tuple/list
                        converted_rows.append(tuple(row))

            # Close source connection for this table
            source_conn.close()

            if converted_rows:
                # Prepare insert statement
                placeholders = ",".join(["?" for _ in columns])
                columns_str = ",".join([f"`{col}`" for col in columns])
                insert_sql = (
                    f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
                )

                # Insert data into target
                target_cursor.executemany(insert_sql, converted_rows)
                print(f"  Inserted {len(converted_rows)} rows into {table}")
            else:
                print(f"  No data to sync for {table}")

        # Commit changes
        target_conn.commit()

        # Verify counts
        print("\n✓ Sync complete!")
        for table in tables:
            target_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = target_cursor.fetchone()[0]
            print(f"  - {table.capitalize()} count: {count}")

    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"Error during sync: {e}")
        target_conn.rollback()
        sys.exit(1)

    finally:
        target_conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sync staging database to miniflare D1"
    )
    parser.add_argument(
        "--miniflare-db",
        type=Path,
        default=DEFAULT_MINIFLARE_DB,
        help=f"Path to miniflare database file (default: {DEFAULT_MINIFLARE_DB})",
    )

    args = parser.parse_args()
    sync_databases(args.miniflare_db)
