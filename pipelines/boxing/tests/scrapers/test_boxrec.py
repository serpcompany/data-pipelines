#!/usr/bin/env python3
"""Tests for BoxRec scraper."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from pipelines.boxing.scrapers.boxrec.boxer import (
    create_filename_from_url,
    load_urls_from_csv
)


def test_create_filename_from_url():
    """Test URL to filename conversion."""
    # Test box-pro URLs
    assert create_filename_from_url("https://boxrec.com/en/box-pro/352") == "en_box-pro_352.html"
    assert create_filename_from_url("https://boxrec.com/es/box-pro/123") == "es_box-pro_123.html"
    
    # Test other URLs
    assert create_filename_from_url("https://boxrec.com/en/event/1234").endswith(".html")


def test_load_urls_from_csv(tmp_path):
    """Test loading URLs from CSV file."""
    # Create test CSV
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("URL\nhttps://boxrec.com/en/box-pro/1\nhttps://boxrec.com/en/box-pro/2")
    
    urls = load_urls_from_csv(csv_file)
    assert len(urls) == 2
    assert urls[0] == "https://boxrec.com/en/box-pro/1"
    assert urls[1] == "https://boxrec.com/en/box-pro/2"


@patch('pipelines.boxing.scrapers.boxrec.boxer.requests.post')
def test_download_html_success(mock_post):
    """Test successful HTML download."""
    # Mock successful response
    mock_response = Mock()
    mock_response.json.return_value = {
        "httpResponseBody": "PGh0bWw+VGVzdDwvaHRtbD4="  # base64 encoded "<html>Test</html>"
    }
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    # Test would go here - but need to refactor boxrec.py to be more testable first
    # (separate download logic from file writing, etc.)