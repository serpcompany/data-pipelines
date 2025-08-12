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
        "entity": "boxer",  # boxer, bout, or event
    },
    max_active_runs=1,
    max_active_tasks=5,
)
def etl_pipeline():

    @task
    def check_data_lake_status() -> Dict[str, Any]:
        """Check data lake for unprocessed HTML records based on entity type."""
        from airflow.operators.python import get_current_context
        
        ctx = get_current_context()
        params = ctx.get("params", {}) or {}
        entity = params.get("entity", "boxer")
        
        conn = get_postgres_connection()
        cursor = conn.cursor()

        if entity == "boxer":
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT boxrec_id) as unique_entities,
                    MAX(scraped_at) as latest_scrape
                FROM "data_lake".boxrec
                WHERE entity = 'boxer'
                """
            )

            total_records, unique_entities, latest_scrape = cursor.fetchone()

            staging_conn = get_staging_connection()
            staging_cursor = staging_conn.cursor()
            staging_cursor.execute("SELECT COUNT(*) FROM boxers")
            staging_count = staging_cursor.fetchone()[0]
            staging_conn.close()

        elif entity == "event":
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT boxrec_id) as unique_entities,
                    MAX(scraped_at) as latest_scrape
                FROM "data_lake".boxrec
                WHERE entity = 'event'
                """
            )

            total_records, unique_entities, latest_scrape = cursor.fetchone()

            staging_conn = get_staging_connection()
            staging_cursor = staging_conn.cursor()
            staging_cursor.execute("SELECT COUNT(*) FROM events")
            staging_count = staging_cursor.fetchone()[0]
            staging_conn.close()

        elif entity == "bout":
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT boxrec_id) as unique_entities,
                    MAX(scraped_at) as latest_scrape
                FROM "data_lake".boxrec
                WHERE entity = 'bout'
                """
            )

            total_records, unique_entities, latest_scrape = cursor.fetchone()

            staging_conn = get_staging_connection()
            staging_cursor = staging_conn.cursor()
            staging_cursor.execute("SELECT COUNT(*) FROM bouts")
            staging_count = staging_cursor.fetchone()[0]
            staging_conn.close()

        conn.close()

        return {
            "entity": entity,
            "data_lake_records": total_records,
            "unique_entities": unique_entities,
            "staging_count": staging_count,
            "latest_scrape": latest_scrape.isoformat() if latest_scrape else None,
            "unprocessed_count": max(0, unique_entities - staging_count),
        }

    @task
    def get_unprocessed_batches(status: Dict[str, Any]) -> List[List[str]]:
        """
        Return batches (lists) of entity_ids to process. This keeps the number of
        mapped tasks under Airflow's max_map_length while still handling
        all IDs in a single DAG run.
        """
        from airflow.operators.python import get_current_context

        ctx = get_current_context()
        params = ctx.get("params", {}) or {}
        batch_size = int(params.get("batch_size") or 500)
        limit = params.get("limit")
        force_reprocess = params.get("force_reprocess", False)
        entity = status.get("entity", "boxer")

        # Early exit if there's nothing to do and we're not forcing reprocess
        if status["unprocessed_count"] == 0 and not force_reprocess:
            return []

        conn = get_postgres_connection()
        cur = conn.cursor()

        if not force_reprocess:
            # Exclude entity_ids already present in staging
            staging_conn = get_staging_connection()
            scur = staging_conn.cursor()
            
            if entity == "boxer":
                scur.execute("SELECT boxrecId FROM boxers")
            elif entity == "event":
                scur.execute("SELECT boxrecId FROM events")
            elif entity == "bout":
                # For bouts, we need to check event_id + bout_id combinations
                scur.execute("SELECT boxrecEventId || '_' || boxrecBoutId FROM bouts")
            
            existing_ids = {row[0] for row in scur.fetchall()}
            staging_conn.close()

            if existing_ids:
                placeholders = ",".join(["%s"] * len(existing_ids))
                cur.execute(
                    f"""
                    SELECT DISTINCT boxrec_id
                    FROM "data_lake".boxrec
                    WHERE boxrec_id NOT IN ({placeholders}) AND entity = %s
                    ORDER BY boxrec_id
                    """,
                    list(existing_ids) + [entity],
                )
            else:
                cur.execute(
                    """
                    SELECT DISTINCT boxrec_id
                    FROM "data_lake".boxrec
                    WHERE entity = %s
                    ORDER BY boxrec_id
                    """,
                    (entity,)
                )
        else:
            query = """
                SELECT DISTINCT boxrec_id
                FROM "data_lake".boxrec
                WHERE entity = %s
                ORDER BY boxrec_id
            """
            if limit:
                query += f" LIMIT {int(limit)}"
            cur.execute(query, (entity,))

        all_ids = [row[0] for row in cur.fetchall()]
        conn.close()

        # Apply optional limit after computing the full set when not force_reprocess
        if not force_reprocess and limit:
            all_ids = all_ids[: int(limit)]

        # Chunk into batches
        batches: List[List[str]] = [
            all_ids[i : i + batch_size] for i in range(0, len(all_ids), batch_size)
        ]
        return batches

    @task
    def process_batch(batch_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Process one batch sequentially. Each result is a small summary dict to keep XComs light.
        """
        from airflow.operators.python import get_current_context
        
        ctx = get_current_context()
        params = ctx.get("params", {}) or {}
        entity = params.get("entity", "boxer")
        
        results: List[Dict[str, Any]] = []

        if entity == "boxer":
            return process_boxer_batch(batch_ids)
        elif entity == "event":
            return process_event_batch(batch_ids)
        elif entity == "bout":
            return process_bout_batch(batch_ids)
        
        return results

    def process_boxer_batch(batch_ids: List[str]) -> List[Dict[str, Any]]:
        """Process a batch of boxer IDs."""
        results: List[Dict[str, Any]] = []
        
        for boxer_id in batch_ids:
            # Fetch HTML data from database for this boxer
            conn = get_postgres_connection()
            cursor = conn.cursor()

            # Professional record (required)
            cursor.execute(
                """
                SELECT boxrec_url, html_file 
                FROM "data_lake".boxrec
                WHERE boxrec_id = %s AND competition_level = 'professional' AND entity = 'boxer'
                """,
                (boxer_id,),
            )
            pro_result = cursor.fetchone()

            # Amateur record (optional)
            cursor.execute(
                """
                SELECT html_file
                FROM "data_lake".boxrec
                WHERE boxrec_id = %s AND competition_level = 'amateur' AND entity = 'boxer'
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

    def process_event_batch(batch_ids: List[str]) -> List[Dict[str, Any]]:
        """Process a batch of event IDs."""
        results: List[Dict[str, Any]] = []
        
        for event_id in batch_ids:
            # Fetch HTML data from database for this event
            conn = get_postgres_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT boxrec_url, html_file 
                FROM "data_lake".boxrec
                WHERE boxrec_id = %s AND entity = 'event'
                """,
                (event_id,),
            )
            result = cursor.fetchone()
            conn.close()

            if not result:
                results.append(
                    {
                        "entity_id": event_id,
                        "status": "failed",
                        "error": "Event record not found in database",
                    }
                )
                continue

            event_url, html_content = result

            try:
                with StagingLoader() as loader:
                    out = loader.process_event_with_html(
                        event_id=event_id,
                        event_url=event_url,
                        html_content=html_content,
                    )

                if out:
                    results.append(
                        {
                            "entity_id": event_id,
                            "status": "success",
                            "event_name": out.get("event_name", "Unknown"),
                        }
                    )
                else:
                    results.append(
                        {
                            "entity_id": event_id,
                            "status": "failed",
                            "error": "Processing failed",
                        }
                    )
            except Exception as e:
                results.append(
                    {"entity_id": event_id, "status": "failed", "error": str(e)}
                )

        return results

    def process_bout_batch(batch_ids: List[str]) -> List[Dict[str, Any]]:
        """Process a batch of bout IDs (event_id_bout_id format)."""
        results: List[Dict[str, Any]] = []
        
        for bout_id in batch_ids:
            # Parse event_id and bout_id from the combined ID
            if "_" not in bout_id:
                results.append(
                    {
                        "entity_id": bout_id,
                        "status": "failed",
                        "error": "Invalid bout ID format",
                    }
                )
                continue
            
            event_id, actual_bout_id = bout_id.rsplit("_", 1)
            
            # Fetch HTML data from database for this bout
            conn = get_postgres_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT boxrec_url, html_file 
                FROM "data_lake".boxrec
                WHERE boxrec_id = %s AND entity = 'bout'
                """,
                (bout_id,),
            )
            result = cursor.fetchone()
            conn.close()

            if not result:
                results.append(
                    {
                        "entity_id": bout_id,
                        "status": "failed",
                        "error": "Bout record not found in database",
                    }
                )
                continue

            bout_url, html_content = result

            try:
                with StagingLoader() as loader:
                    out = loader.process_bout_with_html(
                        event_id=event_id,
                        bout_id=actual_bout_id,
                        bout_url=bout_url,
                        html_content=html_content,
                    )

                if out:
                    results.append(
                        {
                            "entity_id": bout_id,
                            "status": "success",
                            "boxer_a": out.get("boxer_a_side", "Unknown"),
                            "boxer_b": out.get("boxer_b_side", "Unknown"),
                        }
                    )
                else:
                    results.append(
                        {
                            "entity_id": bout_id,
                            "status": "failed",
                            "error": "Processing failed",
                        }
                    )
            except Exception as e:
                results.append(
                    {"entity_id": bout_id, "status": "failed", "error": str(e)}
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
        batches: List[List[str]],
        results: List[Dict[str, Any]],
        validation: Dict[str, Any],
    ) -> str:
        """Generate ETL pipeline report."""
        entity = status.get("entity", "boxer")
        total_to_process = sum(len(b) for b in (batches or []))
        if not batches or total_to_process == 0:
            return f"No {entity}s to process - ETL skipped"

        successful = [r for r in results if r.get("status") == "success"]
        failed = [r for r in results if r.get("status") == "failed"]

        # Entity-specific metrics
        if entity == "boxer":
            total_bouts = sum(int(r.get("bouts_count", 0)) for r in successful)
            with_amateur = sum(1 for r in successful if r.get("has_amateur"))
            
            # Final staging count
            staging_conn = get_staging_connection()
            cursor = staging_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM boxers")
            final_count = cursor.fetchone()[0]
            staging_conn.close()
            
        elif entity == "event":
            # Final staging count
            staging_conn = get_staging_connection()
            cursor = staging_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events")
            final_count = cursor.fetchone()[0]
            staging_conn.close()
            
        elif entity == "bout":
            # Final staging count
            staging_conn = get_staging_connection()
            cursor = staging_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM bouts")
            final_count = cursor.fetchone()[0]
            staging_conn.close()

        print("\n" + "=" * 60)
        print("ETL PIPELINE REPORT")
        print("=" * 60)
        print(
            f"Data Lake: {status['data_lake_records']} records, {status['unique_entities']} {entity}s"
        )
        print(f"Staging Before: {status['staging_count']} {entity}s")
        print(f"Staging After: {final_count} {entity}s")
        print()
        print(f"Batches: {len(batches)} (total {entity}_ids: {total_to_process})")
        print(f"Processing: {len(successful)} success, {len(failed)} failed")
        
        if entity == "boxer":
            print(f"Extracted: {total_bouts} total bouts")
            print(f"Amateur records: {with_amateur} boxers")
        
        print()
        print(
            f"Validation: {validation['status']} "
            f"({validation.get('passed', 0)} passed, {validation.get('failed', 0)} failed)"
        )

        if failed:
            print(f"\nFailed {entity}s (first 3):")
            for fail in failed[:3]:
                entity_id = fail.get("boxer_id") or fail.get("entity_id")
                print(f"  - {entity_id}: {fail.get('error')}")

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
