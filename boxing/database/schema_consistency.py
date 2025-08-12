#!/usr/bin/env python3
"""
Schema Consistency Manager for Boxing Data Pipeline

Compares schemas between production--productionPreview--datapipeline
"""

import json
import logging
import sqlite3
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

from cloudflare import Cloudflare

logger = logging.getLogger(__name__)


class SchemaConsistencyManager:

    def __init__(self):
        self.database_dir = Path(__file__).parent
        self.report_path = self.database_dir / "schema_consistency_report.json"
        self.schemas_cache_dir = self.database_dir / "cached_schemas"

        # Tables to ignore in comparisons
        self.ignored_tables = {
            "d1_migrations",
            "_hub_migrations",
            "sqlite_sequence",  # SQLite internal table
        }

        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.d1_database_id = os.getenv("D1_DATABASE_ID")
        self.d1_preview_database_id = os.getenv("D1_PREVIEW_DATABASE_ID")
        self.api_token = os.getenv("CLOUDFLARE_D1_TOKEN") or os.getenv(
            "CLOUDFLARE_API_TOKEN"
        )
        self.staging_db = (
            self.database_dir / ".." / "data" / "output" / "staging_mirror.db"
        )

        # Ensure cache directory exists
        self.schemas_cache_dir.mkdir(exist_ok=True)

    def _d1_query(self, client: Cloudflare, database_id: str, sql: str) -> Any:
        """Query D1 database via Cloudflare API."""
        return client.d1.database.query(
            account_id=self.account_id, database_id=database_id, sql=sql, params=[]
        )

    def _get_d1_schema(self, database_id: str, env_name: str) -> Optional[Dict]:
        """Get schema from D1 database using export API."""
        try:
            client = Cloudflare(api_token=self.api_token)

            # Export schema
            logger.info(f"Starting schema export for {env_name}...")
            export_response = client.d1.database.export(
                account_id=self.account_id,
                database_id=database_id,
                output_format="polling",
                dump_options={
                    "no_data": True,  # Schema only
                    "tables": [],  # All tables
                },
            )

            if not export_response.success:
                logger.error(f"Failed to start export for {env_name}")
                return None

            # Poll for completion
            import time

            max_attempts = 30
            attempt = 0
            bookmark = export_response.at_bookmark

            while attempt < max_attempts:
                poll_response = client.d1.database.export(
                    account_id=self.account_id,
                    database_id=database_id,
                    output_format="polling",
                    current_bookmark=bookmark,
                )

                if poll_response.status == "complete":
                    logger.info(f"Export complete for {env_name}")
                    if poll_response.result and poll_response.result.signed_url:
                        # Download and save the raw SQL, then parse schema
                        schema = self._parse_sql_from_url(
                            poll_response.result.signed_url, env_name
                        )
                        # Apply ignore list
                        if schema:
                            filtered_schema = {
                                table: info
                                for table, info in schema.items()
                                if table not in self.ignored_tables
                            }
                            return filtered_schema
                        return schema
                    break
                elif poll_response.status == "error":
                    logger.error(f"Export failed for {env_name}: {poll_response.error}")
                    break

                attempt += 1
                time.sleep(2)  # Wait 2 seconds between polls

            logger.error(
                f"Export timed out for {env_name} after {max_attempts} attempts"
            )
            return None

        except Exception as e:
            logger.error(f"Failed to get {env_name} schema: {e}")
            return None

    def _parse_sql_from_url(self, signed_url: str, env_name: str) -> Optional[Dict]:
        """Download and parse SQL schema from signed URL."""
        try:
            import requests

            response = requests.get(signed_url, timeout=30)
            response.raise_for_status()

            sql_content = response.text

            # Save raw SQL for debugging
            sql_cache_path = self.schemas_cache_dir / f"{env_name}_schema.sql"
            with open(sql_cache_path, "w", encoding="utf-8") as f:
                f.write(sql_content)
            logger.info(f"Saved raw SQL schema to: {sql_cache_path}")

            return self._parse_sql_schema(sql_content)

        except Exception as e:
            logger.error(f"Failed to download/parse SQL for {env_name}: {e}")
            return None

    def _parse_sql_schema(self, sql_content: str) -> Dict:
        """Parse SQL schema to extract table and column information."""
        schema = {}

        # Parse CREATE TABLE statements
        table_pattern = (
            r'CREATE TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+["`]?(\w+)["`]?\s*\((.*?)\);'
        )
        table_matches = re.findall(
            table_pattern, sql_content, re.DOTALL | re.IGNORECASE
        )

        for table_name, table_def in table_matches:
            columns = []
            indexes = []

            # Parse column definitions
            # Split by comma but keep track of parentheses depth
            column_parts = []
            current_part = ""
            paren_depth = 0

            for char in table_def:
                if char == "(":
                    paren_depth += 1
                elif char == ")":
                    paren_depth -= 1
                elif char == "," and paren_depth == 0:
                    column_parts.append(current_part.strip())
                    current_part = ""
                    continue
                current_part += char

            if current_part.strip():
                column_parts.append(current_part.strip())

            for part in column_parts:
                part = part.strip()
                if (
                    not part
                    or part.upper().startswith("FOREIGN KEY")
                    or part.upper().startswith("PRIMARY KEY")
                ):
                    continue

                # Extract column info
                col_match = re.match(r'["`]?(\w+)["`]?\s+(\w+)(.*)$', part)
                if col_match:
                    col_name = col_match.group(1)
                    col_type = col_match.group(2)
                    col_constraints = col_match.group(3)

                    # Parse constraints
                    is_primary_key = "PRIMARY KEY" in col_constraints.upper()
                    is_not_null = "NOT NULL" in col_constraints.upper()

                    # Extract default value
                    default_match = re.search(
                        r"DEFAULT\s+([^,\s]+)", col_constraints, re.IGNORECASE
                    )
                    default_value = default_match.group(1) if default_match else None

                    columns.append(
                        {
                            "name": col_name,
                            "type": col_type.lower(),
                            "primary_key": is_primary_key,
                            "not_null": is_not_null,
                            "default": default_value,
                        }
                    )

            schema[table_name] = {"columns": columns, "indexes": indexes}

        # Parse CREATE INDEX statements
        index_pattern = (
            r"CREATE\s+(UNIQUE\s+)?INDEX\s+`?(\w+)`?\s+ON\s+`?(\w+)`?\s*\(([^)]+)\)"
        )
        index_matches = re.findall(index_pattern, sql_content, re.IGNORECASE)

        for unique, index_name, table_name, columns_str in index_matches:
            if table_name in schema:
                columns = [col.strip().strip("`") for col in columns_str.split(",")]
                schema[table_name]["indexes"].append(
                    {
                        "name": index_name,
                        "unique": bool(unique.strip()),
                        "columns": columns,
                    }
                )

        return schema

    def fetch_production_schema(self) -> Optional[Dict]:
        """Get schema from production D1 database."""
        if not self.d1_database_id:
            logger.error("D1_DATABASE_ID not set")
            return None
        return self._get_d1_schema(self.d1_database_id, "production")

    def fetch_production_preview_schema(self) -> Optional[Dict]:
        """Get schema from production preview D1 database."""
        if not self.d1_preview_database_id:
            logger.error("D1_PREVIEW_DATABASE_ID not set")
            return None
        return self._get_d1_schema(self.d1_preview_database_id, "productionPreview")

    def fetch_datapipeline_schema(self) -> Optional[Dict]:
        """Get schema from local SQLite staging database."""
        if not self.staging_db.exists():
            logger.error(f"Staging database not found: {self.staging_db}")
            return None

        try:
            conn = sqlite3.connect(str(self.staging_db))
            cursor = conn.cursor()

            # Get tables
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """
            )
            tables = [row[0] for row in cursor.fetchall()]

            schema = {}
            for table in tables:
                # Skip ignored tables
                if table in self.ignored_tables:
                    continue

                # Get columns
                cursor.execute(f"PRAGMA table_info({table})")
                columns = []
                for col_info in cursor.fetchall():
                    cid, name, data_type, notnull, default_value, pk = col_info
                    columns.append(
                        {
                            "name": name,
                            "type": data_type.lower(),
                            "primary_key": bool(pk),
                            "not_null": bool(notnull),
                            "default": default_value,
                        }
                    )

                # Get indexes
                cursor.execute(f"PRAGMA index_list({table})")
                indexes = []
                for idx_info in cursor.fetchall():
                    seq, name, unique, origin, partial = idx_info
                    if origin == "c":  # Custom indexes only
                        cursor.execute(f"PRAGMA index_info({name})")
                        index_columns = [row[2] for row in cursor.fetchall()]
                        indexes.append(
                            {
                                "name": name,
                                "unique": bool(unique),
                                "columns": index_columns,
                            }
                        )

                schema[table] = {"columns": columns, "indexes": indexes}

            # Save datapipeline schema for debugging
            schema_cache_path = self.schemas_cache_dir / "datapipeline_schema.json"
            with open(schema_cache_path, "w") as f:
                json.dump(schema, f, indent=2)
            logger.info(f"Saved datapipeline schema to: {schema_cache_path}")

            conn.close()
            return schema

        except Exception as e:
            logger.error(f"Failed to get datapipeline schema: {e}")
            return None

    def compare_schemas(
        self, schema1: Dict, schema2: Dict, env1_name: str, env2_name: str
    ) -> List[str]:
        """Compare two schemas and return differences."""
        differences = []

        if not schema1:
            differences.append(f"Could not fetch {env1_name} schema")
            return differences
        if not schema2:
            differences.append(f"Could not fetch {env2_name} schema")
            return differences

        # Compare tables
        tables1 = set(schema1.keys())
        tables2 = set(schema2.keys())

        for table in tables1 - tables2:
            differences.append(
                f"Table '{table}' exists in {env1_name} but not in {env2_name}"
            )

        for table in tables2 - tables1:
            differences.append(
                f"Table '{table}' exists in {env2_name} but not in {env1_name}"
            )

        # Compare columns for common tables
        for table in tables1 & tables2:
            cols1 = {col["name"]: col for col in schema1[table]["columns"]}
            cols2 = {col["name"]: col for col in schema2[table]["columns"]}

            cols1_names = set(cols1.keys())
            cols2_names = set(cols2.keys())

            for col in cols1_names - cols2_names:
                differences.append(
                    f"Table '{table}': column '{col}' exists in {env1_name} but not in {env2_name}"
                )

            for col in cols2_names - cols1_names:
                differences.append(
                    f"Table '{table}': column '{col}' exists in {env2_name} but not in {env1_name}"
                )

            # Compare column types for common columns
            for col in cols1_names & cols2_names:
                if cols1[col]["type"] != cols2[col]["type"]:
                    differences.append(
                        f"Table '{table}', column '{col}': type differs - "
                        f"{env1_name}:{cols1[col]['type']} vs {env2_name}:{cols2[col]['type']}"
                    )

        return differences

    def validate_all_environments(self) -> Dict[str, Any]:
        """Compare schemas across all three environments."""
        logger.info("Fetching schemas from all environments...")

        # Check required config
        missing_config = []
        if not self.account_id:
            missing_config.append("CLOUDFLARE_ACCOUNT_ID")
        if not self.api_token:
            missing_config.append("CLOUDFLARE_D1_TOKEN or CLOUDFLARE_API_TOKEN")
        if not self.d1_database_id:
            missing_config.append("D1_DATABASE_ID")
        if not self.d1_preview_database_id:
            missing_config.append("D1_PREVIEW_DATABASE_ID")

        if missing_config:
            logger.error(
                f"Missing required environment variables: {', '.join(missing_config)}"
            )
            return {
                "error": f"Missing config: {', '.join(missing_config)}",
                "timestamp": datetime.now().isoformat(),
            }

        # Fetch schemas
        production_schema = self.fetch_production_schema()
        preview_schema = self.fetch_production_preview_schema()
        datapipeline_schema = self.fetch_datapipeline_schema()

        results = {
            "timestamp": datetime.now().isoformat(),
            "schema_availability": {
                "production": production_schema is not None,
                "productionPreview": preview_schema is not None,
                "datapipeline": datapipeline_schema is not None,
            },
            "comparisons": {},
            "overall_consistent": False,
            "total_differences": 0,
        }

        # Compare production vs production preview
        prod_vs_preview_diffs = self.compare_schemas(
            production_schema, preview_schema, "production", "productionPreview"
        )
        results["comparisons"][
            "production_vs_productionPreview"
        ] = prod_vs_preview_diffs

        # Compare production vs datapipeline
        prod_vs_pipeline_diffs = self.compare_schemas(
            production_schema, datapipeline_schema, "production", "datapipeline"
        )
        results["comparisons"]["production_vs_datapipeline"] = prod_vs_pipeline_diffs

        # Compare production preview vs datapipeline
        preview_vs_pipeline_diffs = self.compare_schemas(
            preview_schema, datapipeline_schema, "productionPreview", "datapipeline"
        )
        results["comparisons"][
            "productionPreview_vs_datapipeline"
        ] = preview_vs_pipeline_diffs

        # Calculate totals
        all_diffs = (
            prod_vs_preview_diffs + prod_vs_pipeline_diffs + preview_vs_pipeline_diffs
        )
        results["total_differences"] = len(all_diffs)
        results["overall_consistent"] = len(all_diffs) == 0

        # Save report
        with open(self.report_path, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Report saved to: {self.report_path}")
        return results


def run_schema_consistency_check():
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    manager = SchemaConsistencyManager()
    results = manager.validate_all_environments()

    if "error" in results:
        print(f"❌ Configuration Error: {results['error']}")
        return False

    print("\n" + "=" * 70)
    print("SCHEMA CONSISTENCY REPORT")
    print("=" * 70)
    print(f"Generated: {results['timestamp']}")
    print(
        f"Overall Status: {'✅ CONSISTENT' if results['overall_consistent'] else '❌ INCONSISTENT'}"
    )
    print(f"Total Differences: {results['total_differences']}")

    print(f"\nSchema Availability:")
    for env, available in results["schema_availability"].items():
        status = "✅ Available" if available else "❌ Failed to fetch"
        print(f"  {env}: {status}")

    print(f"\nComparisons:")
    for comparison_name, differences in results["comparisons"].items():
        readable_name = comparison_name.replace("_vs_", " ↔ ")
        print(f"\n  {readable_name}:")
        if not differences:
            print("    ✅ No differences")
        else:
            print(f"    ❌ {len(differences)} differences:")
            for diff in differences:
                print(f"      - {diff}")

    print(f"\nFull report saved to: {manager.report_path}")

    return results["overall_consistent"]


if __name__ == "__main__":
    success = run_schema_consistency_check()
    exit(0 if success else 1)
