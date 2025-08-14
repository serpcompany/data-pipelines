"""
Export Staging Data to JSON DAG

Exports data from staging SQLite database tables to JSON files.
Supports boxers, events, and bouts entities.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
import sys

sys.path.append("/opt/airflow/boxing")

from boxing.database.staging_mirror import get_connection as get_staging_connection

DEFAULT_ARGS = {
    "owner": "boxing-pipeline",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": 60,
}

OUTPUT_DIR = Path("/opt/airflow/data")


@dag(
    dag_id="export_staging_to_json",
    description="Export staging database data to JSON files",
    default_args=DEFAULT_ARGS,
    schedule=None,  # Manual trigger
    catchup=False,
    tags=["export", "json", "staging"],
    params={
        "entity": "boxer",  # boxer, event, or bout
        "limit": None,  # Optional limit on number of records
        "output_filename": None,  # Optional custom filename (without .json extension)
    },
    max_active_runs=1,
)
def export_staging_to_json():

    @task
    def check_staging_status() -> Dict[str, Any]:
        """Check staging database for available records."""
        ctx = get_current_context()
        params = ctx.get("params", {}) or {}
        entity = params.get("entity", "boxer")

        staging_conn = get_staging_connection()
        cursor = staging_conn.cursor()

        # Get count for the specified entity
        if entity in ["boxer", "boxers"]:
            cursor.execute("SELECT COUNT(*) FROM boxers")
            table_name = "boxers"
        elif entity in ["event", "events"]:
            cursor.execute("SELECT COUNT(*) FROM events")
            table_name = "events"
        elif entity in ["bout", "bouts", "fight", "fights"]:
            cursor.execute("SELECT COUNT(*) FROM bouts")
            table_name = "bouts"
        else:
            staging_conn.close()
            raise ValueError(f"Unsupported entity type: {entity}")

        total_count = cursor.fetchone()[0]
        staging_conn.close()

        return {
            "entity": entity,
            "table_name": table_name,
            "total_records": total_count,
        }

    @task
    def export_data_to_json(status: Dict[str, Any]) -> Dict[str, Any]:
        """Export staging data to JSON file."""
        ctx = get_current_context()
        params = ctx.get("params", {}) or {}
        entity = status["entity"]
        table_name = status["table_name"]
        limit = params.get("limit")
        custom_filename = params.get("output_filename")

        if status["total_records"] == 0:
            return {
                "status": "skipped",
                "message": f"No {entity} records found in staging database",
                "records_exported": 0,
                "file_path": None,
            }

        # Connect to staging database
        staging_conn = get_staging_connection()
        cursor = staging_conn.cursor()

        # Build query with optional limit
        query = f"SELECT * FROM {table_name} ORDER BY createdAt"
        if limit:
            query += f" LIMIT {int(limit)}"

        cursor.execute(query)
        raw_rows = cursor.fetchall()

        columns = [desc[0] for desc in cursor.description]
        rows = [dict(zip(columns, row)) for row in raw_rows]
        staging_conn.close()

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

        # Create output directory
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if custom_filename:
            filename = f"{custom_filename}.json"
        else:
            filename = f"{entity}_export_{timestamp}.json"
            if limit:
                filename = f"{entity}_export_{timestamp}_limit_{limit}.json"

        file_path = OUTPUT_DIR / filename

        # Write JSON file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(processed_rows, f, indent=2, ensure_ascii=False, default=str)

        return {
            "status": "success",
            "entity": entity,
            "records_exported": len(processed_rows),
            "total_available": status["total_records"],
            "file_path": str(file_path),
            "filename": filename,
            "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
        }

    @task
    def generate_export_report(
        status: Dict[str, Any], export_result: Dict[str, Any]
    ) -> str:
        """Generate export report."""
        entity = status["entity"]

        print("\n" + "=" * 60)
        print("JSON EXPORT REPORT")
        print("=" * 60)
        print(f"Entity: {entity}")
        print(f"Total records in staging: {status['total_records']}")

        if export_result["status"] == "success":
            print(f"Records exported: {export_result['records_exported']}")
            print(f"Output file: {export_result['filename']}")
            print(f"File size: {export_result['file_size_mb']} MB")
            print(f"Full path: {export_result['file_path']}")

            if export_result["records_exported"] < status["total_records"]:
                print(
                    f"Note: Limited export ({export_result['records_exported']}/{status['total_records']} records)"
                )
        else:
            print(f"Export skipped: {export_result['message']}")

        print("=" * 60)

        return f"Exported {export_result.get('records_exported', 0)} {entity} records"

    # Define task dependencies
    status = check_staging_status()
    export_result = export_data_to_json(status)
    report = generate_export_report(status, export_result)


# Create DAG instance
export_dag = export_staging_to_json()
