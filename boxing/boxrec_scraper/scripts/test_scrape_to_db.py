#!/usr/bin/env python3
"""
Test the database-based scraper with a few URLs
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/devin/repos/projects/data-pipelines/boxing/.env')

# PostgreSQL connection
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT'),
    'user': os.getenv('POSTGRES_USER'), 
    'password': os.getenv('POSTGRES_PASSWORD'),
    'database': os.getenv('POSTGRES_DEFAULT_DB')
}

# Create a test CSV with a few URLs
test_urls = """url,boxrec_id
https://boxrec.com/en/box-pro/352,352
https://boxrec.com/en/box-pro/474,474
https://boxrec.com/en/box-pro/6129,6129
"""

with open('data/test_urls.csv', 'w') as f:
    f.write(test_urls)

print("📝 Created test CSV with 3 URLs")
print("🚀 Running scraper...")

# Run the scraper
import subprocess
result = subprocess.run([
    '/Users/devin/repos/projects/data-pipelines/.venv/bin/python',
    'scripts/scrape_to_db.py',
    'data/test_urls.csv',
    '--workers', '3'
], capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)

# Check database
print("\n📊 Checking database...")
conn = psycopg2.connect(**POSTGRES_CONFIG)
cur = conn.cursor()

cur.execute("""
    SELECT url, boxrec_id, scrape_status, 
           length(html_content) as html_size,
           scraped_at
    FROM "data-pipelines-staging".boxrec_html
    ORDER BY scraped_at DESC
    LIMIT 5
""")

print("\nRecent entries in boxrec_html:")
for row in cur.fetchall():
    print(f"  {row[1]}: {row[2]} - {row[3]:,} bytes - {row[4]}")

cur.close()
conn.close()

# Clean up test file
os.remove('data/test_urls.csv')