#!/usr/bin/env python3
"""
Test loading a single record to staging
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

print("Testing single record insert...")

conn = psycopg2.connect(**POSTGRES_CONFIG)
cur = conn.cursor()

try:
    # Test with Mike Tyson
    test_data = (
        'https://boxrec.com/en/box-pro/474',  # url
        '474',                                 # boxrec_id
        'mike-tyson',                         # matched_slug
        'Mike Tyson',                         # boxer_name
        'HTML content here...'                # html_file (truncated for test)
    )
    
    insert_query = """
        INSERT INTO "data-pipelines-staging".boxrec_scraper 
        (url, boxrec_id, matched_slug, boxer_name, html_file)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (boxrec_id) DO UPDATE SET
            url = EXCLUDED.url,
            matched_slug = EXCLUDED.matched_slug,
            boxer_name = EXCLUDED.boxer_name,
            html_file = EXCLUDED.html_file,
            updated_at = CURRENT_TIMESTAMP
    """
    
    print(f"Inserting: {test_data[:4]}...")
    cur.execute(insert_query, test_data)
    conn.commit()
    
    # Check if it worked
    cur.execute('SELECT COUNT(*) FROM "data-pipelines-staging".boxrec_scraper WHERE boxrec_id = %s', ('474',))
    count = cur.fetchone()[0]
    
    print(f"✅ Success! Record count for Mike Tyson: {count}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
    
finally:
    cur.close()
    conn.close()