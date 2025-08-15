"""
Scrape HTML files with Zyte
"""

from __future__ import annotations

from datetime import datetime
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
import pandas as pd
import requests
import time
import os
import base64
import psycopg2
import sqlite3
import sys
from typing import List, Dict, Any, Tuple, Optional

sys.path.append("/opt/airflow/boxing")

from boxing.run_validators import validate_html_file
from boxing.load.to_data_lake import prepare_file_data, DB_CONFIG
from boxing.transform import normalize_boxer_id
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

INPUT_DIR = "/opt/airflow/data/input"
ZYTE_API_URL = "https://api.zyte.com/v1/extract"


@dag(
    dag_id="scrape_html_zyte",
    description="Scrape HTML from URLs using Zyte API",
    default_args=DEFAULT_ARGS,
    schedule=None,  # Manual trigger
    catchup=False,
    tags=["scraping", "zyte"],
    params={
        # Required at run time: {"csv_filename": "your_file.csv"}
        "csv_filename": "",
        "batch_size": 50,  # Number of URLs per batch to avoid xcom issues
        "entity": "boxer",  # Entity type: boxer or bout
    },
    max_active_runs=1,  # Only one DAG run at a time
    max_active_tasks=5,  # Limit total concurrent tasks across the DAG
)
def scrape_html_zyte():
    @task
    def read_csv_files() -> List[Dict[str, Any]]:
        """Read the specified CSV (from DAG run params) and return basic file metadata."""
        ctx = get_current_context()
        params = ctx.get("params", {}) or {}
        specific_file = params.get("csv_filename", "")

        if not specific_file:
            raise ValueError("csv_filename parameter is required")

        if not specific_file.endswith(".csv"):
            raise ValueError(f"Invalid filename: {specific_file}. Must end with .csv")

        filepath = os.path.join(INPUT_DIR, specific_file)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Specified CSV file not found: {filepath}")

        print(f"Reading specified file: {filepath}")
        df = pd.read_csv(filepath)

        return [
            {
                "filename": specific_file,
                "filepath": filepath,
                "rows": len(df),
                "columns": list(df.columns),
            }
        ]

    @task
    def validate_csv_structure(csv_files: List[Dict[str, Any]]) -> List[str]:
        """Validate the CSV(s) have required columns."""
        valid_files: List[str] = []

        for file_info in csv_files:
            df = pd.read_csv(file_info["filepath"])
            has_url_column = any("url" in str(col).lower() for col in df.columns)

            if has_url_column:
                valid_files.append(file_info["filepath"])
                print(f"✓ Valid: {file_info['filename']}")
            else:
                print(f"✗ Invalid: {file_info['filename']} - missing URL column")

        return valid_files

    @task
    def extract_urls(valid_files: List[str]) -> List[List[str]]:
        """Extract unique URLs from all valid CSVs and batch them to avoid xcom issues."""
        from airflow.operators.python import get_current_context

        ctx = get_current_context()
        params = ctx.get("params", {}) or {}
        batch_size = int(params.get("batch_size", 50))  # Default batch size for URLs

        all_urls: List[str] = []

        for filepath in valid_files:
            df = pd.read_csv(filepath)
            url_col = next((c for c in df.columns if "url" in str(c).lower()), None)
            if url_col:
                urls = df[url_col].dropna().astype(str).tolist()
                for url in urls:
                    url = url.split("%2")[0].split("?")[0].rstrip("/")

                    if "." in url and url[url.rfind(".") - 1].isdigit():
                        url = url[: url.rfind(".")].rstrip("/")

                    all_urls.append(url)
                print(f"Extracted {len(urls)} URLs from {os.path.basename(filepath)}")

        unique_urls = list(set(all_urls))
        print(f"Total unique URLs: {len(unique_urls)}")

        # Create batches to avoid xcom size issues
        batches: List[List[str]] = [
            unique_urls[i : i + batch_size]
            for i in range(0, len(unique_urls), batch_size)
        ]
        print(f"Created {len(batches)} batches with batch size {batch_size}")
        return batches

    @task
    def process_batch_urls(url_batch: List[str]) -> List[Dict[str, Any]]:
        """Process a batch of URLs sequentially to avoid xcom issues."""
        results: List[Dict[str, Any]] = []

        for url in url_batch:
            result = process_single_url_internal(url)
            results.append(result)

        return results

    def process_single_url_internal(url: str) -> Dict[str, Any]:
        """Internal function to process a single URL (moved from @task decorator)."""
        print(f"Processing: {url}")

        # Check if recently scraped
        HOURS_THRESHOLD = int(
            os.environ.get("SCRAPE_THRESHOLD_HOURS", "720")
        )  # Default 30 days (720 hours)
        is_recent, last_scraped = check_if_recently_scraped(url, HOURS_THRESHOLD)

        if is_recent:
            print(f"✓ Skipping {url} - already scraped at {last_scraped}")
            return {
                "url": url,
                "status": "skipped",
                "step": "check_db",
                "last_scraped": last_scraped.isoformat() if last_scraped else None,
                "reason": f"Already scraped within {HOURS_THRESHOLD} hours",
                "timestamp": datetime.now().isoformat(),
            }

        print(
            f"→ Need to scrape {url} - not found or older than {HOURS_THRESHOLD} hours"
        )

        # Scrape with Zyte
        api_key = os.environ.get("ZYTE_API_KEY")
        if not api_key:
            raise ValueError("ZYTE_API_KEY not set in environment variables")
        auth_header = base64.b64encode(f"{api_key}:".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json",
        }

        payload = {
            "url": url,
            "httpResponseHeaders": True,
            "browserHtml": True,
        }

        MAX_RETRIES = int(os.environ.get("SCRAPE_MAX_RETRIES", "3"))
        BASE_DELAY = int(os.environ.get("SCRAPE_BASE_DELAY", "5"))

        returnValue = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                if attempt > 0:
                    delay = BASE_DELAY + (2 ** (attempt - 1))
                    print(f"Retrying {url} in {delay} seconds...")
                    time.sleep(delay)

                response = requests.post(
                    ZYTE_API_URL, json=payload, headers=headers, timeout=60
                )

                if response.status_code != 200:
                    returnValue = {
                        "url": url,
                        "status": "failed",
                        "step": "scrape",
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "timestamp": datetime.now().isoformat(),
                    }
                    continue

                data = response.json()
                html_content = data.get("browserHtml", data.get("httpResponseBody"))

                if isinstance(html_content, bytes):
                    html_content = html_content.decode("utf-8", errors="ignore")

                if not html_content:
                    returnValue = {
                        "url": url,
                        "status": "failed",
                        "step": "scrape",
                        "error": "No HTML content returned",
                        "timestamp": datetime.now().isoformat(),
                    }
                    continue

                print(f"✓ Scraped: {url}")

                # Validate HTML
                is_valid, reason = validate_html_file_content(html_content, url)

                if not is_valid:
                    returnValue = {
                        "url": url,
                        "status": "failed",
                        "step": "validate",
                        "error": f"Validation failed: {reason}",
                        "timestamp": datetime.now().isoformat(),
                    }
                    continue

                print(f"✓ Validated: {url}")

                # Upload to Data Lake
                success = upload_to_data_lake(url, html_content)

                if not success:
                    returnValue = {
                        "url": url,
                        "status": "failed",
                        "step": "upload",
                        "error": "Failed to upload to data lake",
                        "timestamp": datetime.now().isoformat(),
                    }
                    continue

                print(f"✓ Uploaded to data lake: {url}")

                return {
                    "url": url,
                    "status": "success",
                    "step": "completed",
                    "timestamp": datetime.now().isoformat(),
                }

            except Exception as e:
                returnValue = {
                    "url": url,
                    "status": "failed",
                    "step": "scrape",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                continue

        # If we reach here, all retries failed
        return returnValue

    def validate_html_file_content(html_content: str, url: str) -> Tuple[bool, str]:
        """Validate HTML content using the existing validation logic."""
        from boxing.validators import (
            blank_page,
            error_page,
            login_page,
            rate_limit,
            file_size,
        )
        from boxing.validators.page import boxer, event

        # Check file size first
        if not file_size.validate(html_content):
            return False, "File too small"

        # Check for error pages
        if not error_page.validate(html_content):
            return False, "Error page detected"

        # Check for login page
        if not login_page.validate(html_content):
            return False, "Login page detected"

        # Check for rate limiting
        if not rate_limit.validate(html_content):
            return False, "Rate limit page detected"

        # Check for blank page
        is_valid, message = blank_page.validate(html_content, url)
        if not is_valid:
            return False, f"Blank page: {message}"

        # Check if it's a valid page based on entity type
        from airflow.operators.python import get_current_context

        ctx = get_current_context()
        params = ctx.get("params", {}) or {}
        entity = params.get("entity", "boxer")

        if entity == "boxer":
            if not boxer.validate(html_content):
                return False, "Not a valid boxer page"
        elif entity == "bout":
            if not event.validate(html_content):
                return False, "Not a valid bout/event page"

        return True, "Valid"

    def check_if_recently_scraped(
        url: str, hours_threshold: int = 24
    ) -> Tuple[bool, Optional[datetime]]:
        """
        Check if URL was scraped within the threshold time.
        Also checks local staging DB for boxer proStatus - if 'inactive', returns True to skip.
        Returns (is_recent, last_scraped_time)
        """
        from boxing.load.to_data_lake import (
            extract_boxer_id_from_filename,
            get_competition_level,
        )

        try:
            # Extract metadata from URL based on entity type
            from airflow.operators.python import get_current_context

            ctx = get_current_context()
            params = ctx.get("params", {}) or {}
            entity = params.get("entity", "boxer")

            parts = url.split("/")
            if len(parts) < 2:
                return False, None

            if entity == "boxer":
                # Create a fake filename to reuse existing extraction logic
                fake_filename = f"en_box-pro_{parts[-1]}.html"
                if "box-am" in url:
                    fake_filename = f"en_box-am_{parts[-1]}.html"

                boxer_id = extract_boxer_id_from_filename(fake_filename)
                competition_level = get_competition_level(fake_filename)

                if not boxer_id:
                    return False, None
            elif entity == "bout":
                if len(parts) >= 2:
                    boxer_id = parts[-2] + "_" + parts[-1]  # event_id_bout_id
                    competition_level = "professional"  # Default for bouts
                else:
                    return False, None
            else:
                # For unknown entity types, try to extract some identifier
                boxer_id = parts[-1] if parts else None
                competition_level = (
                    "professional"  # Default to professional for unknown entities
                )
                if not boxer_id:
                    return False, None

            # Only check staging DB for boxers
            from airflow.operators.python import get_current_context

            ctx = get_current_context()
            params = ctx.get("params", {}) or {}
            entity = params.get("entity", "boxer")

            if entity == "boxer":
                # Check staging DB for proStatus first
                try:
                    staging_conn = get_staging_connection()
                    staging_cur = staging_conn.cursor()

                    staging_cur.execute(
                        "SELECT proStatus FROM boxers WHERE boxrecId = ?", (boxer_id,)
                    )
                    staging_result = staging_cur.fetchone()

                    staging_cur.close()
                    staging_conn.close()

                    if staging_result and staging_result[0] == "inactive":
                        print(
                            f"✓ Skipping {url} - boxer is inactive (proStatus: inactive)"
                        )
                        return True, None  # Skip inactive boxers

                except Exception as staging_e:
                    print(
                        f"Warning: Could not check staging DB for proStatus: {staging_e}"
                    )
                    # Continue with regular check if staging DB fails

            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # Check if record exists and when it was last scraped
            check_query = """
                SELECT scraped_at, updated_at 
                FROM "data_lake".boxrec 
                WHERE boxrec_id = %s AND competition_level = %s AND entity = %s
            """

            cur.execute(check_query, (boxer_id, competition_level, entity))
            result = cur.fetchone()

            cur.close()
            conn.close()

            if not result:
                return False, None  # No record exists, need to scrape

            scraped_at = result[0]  # This is the timestamp when scraped

            if not scraped_at:
                return False, None  # No scraped timestamp, need to scrape

            # For bouts/events, if we've scraped it once, always skip (they don't change)
            if entity in ["bout", "event"]:
                print(
                    f"✓ Skipping {url} - {entity} already scraped (entity is unchanging)"
                )
                return True, scraped_at

            # For boxers, check if scraped within threshold
            if isinstance(scraped_at, str):
                scraped_at = datetime.fromisoformat(scraped_at.replace("Z", "+00:00"))

            time_diff = datetime.now() - scraped_at.replace(tzinfo=None)
            is_recent = time_diff.total_seconds() < (hours_threshold * 3600)

            return is_recent, scraped_at

        except Exception as e:
            print(f"Error checking if recently scraped: {e}")
            return False, None

    def upload_to_data_lake(url: str, html_content: str) -> bool:
        """Upload validated HTML to PostgreSQL data lake using existing logic."""
        from boxing.load.to_data_lake import (
            extract_boxer_id_from_filename,
            construct_boxrec_url,
            get_competition_level,
        )
        from airflow.operators.python import get_current_context

        try:
            # Get entity type from context
            ctx = get_current_context()
            params = ctx.get("params", {}) or {}
            entity = params.get("entity", "boxer")

            # Extract metadata from URL based on entity type
            parts = url.split("/")
            if len(parts) < 2:
                print(f"Could not parse URL structure: {url}")
                return False

            if entity == "boxer":
                # Create a fake filename to reuse existing extraction logic
                fake_filename = f"en_box-pro_{parts[-1]}.html"
                if "box-am" in url:
                    fake_filename = f"en_box-am_{parts[-1]}.html"

                boxer_id = extract_boxer_id_from_filename(fake_filename)
                competition_level = get_competition_level(fake_filename)

                if not boxer_id:
                    print(f"Could not extract boxer ID from URL: {url}")
                    return False
            elif entity == "bout":
                if len(parts) >= 2:
                    boxer_id = parts[-2] + "_" + parts[-1]  # event_id_bout_id
                    competition_level = "professional"
                else:
                    print(f"Could not extract bout ID from URL: {url}")
                    return False
            else:
                # For unknown entity types, try to extract some identifier
                boxer_id = parts[-1] if parts else None
                competition_level = "professional"
                if not boxer_id:
                    print(f"Could not extract ID from URL: {url}")
                    return False

            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            upsert_query = """
                INSERT INTO "data_lake".boxrec 
                (boxrec_url, boxrec_id, html_file, competition_level, entity, scraped_at, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (boxrec_id, competition_level, entity) 
                DO UPDATE SET 
                    html_file = EXCLUDED.html_file,
                    boxrec_url = EXCLUDED.boxrec_url,
                    scraped_at = EXCLUDED.scraped_at,
                    updated_at = EXCLUDED.updated_at
            """

            now = datetime.now()
            cur.execute(
                upsert_query,
                (url, boxer_id, html_content, competition_level, entity, now, now, now),
            )

            conn.commit()
            cur.close()
            conn.close()

            return True

        except Exception as e:
            print(f"Error uploading to data lake: {e}")
            return False

    @task
    def flatten(all_batch_results: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Flatten the list of lists from mapped batches into one list of results."""
        flat: List[Dict[str, Any]] = []
        for batch in all_batch_results:
            flat.extend(batch or [])
        return flat

    @task
    def report_results(results: List[Dict[str, Any]]) -> str:
        """Print a report of processing results."""
        successful = [r for r in results if r["status"] == "success"]
        skipped = [r for r in results if r["status"] == "skipped"]
        failed = [r for r in results if r["status"] == "failed"]

        # Group failures by step
        failure_by_step = {}
        for fail in failed:
            step = fail.get("step", "unknown")
            if step not in failure_by_step:
                failure_by_step[step] = []
            failure_by_step[step].append(fail)

        print("\n" + "=" * 60)
        print("BOXING DATA PIPELINE SCRAPE REPORT")
        print("=" * 60)
        print(f"Total URLs processed: {len(results)}")
        print(f"Successfully scraped: {len(successful)}")
        print(f"Skipped (recently scraped): {len(skipped)}")
        print(f"Failed: {len(failed)}")
        print(f"Efficiency: {len(skipped)}/{len(results)} URLs avoided re-scraping")

        if failure_by_step:
            print("\nFailures by step:")
            for step, fails in failure_by_step.items():
                print(f"  {step}: {len(fails)} failures")

        if failed:
            print(f"\nFirst 10 failed URLs:")
            for i, fail in enumerate(failed[:10]):
                step = fail.get("step", "unknown")
                error = fail.get("error", "Unknown error")
                print(f"  {i+1}. {fail['url']} [{step}]: {error}")

            if len(failed) > 10:
                print(f"  ... and {len(failed) - 10} more failures")

        if skipped:
            print(f"\nFirst 5 skipped URLs:")
            for i, skip in enumerate(skipped[:5]):
                last_scraped = skip.get("last_scraped", "Unknown")
                if last_scraped and last_scraped != "Unknown":
                    last_scraped = last_scraped[:19]  # Show just date and time part
                print(f"  {i+1}. {skip['url']} (last scraped: {last_scraped})")

        return f"Scraped {len(successful)}, skipped {len(skipped)}, failed {len(failed)} URLs"

    csv_files = read_csv_files()
    valid_files = validate_csv_structure(csv_files)
    url_batches = extract_urls(valid_files)
    # Process URL batches in parallel to avoid xcom issues
    batch_results = process_batch_urls.expand(url_batch=url_batches)
    results = flatten(batch_results)
    report = report_results(results)


# Create DAG instance
dag = scrape_html_zyte()
