#!/usr/bin/env python3
"""
Test the complete scraping pipeline with database storage
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
import subprocess
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

def check_database_before():
    """Check current state of database"""
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT COUNT(*) FROM "data-pipelines-staging".boxrec_html
    """)
    boxer_count = cur.fetchone()[0]
    
    cur.execute("""
        SELECT COUNT(*) FROM "data-pipelines-staging".bout_html
    """)
    bout_count = cur.fetchone()[0]
    
    print(f"📊 Database state before scraping:")
    print(f"   Boxer pages: {boxer_count}")
    print(f"   Bout pages: {bout_count}")
    
    cur.close()
    conn.close()
    
    return boxer_count, bout_count

def create_test_csv():
    """Create a test CSV with mixed boxer and bout URLs"""
    test_data = """url,entity_type,entity_id
https://boxrec.com/en/box-pro/659461,boxer,659461
https://boxrec.com/en/box-pro/432442,boxer,432442
https://boxrec.com/en/event/752960,bout,752960
https://boxrec.com/en/box-pro/11119,boxer,11119
https://boxrec.com/en/event/716316,bout,716316
"""
    
    csv_path = Path('data/test_scrape_5.csv')
    with open(csv_path, 'w') as f:
        f.write(test_data)
    
    print(f"📝 Created test CSV with 5 URLs (3 boxers, 2 bouts)")
    return csv_path

def run_scraper(csv_path):
    """Run the scraper"""
    print("\n🚀 Running scraper...")
    
    cmd = [
        sys.executable,
        'scripts/scrape_to_db.py',
        str(csv_path),
        '--workers', '3',
        '--rate-limit', '2'  # Slower rate for testing
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Print output
    if result.stdout:
        print("\nOutput:")
        print(result.stdout)
    
    if result.stderr:
        print("\nLogs:")
        for line in result.stderr.split('\n'):
            if any(keyword in line for keyword in ['🎉', 'Total:', 'Successful:', 'Failed:', 'Skipped:', 'Saved to DB:', 'Invalid']):
                print(line.replace('2025-07-31', '').strip())
    
    return result.returncode == 0

def check_database_after(initial_boxer_count, initial_bout_count):
    """Check database after scraping"""
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor()
    
    # Check boxer pages
    cur.execute("""
        SELECT url, boxrec_id, scrape_status, 
               LENGTH(html_content) as size,
               language, scraped_at
        FROM "data-pipelines-staging".boxrec_html
        ORDER BY scraped_at DESC
        LIMIT 10
    """)
    
    print("\n📊 Recent boxer pages in database:")
    boxer_results = cur.fetchall()
    new_boxer_count = 0
    for row in boxer_results:
        if row[5]:  # Has scraped_at
            age = "just now"
            print(f"   ID {row[1]}: {row[2]} - {row[3]:,} bytes - {row[4]} - {age}")
            new_boxer_count += 1
    
    # Check bout pages
    cur.execute("""
        SELECT url, event_id, scrape_status, 
               LENGTH(html_content) as size,
               language, scraped_at
        FROM "data-pipelines-staging".bout_html
        ORDER BY scraped_at DESC
        LIMIT 10
    """)
    
    print("\n📊 Recent bout pages in database:")
    bout_results = cur.fetchall()
    new_bout_count = 0
    for row in bout_results:
        if row[5]:  # Has scraped_at
            age = "just now"
            print(f"   Event {row[1]}: {row[2]} - {row[3]:,} bytes - {row[4]} - {age}")
            new_bout_count += 1
    
    # Get total counts
    cur.execute("""
        SELECT COUNT(*) FROM "data-pipelines-staging".boxrec_html
    """)
    final_boxer_count = cur.fetchone()[0]
    
    cur.execute("""
        SELECT COUNT(*) FROM "data-pipelines-staging".bout_html
    """)
    final_bout_count = cur.fetchone()[0]
    
    print(f"\n✅ Scraping summary:")
    print(f"   New boxer pages: {final_boxer_count - initial_boxer_count}")
    print(f"   New bout pages: {final_bout_count - initial_bout_count}")
    print(f"   Total boxer pages in DB: {final_boxer_count}")
    print(f"   Total bout pages in DB: {final_bout_count}")
    
    # Check for any errors
    cur.execute("""
        SELECT scrape_status, COUNT(*) 
        FROM "data-pipelines-staging".boxrec_html
        WHERE scraped_at > NOW() - INTERVAL '5 minutes'
        GROUP BY scrape_status
    """)
    
    print("\n📈 Recent scrape statuses:")
    for row in cur.fetchall():
        print(f"   {row[0]}: {row[1]}")
    
    cur.close()
    conn.close()

def main():
    """Run the complete test"""
    print("🧪 Testing BoxRec scraper with database storage\n")
    
    # Check initial state
    initial_boxer_count, initial_bout_count = check_database_before()
    
    # Create test CSV
    csv_path = create_test_csv()
    
    try:
        # Run scraper
        success = run_scraper(csv_path)
        
        if success:
            # Check results
            check_database_after(initial_boxer_count, initial_bout_count)
        else:
            print("\n❌ Scraper failed!")
            
    finally:
        # Clean up
        if csv_path.exists():
            csv_path.unlink()
            print(f"\n🧹 Cleaned up test file: {csv_path}")

if __name__ == "__main__":
    main()