#!/usr/bin/env python3
"""
Sync staging_mirror.db to local miniflare D1 database
"""

import sqlite3
import os
import sys
from pathlib import Path
from typing import Iterable, List, Tuple, Any

from cloudflare import Cloudflare

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from boxing.database.staging_mirror import get_connection

# Configuration
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
D1_DATABASE_ID = os.getenv("D1_DATABASE_ID")
D1_PREVIEW_DATABASE_ID = os.getenv("D1_PREVIEW_DATABASE_ID")
USE_PREVIEW_DB = os.getenv("USE_PREVIEW_DB", "true").lower() == "true"
API_TOKEN = os.getenv("CLOUDFLARE_D1_TOKEN") or os.getenv("CLOUDFLARE_API_TOKEN")

TABLES_TO_SYNC = ["boxers", "divisions", "bouts"]


def fail(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def chunked(iterable: Iterable, n: int) -> Iterable[List[Any]]:
    """Yield successive n-sized chunks from iterable."""
    buf = []
    for item in iterable:
        buf.append(item)
        if len(buf) >= n:
            yield buf
            buf = []
    if buf:
        yield buf


def sanitize_value(v: Any) -> Any:
    """
    Make SQLite row values JSON-serializable for Cloudflare API params.
    - Keep None as None (NULL).
    - Convert bools to int (SQLite uses 0/1).
    - Leave int/float/str as-is.
    - Convert bytes to memoryview -> bytes hex string (or str) if needed.
    """
    if v is None:
        return None
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, (int, float, str)):
        return v
    if isinstance(v, (bytes, bytearray, memoryview)):
        # store as hex text; adjust to your schema needs
        return v.hex() if isinstance(v, (bytes, bytearray)) else bytes(v).hex()
    # Fallback to string representation
    return str(v)


def build_multi_insert_sql(
    table: str, columns: List[str], rows_count: int
) -> Tuple[str, int]:
    """
    Build a multi-row INSERT statement with positional '?' placeholders.
    Returns (sql, params_per_row).
    """
    quoted_cols = ",".join(f"`{c}`" for c in columns)
    row_placeholders = "(" + ",".join("?" for _ in columns) + ")"
    values_clause = ",".join([row_placeholders] * rows_count)
    sql = f"INSERT INTO `{table}` ({quoted_cols}) VALUES {values_clause};"
    return sql, len(columns)


def build_upsert_sql(table: str, columns: List[str], rows_count: int) -> str:
    """
    Build a multi-row INSERT OR REPLACE statement with positional '?' placeholders.
    """
    quoted_cols = ",".join(f"`{c}`" for c in columns)
    row_placeholders = "(" + ",".join("?" for _ in columns) + ")"
    values_clause = ",".join([row_placeholders] * rows_count)
    sql = f"INSERT OR REPLACE INTO `{table}` ({quoted_cols}) VALUES {values_clause};"
    return sql


def d1_query(
    client: Cloudflare,
    account_id: str,
    database_id: str,
    sql: str,
    params: List[Any] = None,
):
    """Wrapper around Cloudflare D1 query endpoint."""
    page = client.d1.database.query(
        account_id=account_id,
        database_id=database_id,
        sql=sql,
        params=params or [],
    )
    return page


def get_last_sync_timestamp(source_cur, table: str, environment: str) -> str:
    """Get the last sync timestamp for a table from sync_jobs."""
    try:
        source_cur.execute(
            "SELECT last_sync_timestamp FROM sync_jobs WHERE name = ?",
            (f"{table}_{environment}",),
        )
        result = source_cur.fetchone()
        return result[0] if result else "1970-01-01 00:00:00"
    except Exception:
        # sync_jobs table doesn't exist yet
        return "1970-01-01 00:00:00"


def update_sync_timestamp(
    source_cur, table: str, environment: str, timestamp: str
) -> None:
    """Update the last sync timestamp for a table in sync_jobs."""
    try:
        source_cur.execute(
            "INSERT OR REPLACE INTO sync_jobs (name, last_sync_timestamp) VALUES (?, ?)",
            (f"{table}_{environment}", timestamp),
        )
    except Exception:
        # sync_jobs table doesn't exist, skip tracking
        print(f"  Warning: sync_jobs table not found, skipping timestamp tracking")


def sync_table(
    client: Cloudflare,
    account_id: str,
    database_id: str,
    table: str,
    environment: str,
) -> None:
    print(f"\nSyncing {table}...")

    # Open connection to get data
    source_conn = get_connection()
    source_cur = source_conn.cursor()

    try:
        # Get last sync timestamp
        last_sync = get_last_sync_timestamp(source_cur, table, environment)
        print(f"  Last sync: {last_sync}")

        # Get table columns
        source_cur.execute(f"PRAGMA table_info(`{table}`)")
        columns = [col[1] for col in source_cur.fetchall()]
        if not columns:
            print(f"  Skipping {table}: couldn't read columns")
            return

        # Check if table has updatedAt column for incremental sync
        has_updated_at = "updatedAt" in columns

        if has_updated_at:
            # Incremental sync based on updatedAt timestamp
            # Use datetime() to normalize both formats for comparison
            source_cur.execute(
                f"SELECT * FROM `{table}` WHERE datetime(updatedAt) > datetime(?) ORDER BY updatedAt",
                (last_sync,),
            )
            rows = source_cur.fetchall()
            print(f"  Found {len(rows)} updated/new records since {last_sync}")
        else:
            # No updatedAt column, sync all records with upsert
            print(f"  No updatedAt column found, syncing all records with upsert")
            source_cur.execute(f"SELECT * FROM `{table}`")
            rows = source_cur.fetchall()

        # Convert rows to list if needed (libsql compatibility)
        if hasattr(rows, "__iter__") and not isinstance(rows, list):
            rows = list(rows)

        # Convert rows to plain data immediately while connection is active
        converted_rows = []
        for r in rows:
            # Handle both sqlite3.Row and libsql row objects
            if hasattr(r, "keys"):
                # Row object with keys (sqlite3.Row or libsql.Row)
                row_values = [r[col] for col in columns]
            else:
                # Plain tuple/list
                row_values = list(r)
            converted_rows.append(row_values)

    finally:
        # Close connection after getting data
        source_conn.close()

    if not converted_rows:
        print("  No rows to sync")
        return

    # Use upsert for all sync operations
    params_per_row = len(columns)
    if params_per_row == 0:
        print("  No columns found, skipping")
        return

    max_rows_per_batch = max(1, 100 // params_per_row)

    processed = 0
    for batch in chunked(converted_rows, max_rows_per_batch):
        # Always use INSERT OR REPLACE for upsert behavior
        sql = build_upsert_sql(table, columns, len(batch))

        params: List[Any] = []
        for row_values in batch:
            params.extend(sanitize_value(v) for v in row_values)

        d1_query(client, account_id, database_id, sql, params)
        processed += len(batch)
        print(f"  Processed {processed}/{len(converted_rows)}", end="\r")

    print(f"\n  ✓ Finished {table}: {processed} rows processed")

    # Reopen connection for timestamp update
    source_conn = get_connection()
    source_cur = source_conn.cursor()
    try:
        source_cur.execute("SELECT datetime('now')")
        actual_timestamp = source_cur.fetchone()[0]
        update_sync_timestamp(source_cur, table, environment, actual_timestamp)
        source_conn.commit()
    finally:
        source_conn.close()


def sync_databases():
    if not ACCOUNT_ID:
        fail("CLOUDFLARE_ACCOUNT_ID not set")

    database_id = D1_PREVIEW_DATABASE_ID if USE_PREVIEW_DB else D1_DATABASE_ID
    if not database_id:
        which = (
            "CLOUDFLARE_D1_PREVIEW_DATABASE_ID"
            if USE_PREVIEW_DB
            else "CLOUDFLARE_D1_DATABASE_ID"
        )
        fail(f"{which} not set")

    if not API_TOKEN:
        fail("CLOUDFLARE_D1_TOKEN or CLOUDFLARE_API_TOKEN not set")

    target_label = "preview" if USE_PREVIEW_DB else "production"
    print(f"Starting sync to Cloudflare D1 ({target_label})")

    client = Cloudflare(api_token=API_TOKEN)

    try:
        for table in TABLES_TO_SYNC:
            sync_table(client, ACCOUNT_ID, database_id, table, target_label)

        print("\n✓ Sync complete!")
    except Exception as e:
        import traceback

        traceback.print_exc()

        fail(f"Error during sync: {e}")


if __name__ == "__main__":
    sync_databases()
