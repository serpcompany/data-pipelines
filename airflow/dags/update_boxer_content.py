"""
Content Update DAG: Check for new content in MySQL and update staging database

This DAG identifies boxers without content and checks if they now have
valid content available in the MySQL database. If found, it updates the
staging database with the new content.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import Dict, List, Any
from airflow.decorators import dag, task
import sys

sys.path.append("/opt/airflow/boxing")

from boxing.database.staging_mirror import get_connection as get_staging_connection
from boxing.database.utils import get_mysql_connection, get_mysql_gen_data
from dotenv import load_dotenv

load_dotenv()


@dag(
    dag_id="update_boxer_content",
    description="Check for new content in MySQL and update staging database",
    schedule=None,  # Manual trigger
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["content", "update", "mysql"],
    params={
        "dry_run": False,  # Set to True to see what would be updated without making changes
    },
    max_active_runs=1,
)
def content_update_pipeline():

    @task
    def identify_boxers_without_content() -> List[str]:
        """Identify boxers in staging that don't have content."""
        staging_conn = get_staging_connection()
        cursor = staging_conn.cursor()

        # Get boxers without content (bio is NULL or empty)
        cursor.execute(
            """
            SELECT boxrecId 
            FROM boxers 
            WHERE bio IS NULL OR bio = '' OR TRIM(bio) = ''
            ORDER BY boxrecId
        """
        )

        boxers_without_content = [row[0] for row in cursor.fetchall()]
        staging_conn.close()

        # Also check CSV for existing content
        content_csv_path = "/opt/airflow/data/input/boxer-articles.csv"
        csv_content_ids = set()

        try:
            with open(content_csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("boxrec_id") and row.get("bio"):
                        csv_content_ids.add(row["boxrec_id"].strip())
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error reading CSV: {e}")

        # Filter out boxers that have content in CSV
        filtered_boxers = [
            boxrec_id
            for boxrec_id in boxers_without_content
            if boxrec_id not in csv_content_ids
        ]

        print(f"Found {len(boxers_without_content)} boxers without content in staging")
        print(f"Found {len(csv_content_ids)} boxers with content in CSV")
        print(f"Checking {len(filtered_boxers)} boxers for MySQL content")

        return filtered_boxers

    @task
    def check_and_update_content(boxer_ids: List[str]) -> Dict[str, Any]:
        """Check MySQL for content and update staging database."""
        from airflow.operators.python import get_current_context

        ctx = get_current_context()
        params = ctx.get("params", {}) or {}
        dry_run = params.get("dry_run", False)

        if not boxer_ids:
            return {
                "checked_count": 0,
                "found_count": 0,
                "updated_count": 0,
                "dry_run": dry_run,
                "updates": [],
            }

        found_content = []

        try:
            mysql_conn = get_mysql_connection()

            module_id = int(os.getenv("MYSQL_MODULE_ID", "409"))

            mysql_data = get_mysql_gen_data(
                mysql_conn=mysql_conn,
                module_id=module_id,
                identifiers=boxer_ids,
                type_="boxer",
                use_citations=False,
            )

            mysql_conn.close()

            # Process results
            for result in mysql_data:
                found_content.append(
                    {
                        "boxrec_id": result["identifier"],
                        "content": result["content"],
                        "one_liner": result["one_liner"],
                        "excerpt": result["excerpt"],
                        "content_length": len(result["content"]),
                    }
                )

        except Exception as e:
            print(f"Error checking MySQL content: {e}")
            return {
                "checked_count": len(boxer_ids),
                "found_count": 0,
                "updated_count": 0,
                "dry_run": dry_run,
                "updates": [],
                "error": str(e),
            }

        # Update staging database
        updated_boxers = []

        if found_content and not dry_run:
            staging_conn = get_staging_connection()
            cursor = staging_conn.cursor()

            try:
                cursor.execute("BEGIN")

                for update in found_content:
                    cursor.execute(
                        """
                        UPDATE boxers 
                        SET bio = ?, updatedAt = ?
                        WHERE boxrecId = ?
                    """,
                        (
                            update["content"],
                            datetime.now().isoformat(),
                            update["boxrec_id"],
                        ),
                    )

                    updated_boxers.append(
                        {
                            "boxrec_id": update["boxrec_id"],
                            "content_length": update["content_length"],
                            "has_one_liner": update["one_liner"] is not None,
                            "has_excerpt": update["excerpt"] is not None,
                        }
                    )

                cursor.execute("COMMIT")
                staging_conn.close()

            except Exception as e:
                cursor.execute("ROLLBACK")
                staging_conn.close()
                raise e
        elif found_content:
            # Dry run - just collect what would be updated
            updated_boxers = [
                {
                    "boxrec_id": update["boxrec_id"],
                    "content_length": update["content_length"],
                    "has_one_liner": update["one_liner"] is not None,
                    "has_excerpt": update["excerpt"] is not None,
                }
                for update in found_content
            ]

        return {
            "checked_count": len(boxer_ids),
            "found_count": len(found_content),
            "updated_count": len(updated_boxers),
            "dry_run": dry_run,
            "updates": updated_boxers,
        }

    @task
    def generate_content_update_report(update_results: Dict[str, Any]) -> str:
        """Generate a report of the content update process."""

        print("\n" + "=" * 60)
        print("CONTENT UPDATE REPORT")
        print("=" * 60)

        print(f"Process Summary:")
        print(
            f"  - Boxers checked for MySQL content: {update_results['checked_count']}"
        )
        print(f"  - Boxers with new content found: {update_results['found_count']}")
        print(
            f"  - Content updates {'(DRY RUN)' if update_results['dry_run'] else ''}: {update_results['updated_count']}"
        )

        if update_results.get("error"):
            print(f"  - Error occurred: {update_results['error']}")

        if update_results["updates"]:
            print(f"\nUpdated Boxers (first 10):")
            for update in update_results["updates"][:10]:
                print(f"  - {update['boxrec_id']}: {update['content_length']} chars")
                if update["has_one_liner"]:
                    print(f"    ✓ Has one-liner")
                if update["has_excerpt"]:
                    print(f"    ✓ Has excerpt")

        # Final staging statistics
        staging_conn = get_staging_connection()
        cursor = staging_conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM boxers")
        total_boxers = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*) FROM boxers 
            WHERE bio IS NOT NULL AND bio != '' AND TRIM(bio) != ''
        """
        )
        boxers_with_content = cursor.fetchone()[0]

        staging_conn.close()

        print(f"\nFinal Statistics:")
        print(f"  - Total boxers in staging: {total_boxers}")
        print(f"  - Boxers with content: {boxers_with_content}")
        print(f"  - Boxers without content: {total_boxers - boxers_with_content}")
        print(f"  - Content coverage: {(boxers_with_content/total_boxers*100):.1f}%")

        return (
            f"Content update complete: {update_results['updated_count']} boxers updated"
        )

    # Task flow
    boxer_ids = identify_boxers_without_content()
    update_results = check_and_update_content(boxer_ids)
    report = generate_content_update_report(update_results)


# Create DAG instance
content_update_dag = content_update_pipeline()
