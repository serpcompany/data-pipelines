#!/usr/bin/env python3
"""
Test loading a few records to staging database
"""

import os
import csv
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
from pathlib import Path

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

print("Testing load of first 5 records...")

# Connect to PostgreSQL
conn = psycopg2.connect(**POSTGRES_CONFIG)
cur = conn.cursor()

try:
    # Read first 5 records from CSV
    csv_file = 'data/urls.csv'
    html_dir = Path('data/raw/boxrec_html')
    
    data_to_insert = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 5:  # Only process first 5
                break
                
            boxrec_id = row.get('boxrec_id')
            url = row.get('url')
            boxer_name = row.get('name', '')
            matched_slug = row.get('slug', '')
            
            print(f"Processing: {boxer_name} (ID: {boxrec_id})")
            
            # Look for HTML file
            html_content = None
            possible_files = [
                html_dir / f"en_box-pro_{boxrec_id}.html",
                html_dir / f"de_box-pro_{boxrec_id}.html",
                html_dir / f"es_box-pro_{boxrec_id}.html",
                html_dir / f"fr_box-pro_{boxrec_id}.html",
                html_dir / f"ru_box-pro_{boxrec_id}.html"
            ]
            
            for html_file in possible_files:
                if html_file.exists():
                    with open(html_file, 'r', encoding='utf-8') as hf:
                        html_content = hf.read()
                    print(f"  Found HTML: {html_file.name} ({len(html_content)} bytes)")
                    break
            
            if not html_content:
                print(f"  ⚠️  No HTML file found")
            
            data_to_insert.append((
                url,
                boxrec_id,
                matched_slug if matched_slug else None,
                boxer_name,
                html_content
            ))
    
    print(f"\n💾 Inserting {len(data_to_insert)} records...")
    
    # Insert data
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
    
    execute_batch(cur, insert_query, data_to_insert)
    conn.commit()
    
    # Check what's in the database
    cur.execute('SELECT boxrec_id, boxer_name, matched_slug, length(html_file) as html_size FROM "data-pipelines-staging".boxrec_scraper')
    results = cur.fetchall()
    
    print("\n✅ Database contents:")
    for row in results:
        print(f"  {row[0]}: {row[1]} (slug: {row[2]}, HTML: {row[3]} bytes)")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
    
finally:
    cur.close()
    conn.close()