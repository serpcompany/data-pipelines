#!/usr/bin/env python3
"""
Change detection for HTML content in the data lake.
Compares current HTML with stored hashes to detect updates.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import psycopg2

try:
    from ..utils.config import get_postgres_connection
    from .metadata import MetadataTracker
except ImportError:
    # Fall back to absolute import (when run as script)
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from boxing.utils.config import get_postgres_connection
    from boxing.database.metadata import MetadataTracker

logger = logging.getLogger(__name__)


class ChangeDetector:
    """Detect changes in boxer HTML pages."""

    def __init__(self, min_check_interval_days: int = 7):
        """
        Initialize change detector.

        Args:
            min_check_interval_days: Minimum days between checks for the same URL
        """
        self.min_check_interval = timedelta(days=min_check_interval_days)

    def get_urls_to_check(self, limit: Optional[int] = None) -> List[Dict]:
        """Get URLs that should be checked for changes."""
        with MetadataTracker() as tracker:
            cursor = tracker.staging_conn.cursor()

            # Calculate cutoff time
            cutoff_time = datetime.now() - self.min_check_interval

            query = """
                SELECT boxrec_url, boxrec_id, last_checked_at, html_hash
                FROM data_lake_metadata
                WHERE last_checked_at < ? OR last_checked_at IS NULL
                ORDER BY 
                    CASE WHEN last_checked_at IS NULL THEN 0 ELSE 1 END,
                    last_checked_at ASC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, (cutoff_time,))

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "boxrec_url": row[0],
                        "boxrec_id": row[1],
                        "last_checked_at": row[2],
                        "current_hash": row[3],
                    }
                )

            return results

    def check_for_changes(self, boxrec_url: str, new_html: str) -> Dict:
        """
        Check if HTML content has changed since last scrape.

        Returns:
            Dict with change information
        """
        with MetadataTracker() as tracker:
            result = tracker.track_scraped_html(
                boxrec_url=boxrec_url,
                boxrec_id=boxrec_url.split("/")[-1],  # Extract ID from URL
                html_content=new_html,
                scraped_at=datetime.now(),
            )

            return result

    def bulk_check_changes(self, limit: int = 100) -> Dict:
        """
        Check multiple URLs for changes.

        Returns:
            Summary of changes detected
        """
        urls_to_check = self.get_urls_to_check(limit=limit)

        if not urls_to_check:
            logger.info("No URLs need checking at this time")
            return {"checked": 0, "changed": 0, "errors": 0}

        logger.info(f"Checking {len(urls_to_check)} URLs for changes")

        checked = 0
        changed = 0
        errors = 0
        changes_detected = []

        # Get Postgres connection for fetching HTML
        pg_conn = get_postgres_connection()
        pg_cursor = pg_conn.cursor()

        for url_info in urls_to_check:
            try:
                # Fetch current HTML from data lake
                pg_cursor.execute(
                    """
                    SELECT html_file
                    FROM "data-pipelines-raw".boxrec
                    WHERE boxrec_url = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    (url_info["boxrec_url"],),
                )

                result = pg_cursor.fetchone()
                if not result:
                    logger.warning(
                        f"No HTML found in data lake for {url_info['boxrec_url']}"
                    )
                    continue

                current_html = result[0]

                # Check for changes
                change_result = self.check_for_changes(
                    boxrec_url=url_info["boxrec_url"], new_html=current_html
                )

                checked += 1

                if change_result.get("change_detected"):
                    changed += 1
                    changes_detected.append(
                        {
                            "url": url_info["boxrec_url"],
                            "previous_hash": change_result.get("previous_hash"),
                            "new_hash": change_result.get("new_hash"),
                            "last_checked": url_info["last_checked_at"],
                        }
                    )
                    logger.info(f"Change detected for {url_info['boxrec_url']}")

            except Exception as e:
                logger.error(f"Error checking {url_info['boxrec_url']}: {e}")
                errors += 1

        pg_conn.close()

        summary = {
            "checked": checked,
            "changed": changed,
            "errors": errors,
            "changes": changes_detected[:10],  # First 10 changes
        }

        logger.info(
            f"Change detection complete: {checked} checked, {changed} changed, {errors} errors"
        )

        return summary

    def get_change_report(self) -> Dict:
        """Generate a report of all detected changes."""
        with MetadataTracker() as tracker:
            changed_urls = tracker.get_changed_urls()

            report = {
                "total_changes": len(changed_urls),
                "changes_by_date": {},
                "recent_changes": [],
            }

            # Group by date
            for change in changed_urls:
                date_key = (
                    change["last_checked_at"].date()
                    if change["last_checked_at"]
                    else "unknown"
                )
                if date_key not in report["changes_by_date"]:
                    report["changes_by_date"][date_key] = 0
                report["changes_by_date"][date_key] += 1

            # Recent changes (last 7 days)
            recent_cutoff = datetime.now() - timedelta(days=7)
            report["recent_changes"] = [
                change
                for change in changed_urls
                if change["last_checked_at"]
                and change["last_checked_at"] > recent_cutoff
            ]

            return report


def run_change_detection(limit: int = 100):
    """Run change detection as a scheduled task."""
    logger.info("Starting change detection run")

    detector = ChangeDetector()
    summary = detector.bulk_check_changes(limit=limit)

    # Log summary
    logger.info(f"Change detection summary: {summary}")

    # If changes were detected, log them
    if summary["changed"] > 0:
        report = detector.get_change_report()
        logger.info(f"Total changes in system: {report['total_changes']}")
        logger.info(f"Recent changes (last 7 days): {len(report['recent_changes'])}")

    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Run change detection
    run_change_detection(limit=10)
