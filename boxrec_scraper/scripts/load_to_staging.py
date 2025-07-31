#!/usr/bin/env python3
"""
Load scraped BoxRec data into PostgreSQL staging database
"""

import os
import csv
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
import argparse
from pathlib import Path

# Load environment variables
load_dotenv('/Users/devin/repos/projects/data-pipelines/boxing/.env')

# PostgreSQL connection details
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT'),
    'user': os.getenv('POSTGRES_USER'), 
    'password': os.getenv('POSTGRES_PASSWORD'),
    'database': os.getenv('POSTGRES_DEFAULT_DB')
}

def load_scraped_data(csv_file, html_dir):
    """Load scraped data from CSV and HTML files into staging database"""
    
    print("Starting load_scraped_data function...")
    print(f"CSV file: {csv_file}")
    print(f"HTML dir: {html_dir}")
    
    # Connect to PostgreSQL
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor()
    
    try:
        print(f"📁 Reading data from {csv_file}")
        
        # Read CSV data
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data_to_insert = []
            
            for row in reader:
                boxrec_id = row.get('boxrec_id')
                url = row.get('url')
                boxer_name = row.get('name', '')
                matched_slug = row.get('slug', '')
                
                # Look for corresponding HTML file
                html_content = None
                if html_dir:
                    html_path = Path(html_dir)
                    
                    # Try different HTML file naming patterns
                    possible_files = [
                        html_path / f"en_box-pro_{boxrec_id}.html",
                        html_path / f"de_box-pro_{boxrec_id}.html", 
                        html_path / f"es_box-pro_{boxrec_id}.html",
                        html_path / f"fr_box-pro_{boxrec_id}.html",
                        html_path / f"ru_box-pro_{boxrec_id}.html"
                    ]
                    
                    for html_file in possible_files:
                        if html_file.exists():
                            with open(html_file, 'r', encoding='utf-8') as hf:
                                html_content = hf.read()
                            break
                
                data_to_insert.append((
                    url,
                    boxrec_id, 
                    matched_slug if matched_slug else None,
                    boxer_name,
                    html_content
                ))
        
        print(f"📊 Prepared {len(data_to_insert)} records for insertion")
        
        if len(data_to_insert) == 0:
            print("⚠️  No data to insert!")
            return
            
        # Show sample of what we're inserting
        print(f"Sample record: {data_to_insert[0][:3]}...")
        
        # Insert data using batch insert for performance
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
        
        print("💾 Inserting data into database...")
        execute_batch(cur, insert_query, data_to_insert, page_size=1000)
        
        conn.commit()
        
        # Get final count
        cur.execute('SELECT COUNT(*) FROM "data-pipelines-staging".boxrec_scraper')
        total_count = cur.fetchone()[0]
        
        print(f"✅ Successfully loaded data!")
        print(f"   Records inserted/updated: {len(data_to_insert)}")
        print(f"   Total records in table: {total_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        
    finally:
        cur.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='Load scraped BoxRec data to staging database')
    parser.add_argument('csv_file', help='Path to CSV file with boxer data')
    parser.add_argument('--html-dir', help='Directory containing HTML files', default='data/raw/boxrec_html')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"❌ CSV file not found: {args.csv_file}")
        return
        
    if args.html_dir and not os.path.exists(args.html_dir):
        print(f"⚠️  HTML directory not found: {args.html_dir}")
        print("Proceeding without HTML content...")
        args.html_dir = None
    
    load_scraped_data(args.csv_file, args.html_dir)

if __name__ == "__main__":
    main()