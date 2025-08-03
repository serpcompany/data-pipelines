"""Configuration for boxing data pipeline."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # data-pipelines/
PIPELINES_ROOT = Path(__file__).parent.parent.parent  # pipelines/
PIPELINE_ROOT = Path(__file__).parent.parent  # pipelines/boxing/

# Load environment variables
load_dotenv(PROJECT_ROOT / '.env')

# API Configuration
ZYTE_API_KEY = os.getenv('ZYTE_API_KEY')
ZYTE_API_URL = "https://api.zyte.com/v1/extract"

# Directories
DATA_DIR = PIPELINE_ROOT / 'data'
INPUT_DIR = DATA_DIR / 'input'
OUTPUT_DIR = DATA_DIR / 'output'
HTML_DIR = OUTPUT_DIR / 'html'
PENDING_HTML_DIR = HTML_DIR / 'pending'  # Unvalidated HTML files
VALIDATED_HTML_DIR = HTML_DIR / 'validated'  # Validated HTML files
LOG_DIR = PIPELINE_ROOT / 'logs'

# Create directories
for directory in [DATA_DIR, INPUT_DIR, OUTPUT_DIR, HTML_DIR, PENDING_HTML_DIR, VALIDATED_HTML_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database
STAGING_MIRROR_DB_PATH = OUTPUT_DIR / 'staging_mirror.db'

# Scraper settings
DEFAULT_WORKERS = 5
DEFAULT_RATE_LIMIT = 5  # requests per second
REQUEST_TIMEOUT = 30

# PostgreSQL configuration
POSTGRES_HOST = os.getenv('POSTGRES_HOST', '38.99.106.18')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5978')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DEFAULT_DB', 'postgres')

def get_postgres_connection():
    """Get PostgreSQL connection for data lake."""
    import psycopg2
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB
    )