"""
Miniflare Sync DAG: Sync staging database to miniflare D1 database

This DAG syncs data from the staging database to a local miniflare D1 database.
The miniflare database path can be specified as a parameter.
"""

from __future__ import annotations

import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from airflow.decorators import dag, task
import sys

sys.path.append("/opt/airflow/boxing")

from boxing.database.staging_mirror import get_connection as get_staging_connection


@dag(
    dag_id="sync_to_miniflare",
    description="Sync staging database to miniflare D1 database",
    schedule=None,  # Manual trigger
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["sync", "miniflare", "d1"],
    params={
        "miniflare_db_path": "/path/to/miniflare/database.sqlite",  # Required parameter
        "tables_to_sync": ["boxers", "divisions", "bouts"],  # Tables to sync
        "dry_run": False,  # Set to True to see what would be synced without making changes
    },
    max_active_runs=1,
)
def miniflare_sync_pipeline():

    @task
    def validate_parameters() -> Dict[str, Any]:
        """Validate DAG parameters and database paths."""
        from airflow.operators.python import get_current_context
        
        ctx = get_current_context()
        params = ctx.get("params", {}) or {}
        
        miniflare_db_path = params.get("miniflare_db_path")
        tables_to_sync = params.get("tables_to_sync", ["boxers", "divisions", "bouts"])
        dry_run = params.get("dry_run", False)
        
        if not miniflare_db_path or miniflare_db_path == "/path/to/miniflare/database.sqlite":
            raise ValueError("miniflare_db_path parameter is required and must be a valid path")
        
        miniflare_path = Path(miniflare_db_path)
        
        # Check if miniflare database exists
        if not miniflare_path.exists():
            raise FileNotFoundError(f"Miniflare database not found at {miniflare_path}")
        
        # Check staging database connection
        try:
            staging_conn = get_staging_connection()
            staging_conn.close()
        except Exception as e:
            raise ConnectionError(f"Cannot connect to staging database: {e}")
        
        return {
            "miniflare_db_path": str(miniflare_path),
            "tables_to_sync": tables_to_sync,
            "dry_run": dry_run,
            "validation_passed": True
        }

    @task
    def check_staging_data(config: Dict[str, Any]) -> Dict[str, Any]:
        """Check staging database for data counts before sync."""
        staging_conn = get_staging_connection()
        cursor = staging_conn.cursor()
        
        staging_counts = {}
        tables = config["tables_to_sync"]
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                staging_counts[table] = count
            except sqlite3.OperationalError as e:
                print(f"Warning: Table {table} not found in staging database: {e}")
                staging_counts[table] = 0
        
        staging_conn.close()
        
        return {
            "staging_counts": staging_counts,
            "total_records": sum(staging_counts.values())
        }

    @task
    def sync_databases(config: Dict[str, Any], staging_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync data from staging to miniflare database."""
        miniflare_db_path = config["miniflare_db_path"]
        tables_to_sync = config["tables_to_sync"]
        dry_run = config["dry_run"]
        
        if dry_run:
            return {
                "dry_run": True,
                "staged_operations": staging_data["staging_counts"],
                "message": "Dry run - no changes made"
            }
        
        # Connect to both databases
        staging_conn = get_staging_connection()
        target_conn = sqlite3.connect(miniflare_db_path)
        
        sync_results = {}
        
        try:
            staging_cursor = staging_conn.cursor()
            target_cursor = target_conn.cursor()
            
            for table in tables_to_sync:
                print(f"Syncing {table} table...")
                
                # Skip if no data in staging
                if staging_data["staging_counts"].get(table, 0) == 0:
                    print(f"  No data to sync for {table}")
                    sync_results[table] = {"cleared": 0, "inserted": 0, "status": "skipped"}
                    continue
                
                # Clear existing data in target
                target_cursor.execute(f"DELETE FROM {table}")
                cleared_count = target_cursor.rowcount
                print(f"  Cleared {cleared_count} existing {table} records")
                
                # Get data from source
                staging_cursor.execute(f"SELECT * FROM {table}")
                rows = staging_cursor.fetchall()
                
                inserted_count = 0
                if rows:
                    # Get column names
                    staging_cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in staging_cursor.fetchall()]
                    
                    # Prepare insert statement
                    placeholders = ",".join(["?" for _ in columns])
                    columns_str = ",".join([f"`{col}`" for col in columns])
                    insert_sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
                    
                    # Insert data into target
                    target_cursor.executemany(insert_sql, rows)
                    inserted_count = len(rows)
                    print(f"  Inserted {inserted_count} rows into {table}")
                
                sync_results[table] = {
                    "cleared": cleared_count,
                    "inserted": inserted_count,
                    "status": "success"
                }
            
            # Commit changes
            target_conn.commit()
            
            # Verify final counts in target
            final_counts = {}
            for table in tables_to_sync:
                try:
                    target_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    final_counts[table] = target_cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    final_counts[table] = 0
            
            return {
                "dry_run": False,
                "sync_results": sync_results,
                "final_counts": final_counts,
                "total_synced": sum(result.get("inserted", 0) for result in sync_results.values()),
                "status": "success"
            }
            
        except Exception as e:
            target_conn.rollback()
            return {
                "dry_run": False,
                "sync_results": sync_results,
                "status": "error",
                "error": str(e)
            }
        
        finally:
            staging_conn.close()
            target_conn.close()

    @task
    def generate_sync_report(
        config: Dict[str, Any],
        staging_data: Dict[str, Any],
        sync_results: Dict[str, Any]
    ) -> str:
        """Generate a report of the sync process."""
        
        print("\n" + "=" * 60)
        print("MINIFLARE SYNC REPORT")
        print("=" * 60)
        
        print(f"Configuration:")
        print(f"  - Miniflare DB Path: {config['miniflare_db_path']}")
        print(f"  - Tables to Sync: {', '.join(config['tables_to_sync'])}")
        print(f"  - Dry Run: {config['dry_run']}")
        
        print(f"\nStaging Database (Source):")
        for table, count in staging_data["staging_counts"].items():
            print(f"  - {table.capitalize()}: {count:,} records")
        print(f"  - Total: {staging_data['total_records']:,} records")
        
        if sync_results["dry_run"]:
            print(f"\n🔍 DRY RUN RESULTS:")
            print(f"  - Would sync {staging_data['total_records']:,} total records")
            print(f"  - No changes made to miniflare database")
        else:
            print(f"\n📊 SYNC RESULTS:")
            if sync_results["status"] == "success":
                print(f"  - Total Records Synced: {sync_results['total_synced']:,}")
                
                print(f"\n  Table Details:")
                for table, result in sync_results["sync_results"].items():
                    if result["status"] == "success":
                        print(f"    • {table.capitalize()}: {result['inserted']:,} inserted")
                    elif result["status"] == "skipped":
                        print(f"    • {table.capitalize()}: skipped (no data)")
                
                print(f"\n  Final Miniflare Counts:")
                for table, count in sync_results["final_counts"].items():
                    print(f"    • {table.capitalize()}: {count:,} records")
                
                print(f"\n✅ Sync completed successfully!")
                
            else:
                print(f"  - Status: ERROR")
                print(f"  - Error: {sync_results.get('error', 'Unknown error')}")
                print(f"\n❌ Sync failed!")
        
        return f"Miniflare sync {'(dry run)' if sync_results['dry_run'] else ''} complete: {sync_results.get('total_synced', 0)} records"

    # Task flow
    config = validate_parameters()
    staging_data = check_staging_data(config)
    sync_results = sync_databases(config, staging_data)
    report = generate_sync_report(config, staging_data, sync_results)


# Create DAG instance
miniflare_sync_dag = miniflare_sync_pipeline()