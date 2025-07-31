#!/usr/bin/env python3
"""
Test the staging database scraper with mixed entity types
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
    
    tables = ['boxrec_boxer', 'boxrec_event', 'boxrec_bout']
    counts = {}
    
    for table in tables:
        cur.execute(f'SELECT COUNT(*) FROM "data-pipelines-staging".{table}')
        counts[table] = cur.fetchone()[0]
    
    print(f"📊 Database state before scraping:")
    for table, count in counts.items():
        print(f"   {table}: {count} records")
    
    cur.close()
    conn.close()
    
    return counts

def create_test_csv():
    """Create a test CSV with mixed entity types"""
    test_data = """url
https://boxrec.com/en/box-pro/659461
https://boxrec.com/en/box-pro/432442
https://boxrec.com/en/event/752960
https://boxrec.com/en/event/752960/2570147
https://boxrec.com/en/box-pro/11119
https://boxrec.com/en/event/716316
https://boxrec.com/en/event/716316/2359078
"""
    
    csv_path = Path('data/test_staging_mixed.csv')
    with open(csv_path, 'w') as f:
        f.write(test_data)
    
    print(f"📝 Created test CSV with 7 URLs:")
    print(f"   - 3 boxers")
    print(f"   - 2 events") 
    print(f"   - 2 bouts")
    return csv_path

def run_scraper(csv_path):
    """Run the scraper"""
    print("\n🚀 Running scraper...")
    
    cmd = [
        sys.executable,
        'scripts/scrape_to_staging_db.py',
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
            if any(keyword in line for keyword in ['Entity types:', '🎉', 'Total:', 'Successful:', 'Failed:', 'Skipped:', 'Saved to DB:']):
                print(line.replace('2025-07-31', '').strip())
    
    return result.returncode == 0

def check_database_after(initial_counts):
    """Check database after scraping"""
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor()
    
    print("\n📊 Database contents after scraping:")
    
    # Check boxrec_boxer
    print("\n🥊 Boxer records:")
    cur.execute("""
        SELECT boxrec_id, boxrec_url, LENGTH(html_file) as size, scraped_at
        FROM "data-pipelines-staging".boxrec_boxer
        WHERE scraped_at > NOW() - INTERVAL '5 minutes'
        ORDER BY scraped_at DESC
    """)
    for row in cur.fetchall():
        print(f"   Boxer {row[0]}: {row[2]:,} bytes - scraped just now")
    
    # Check boxrec_event
    print("\n📅 Event records:")
    cur.execute("""
        SELECT boxrec_event_id, boxrec_url, LENGTH(html_file) as size, scraped_at
        FROM "data-pipelines-staging".boxrec_event
        WHERE scraped_at > NOW() - INTERVAL '5 minutes'
        ORDER BY scraped_at DESC
    """)
    for row in cur.fetchall():
        print(f"   Event {row[0]}: {row[2]:,} bytes - scraped just now")
    
    # Check boxrec_bout
    print("\n🥊 Bout records:")
    cur.execute("""
        SELECT boxrec_bout_id, boxrec_url, LENGTH(html_file) as size, scraped_at
        FROM "data-pipelines-staging".boxrec_bout
        WHERE scraped_at > NOW() - INTERVAL '5 minutes'
        ORDER BY scraped_at DESC
    """)
    for row in cur.fetchall():
        print(f"   Bout {row[0]}: {row[2]:,} bytes - scraped just now")
    
    # Get final counts
    print("\n✅ Summary:")
    tables = ['boxrec_boxer', 'boxrec_event', 'boxrec_bout']
    for table in tables:
        cur.execute(f'SELECT COUNT(*) FROM "data-pipelines-staging".{table}')
        final_count = cur.fetchone()[0]
        new_records = final_count - initial_counts[table]
        print(f"   {table}: +{new_records} new records (total: {final_count})")
    
    cur.close()
    conn.close()

def main():
    """Run the complete test"""
    print("🧪 Testing BoxRec staging database scraper\n")
    
    # Check initial state
    initial_counts = check_database_before()
    
    # Create test CSV
    csv_path = create_test_csv()
    
    try:
        # Run scraper
        success = run_scraper(csv_path)
        
        if success:
            # Check results
            check_database_after(initial_counts)
        else:
            print("\n❌ Scraper failed!")
            
    finally:
        # Clean up
        if csv_path.exists():
            csv_path.unlink()
            print(f"\n🧹 Cleaned up test file: {csv_path}")

if __name__ == "__main__":
    main()