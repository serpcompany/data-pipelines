"""
ETL DAG: Extract from Data Lake -> Transform -> Load to Staging

Fixed to avoid Airflow's dynamic task mapping length cap by batching the work.
We map over batches of boxer_ids instead of every single boxer, so one run
can process everything without hitting the 1,024 mapped task limit.
"""

from __future__ import annotations

from datetime import datetime
from airflow.decorators import dag, task
import sys
from typing import List, Dict, Any

sys.path.append("/opt/airflow/boxing")

from boxing.load.to_staging_mirror_db import StagingLoader
from boxing.database.validators import run_validation
from boxing.utils.config import get_postgres_connection
from boxing.database.staging_mirror import get_connection as get_staging_connection


@dag(
    dag_id="etl_data_lake_to_staging",
    description="ETL: Extract HTML from data lake, transform, load to staging",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["etl", "data-lake", "staging"],
    params={
        "batch_size": 500,
        "force_reprocess": False,
    },
    max_active_runs=1,
    max_active_tasks=5,
)
def etl_pipeline():

    @task
    def check_data_lake_status() -> Dict[str, Any]:
        """Check data lake for unprocessed HTML records."""
        conn = get_postgres_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT boxrec_id) as unique_boxers,
                MAX(scraped_at) as latest_scrape
            FROM "data_lake".boxrec_boxer_raw_html
            """
        )

        total_records, unique_boxers, latest_scrape = cursor.fetchone()

        staging_conn = get_staging_connection()
        staging_cursor = staging_conn.cursor()
        staging_cursor.execute("SELECT COUNT(*) FROM boxers")
        staging_count = staging_cursor.fetchone()[0]

        staging_conn.close()
        conn.close()

        return {
            "data_lake_records": total_records,
            "unique_boxers": unique_boxers,
            "staging_boxers": staging_count,
            "latest_scrape": latest_scrape.isoformat() if latest_scrape else None,
            "unprocessed_count": max(0, unique_boxers - staging_count),
        }

    @task
    def get_unprocessed_batches(status: Dict[str, Any]) -> List[List[int]]:
        """
        Return batches (lists) of boxer_ids to process. This keeps the number of
        mapped tasks under Airflow's max_map_length while still handling
        all IDs in a single DAG run.
        """
        from airflow.operators.python import get_current_context

        ctx = get_current_context()
        params = ctx.get("params", {}) or {}
        batch_size = int(params.get("batch_size") or 500)
        limit = params.get("limit")
        force_reprocess = params.get("force_reprocess", False)

        # Early exit if there's nothing to do and we're not forcing reprocess
        if status["unprocessed_count"] == 0 and not force_reprocess:
            return []

        conn = get_postgres_connection()
        cur = conn.cursor()

        if not force_reprocess:
            # Exclude boxer_ids already present in staging
            staging_conn = get_staging_connection()
            scur = staging_conn.cursor()
            scur.execute("SELECT boxrecId FROM boxers")
            existing_ids = {row[0] for row in scur.fetchall()}
            staging_conn.close()

            if existing_ids:
                placeholders = ",".join(["%s"] * len(existing_ids))
                cur.execute(
                    f"""
                    SELECT DISTINCT boxrec_id
                    FROM "data_lake".boxrec_boxer_raw_html
                    WHERE boxrec_id NOT IN ({placeholders})
                    ORDER BY boxrec_id
                    """,
                    list(existing_ids),
                )
            else:
                cur.execute(
                    """
                    SELECT DISTINCT boxrec_id
                    FROM "data_lake".boxrec_boxer_raw_html
                    ORDER BY boxrec_id
                    """
                )
        else:
            query = """
                SELECT DISTINCT boxrec_id
                FROM "data_lake".boxrec_boxer_raw_html
                ORDER BY boxrec_id
            """
            if limit:
                query += f" LIMIT {int(limit)}"
            cur.execute(query)

        all_ids = [row[0] for row in cur.fetchall()]
        conn.close()

        # Apply optional limit after computing the full set when not force_reprocess
        if not force_reprocess and limit:
            all_ids = all_ids[: int(limit)]

        # Chunk into batches
        batches: List[List[int]] = [
            all_ids[i : i + batch_size] for i in range(0, len(all_ids), batch_size)
        ]
        return batches

    @task
    def process_batch(batch_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Process one batch sequentially. Each result is a small summary dict to keep XComs light.
        """
        results: List[Dict[str, Any]] = []

        for boxer_id in batch_ids:
            # Fetch HTML data from database for this boxer
            conn = get_postgres_connection()
            cursor = conn.cursor()

            # Professional record (required)
            cursor.execute(
                """
                SELECT boxrec_url, html_file 
                FROM "data_lake".boxrec_boxer_raw_html
                WHERE boxrec_id = %s AND competition_level = 'professional'
                """,
                (boxer_id,),
            )
            pro_result = cursor.fetchone()

            # Amateur record (optional)
            cursor.execute(
                """
                SELECT html_file
                FROM "data_lake".boxrec_boxer_raw_html
                WHERE boxrec_id = %s AND competition_level = 'amateur'
                """,
                (boxer_id,),
            )
            amat_result = cursor.fetchone()
            conn.close()

            if not pro_result:
                results.append(
                    {
                        "boxer_id": boxer_id,
                        "status": "failed",
                        "error": "Professional record not found in database",
                    }
                )
                continue

            pro_url, pro_html = pro_result
            amateur_html = amat_result[0] if amat_result else None

            try:
                with StagingLoader() as loader:
                    out = loader.process_boxer_with_both_records(
                        boxer_id=boxer_id,
                        pro_url=pro_url,
                        pro_html=pro_html,
                        amateur_html=amateur_html,
                    )

                if out:
                    results.append(
                        {
                            "boxer_id": boxer_id,
                            "status": "success",
                            "name": out.get("name", "Unknown"),
                            "bouts_count": len(out.get("bouts", [])),
                            "has_amateur": amateur_html is not None,
                        }
                    )
                else:
                    results.append(
                        {
                            "boxer_id": boxer_id,
                            "status": "failed",
                            "error": "Processing failed",
                        }
                    )
            except Exception as e:
                results.append(
                    {"boxer_id": boxer_id, "status": "failed", "error": str(e)}
                )

        return results

    @task
    def flatten(all_batch_results: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Flatten the list of lists from mapped batches into one list of results."""
        flat: List[Dict[str, Any]] = []
        for batch in all_batch_results:
            flat.extend(batch or [])
        return flat

    @task
    def validate_staging_data(
        processing_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Run validation checks on staging database."""
        try:
            report = run_validation()
            return {
                "status": "success" if report["summary"]["failed"] == 0 else "warnings",
                "passed": report["summary"]["passed"],
                "failed": report["summary"]["failed"],
                "failed_checks": [
                    check["name"] for check in report.get("failed_checks", [])[:5]
                ],
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @task
    def generate_etl_report(
        status: Dict[str, Any],
        batches: List[List[int]],
        results: List[Dict[str, Any]],
        validation: Dict[str, Any],
    ) -> str:
        """Generate ETL pipeline report."""
        total_to_process = sum(len(b) for b in (batches or []))
        if not batches or total_to_process == 0:
            return "No boxers to process - ETL skipped"

        successful = [r for r in results if r.get("status") == "success"]
        failed = [r for r in results if r.get("status") == "failed"]
        total_bouts = sum(int(r.get("bouts_count", 0)) for r in successful)
        with_amateur = sum(1 for r in successful if r.get("has_amateur"))

        # Final staging count
        staging_conn = get_staging_connection()
        cursor = staging_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM boxers")
        final_count = cursor.fetchone()[0]
        staging_conn.close()

        print("\n" + "=" * 60)
        print("ETL PIPELINE REPORT")
        print("=" * 60)
        print(
            f"Data Lake: {status['data_lake_records']} records, {status['unique_boxers']} boxers"
        )
        print(f"Staging Before: {status['staging_boxers']} boxers")
        print(f"Staging After: {final_count} boxers")
        print()
        print(f"Batches: {len(batches)} (total boxer_ids: {total_to_process})")
        print(f"Processing: {len(successful)} success, {len(failed)} failed")
        print(f"Extracted: {total_bouts} total bouts")
        print(f"Amateur records: {with_amateur} boxers")
        print()
        print(
            f"Validation: {validation['status']} "
            f"({validation.get('passed', 0)} passed, {validation.get('failed', 0)} failed)"
        )

        if failed:
            print(f"\nFailed boxers (first 3):")
            for fail in failed[:3]:
                print(f"  - {fail.get('boxer_id')}: {fail.get('error')}")

        return f"ETL: {len(successful)} success, {len(failed)} failed across {len(batches)} batches"

    status = check_data_lake_status()
    batches = get_unprocessed_batches(status)
    batch_results = process_batch.expand(
        batch_ids=batches
    )  # map over batches and process in parallel
    results = flatten(batch_results)
    validation = validate_staging_data(results)
    report = generate_etl_report(status, batches, results, validation)


# Create DAG instance
etl_dag = etl_pipeline()
