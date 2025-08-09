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

# Configuration
STAGING_DB = Path(
    "/Users/devin/repos/projects/data-pipelines/boxing/data/output/staging_mirror.db"
)
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
D1_DATABASE_ID = os.getenv("D1_DATABASE_ID")
D1_PREVIEW_DATABASE_ID = os.getenv("D1_PREVIEW_DATABASE_ID")
USE_PREVIEW_DB = os.getenv("USE_PREVIEW_DB", "false").lower() == "true"
API_TOKEN = os.getenv("CLOUDFLARE_D1_TOKEN") or os.getenv("CLOUDFLARE_API_TOKEN")

TABLES_TO_SYNC = ["boxers", "divisions"]


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


def sync_table(
    source_cur: sqlite3.Cursor,
    client: Cloudflare,
    account_id: str,
    database_id: str,
    table: str,
) -> None:
    print(f"\nSyncing {table}...")

    # Fetch source rows
    source_cur.execute(f"SELECT * FROM `{table}`")
    rows = source_cur.fetchall()

    # Columns
    source_cur.execute(f"PRAGMA table_info(`{table}`)")
    columns = [col[1] for col in source_cur.fetchall()]
    if not columns:
        print(f"  Skipping {table}: couldn't read columns")
        return

    # Clear target table
    d1_query(client, account_id, database_id, f"DELETE FROM `{table}`;")
    print("  Cleared target table")

    if not rows:
        print("  No rows to insert")
        return

    # Respect D1 params limit (100 params per query)
    params_per_row = len(columns)
    if params_per_row == 0:
        print("  No columns found, skipping")
        return

    max_rows_per_batch = max(1, 100 // params_per_row)

    inserted = 0
    for batch in chunked(rows, max_rows_per_batch):
        # Build SQL and params
        sql, ppr = build_multi_insert_sql(table, columns, len(batch))
        params: List[Any] = []
        for r in batch:
            params.extend(sanitize_value(v) for v in r)

        d1_query(client, account_id, database_id, sql, params)
        inserted += len(batch)
        print(f"  Inserted {inserted}/{len(rows)}", end="\r")

    print(f"\n  ✓ Finished {table}: {inserted} rows")


def sync_databases():
    if not STAGING_DB.exists():
        fail(f"Source database not found at {STAGING_DB}")

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

    target_label = "preview" if USE_PREVIEW_DB else "prod"
    print(f"Starting sync from {STAGING_DB} → Cloudflare D1 ({target_label})")

    client = Cloudflare(api_token=API_TOKEN)

    # Open source sqlite
    src_conn = sqlite3.connect(STAGING_DB)
    try:
        src_conn.row_factory = sqlite3.Row
        src_cur = src_conn.cursor()

        for table in TABLES_TO_SYNC:
            sync_table(src_cur, client, ACCOUNT_ID, database_id, table)

        print("\n✓ Sync complete!")
    except Exception as e:
        fail(f"Error during sync: {e}")
    finally:
        src_conn.close()


if __name__ == "__main__":
    sync_databases()
