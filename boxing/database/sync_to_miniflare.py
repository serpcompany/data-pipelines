#!/usr/bin/env python3
"""
Sync staging_mirror.db to local miniflare D1 database
"""

import sqlite3
import os
import sys
from pathlib import Path

# Configuration
STAGING_DB = Path("/Users/devin/repos/projects/data-pipelines/boxing/data/output/staging_mirror.db")
MINIFLARE_DB = Path("/Users/devin/repos/projects/boxingundefeated.com/.data/hub/d1/miniflare-D1DatabaseObject/7b8799eb95f0bb5448e259812996a461ce40142dacbdea254ea597e307767f45.sqlite")

def sync_databases():
    """Sync data from staging_mirror.db to miniflare D1 database"""
    
    # Check if databases exist
    if not STAGING_DB.exists():
        print(f"Error: Source database not found at {STAGING_DB}")
        sys.exit(1)
    
    if not MINIFLARE_DB.exists():
        print(f"Error: Target miniflare database not found at {MINIFLARE_DB}")
        sys.exit(1)
    
    print("Starting sync from staging_mirror.db to miniflare D1...")
    
    # Connect to both databases
    source_conn = sqlite3.connect(STAGING_DB)
    target_conn = sqlite3.connect(MINIFLARE_DB)
    
    try:
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()
        
        # Tables to sync
        tables = ['boxers', 'divisions']
        
        for table in tables:
            print(f"\nSyncing {table} table...")
            
            # Clear existing data in target
            target_cursor.execute(f"DELETE FROM {table}")
            print(f"  Cleared existing {table} data")
            
            # Get data from source
            source_cursor.execute(f"SELECT * FROM {table}")
            rows = source_cursor.fetchall()
            
            if rows:
                # Get column names
                source_cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in source_cursor.fetchall()]
                
                # Prepare insert statement
                placeholders = ','.join(['?' for _ in columns])
                columns_str = ','.join([f'`{col}`' for col in columns])
                insert_sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
                
                # Insert data into target
                target_cursor.executemany(insert_sql, rows)
                print(f"  Inserted {len(rows)} rows into {table}")
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
        print(f"Error during sync: {e}")
        target_conn.rollback()
        sys.exit(1)
    
    finally:
        source_conn.close()
        target_conn.close()

if __name__ == "__main__":
    sync_databases()