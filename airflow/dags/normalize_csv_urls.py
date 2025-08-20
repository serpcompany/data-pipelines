"""
Normalize URLs in CSV files and remove duplicates
"""

from __future__ import annotations

from datetime import datetime
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
import pandas as pd
import os
from typing import List, Dict, Any


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


@dag(
    dag_id="normalize_csv_urls",
    description="Normalize URLs in CSV files and remove duplicates",
    default_args=DEFAULT_ARGS,
    schedule=None,  # Manual trigger
    catchup=False,
    tags=["csv", "url", "normalization"],
    params={
        # Required at run time: {"csv_filename": "your_file.csv"}
        "csv_filename": "",
    },
    max_active_runs=1,
)
def normalize_csv_urls():
    @task
    def read_input_csv() -> Dict[str, Any]:
        """Read the specified CSV file and validate it has URL columns."""
        ctx = get_current_context()
        params = ctx.get("params", {}) or {}
        csv_filename = params.get("csv_filename", "")

        if not csv_filename:
            raise ValueError("csv_filename parameter is required")

        if not csv_filename.endswith(".csv"):
            raise ValueError(f"Invalid filename: {csv_filename}. Must end with .csv")

        filepath = os.path.join(INPUT_DIR, csv_filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Specified CSV file not found: {filepath}")

        print(f"Reading CSV file: {filepath}")
        df = pd.read_csv(filepath)

        # Check for URL columns
        url_columns = [col for col in df.columns if "url" in str(col).lower()]
        if not url_columns:
            raise ValueError(f"No URL columns found in {csv_filename}")

        print(f"Found {len(df)} rows with URL columns: {url_columns}")

        return {
            "filepath": filepath,
            "filename": csv_filename,
            "original_rows": len(df),
            "url_columns": url_columns,
            "total_columns": len(df.columns),
        }

    @task
    def normalize_and_dedupe_urls(csv_info: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize URLs and remove duplicates."""
        df = pd.read_csv(csv_info["filepath"])
        original_count = len(df)

        print(f"Processing {original_count} rows...")

        # Process each URL column
        for url_col in csv_info["url_columns"]:
            print(f"Normalizing column: {url_col}")

            def normalize_url(url):
                if pd.isna(url):
                    return url

                url = str(url)
                # Remove query parameters and fragments, normalize trailing slash
                url = url.split("%2")[0].split("?")[0].rstrip("/")

                if "." in url and url[url.rfind(".") - 1].isdigit():
                    url = url[: url.rfind(".")].rstrip("/")

                return url

            # Apply normalization
            df[url_col] = df[url_col].apply(normalize_url)

        # Remove duplicates based on URL columns
        before_dedup = len(df)
        df = df.drop_duplicates(subset=csv_info["url_columns"], keep="first")
        after_dedup = len(df)

        duplicates_removed = before_dedup - after_dedup

        # Generate output filename with _normalized suffix
        input_name = csv_info["filename"]
        if input_name.endswith(".csv"):
            output_name = input_name[:-4] + "_normalized.csv"
        else:
            output_name = input_name + "_normalized"

        output_path = os.path.join(INPUT_DIR, output_name)

        print(f"Saving normalized CSV to: {output_path}")
        df.to_csv(output_path, index=False)

        return {
            "input_file": csv_info["filepath"],
            "output_file": output_path,
            "output_filename": output_name,
            "original_rows": original_count,
            "final_rows": after_dedup,
            "duplicates_removed": duplicates_removed,
            "url_columns_processed": csv_info["url_columns"],
        }

    @task
    def generate_report(results: Dict[str, Any]) -> str:
        """Generate a final report of the URL normalization process."""
        print("\n" + "=" * 60)
        print("URL NORMALIZATION AND DEDUPLICATION REPORT")
        print("=" * 60)
        print(f"Input file: {os.path.basename(results['input_file'])}")
        print(f"Output file: {results['output_filename']}")
        print(f"URL columns processed: {', '.join(results['url_columns_processed'])}")
        print(f"Original rows: {results['original_rows']:,}")
        print(f"Final rows: {results['final_rows']:,}")
        print(f"Duplicates removed: {results['duplicates_removed']:,}")

        if results["duplicates_removed"] > 0:
            reduction_pct = (
                results["duplicates_removed"] / results["original_rows"]
            ) * 100
            print(f"Reduction: {reduction_pct:.1f}%")
        else:
            print("No duplicates found")

        print(f"Processing complete: {results['output_filename']}")
        print("=" * 60)

        return f"Processed {results['original_rows']:,} → {results['final_rows']:,} rows (-{results['duplicates_removed']:,} duplicates)"

    # DAG workflow
    csv_info = read_input_csv()
    normalized_results = normalize_and_dedupe_urls(csv_info)
    final_report = generate_report(normalized_results)


# Create DAG instance
dag = normalize_csv_urls()
