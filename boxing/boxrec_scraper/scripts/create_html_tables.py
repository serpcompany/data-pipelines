#!/usr/bin/env python3
"""
Create HTML storage tables in the staging database
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
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

def create_tables():
    """Create HTML storage tables in staging schema"""
    
    print("🔨 Creating HTML storage tables in staging schema...")
    
    # Connect to PostgreSQL
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    try:
        # Create boxrec_html table
        print("📋 Creating boxrec_html table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS "data-pipelines-staging".boxrec_html (
                id SERIAL PRIMARY KEY,
                url VARCHAR(500) NOT NULL,
                boxrec_id VARCHAR(50),
                html_content TEXT NOT NULL,
                content_hash VARCHAR(64),
                language VARCHAR(10) DEFAULT 'en',
                page_type VARCHAR(50) DEFAULT 'boxer',
                scrape_status VARCHAR(50) DEFAULT 'valid',
                status_message TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(url)
            )
        """)
        
        # Create indexes for boxrec_html
        print("📇 Creating indexes for boxrec_html...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_boxrec_html_boxrec_id ON \"data-pipelines-staging\".boxrec_html(boxrec_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_boxrec_html_page_type ON \"data-pipelines-staging\".boxrec_html(page_type)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_boxrec_html_scrape_status ON \"data-pipelines-staging\".boxrec_html(scrape_status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_boxrec_html_scraped_at ON \"data-pipelines-staging\".boxrec_html(scraped_at)")
        
        # Create bout_html table
        print("📋 Creating bout_html table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS "data-pipelines-staging".bout_html (
                id SERIAL PRIMARY KEY,
                url VARCHAR(500) NOT NULL,
                event_id VARCHAR(50),
                html_content TEXT NOT NULL,
                content_hash VARCHAR(64),
                language VARCHAR(10) DEFAULT 'en',
                scrape_status VARCHAR(50) DEFAULT 'valid',
                status_message TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(url)
            )
        """)
        
        # Create indexes for bout_html
        print("📇 Creating indexes for bout_html...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_bout_html_event_id ON \"data-pipelines-staging\".bout_html(event_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_bout_html_scrape_status ON \"data-pipelines-staging\".bout_html(scrape_status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_bout_html_scraped_at ON \"data-pipelines-staging\".bout_html(scraped_at)")
        
        # Create scrape_queue table
        print("📋 Creating scrape_queue table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS "data-pipelines-staging".scrape_queue (
                id SERIAL PRIMARY KEY,
                url VARCHAR(500) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id VARCHAR(50),
                priority INT DEFAULT 5,
                status VARCHAR(50) DEFAULT 'pending',
                attempts INT DEFAULT 0,
                last_attempt_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(url)
            )
        """)
        
        # Create indexes for scrape_queue
        print("📇 Creating indexes for scrape_queue...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_scrape_queue_status_priority ON \"data-pipelines-staging\".scrape_queue(status, priority)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_scrape_queue_entity_type ON \"data-pipelines-staging\".scrape_queue(entity_type)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_scrape_queue_created_at ON \"data-pipelines-staging\".scrape_queue(created_at)")
        
        # Create update trigger function
        print("🔧 Creating update trigger function...")
        cur.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        """)
        
        # Create triggers
        print("⚡ Creating update triggers...")
        cur.execute("""
            CREATE TRIGGER update_boxrec_html_updated_at 
            BEFORE UPDATE ON "data-pipelines-staging".boxrec_html
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """)
        
        cur.execute("""
            CREATE TRIGGER update_bout_html_updated_at 
            BEFORE UPDATE ON "data-pipelines-staging".bout_html
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """)
        
        cur.execute("""
            CREATE TRIGGER update_scrape_queue_updated_at 
            BEFORE UPDATE ON "data-pipelines-staging".scrape_queue
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """)
        
        # Add comments
        print("📝 Adding table comments...")
        cur.execute("COMMENT ON TABLE \"data-pipelines-staging\".boxrec_html IS 'Stores raw HTML content for boxer pages'")
        cur.execute("COMMENT ON TABLE \"data-pipelines-staging\".bout_html IS 'Stores raw HTML content for bout/event pages'")
        cur.execute("COMMENT ON TABLE \"data-pipelines-staging\".scrape_queue IS 'Manages scraping queue and tracks scraping status'")
        
        print("✅ All tables created successfully!")
        
        # Show table info
        cur.execute("""
            SELECT table_name, 
                   pg_size_pretty(pg_total_relation_size('"data-pipelines-staging".'||table_name)) as size
            FROM information_schema.tables 
            WHERE table_schema = 'data-pipelines-staging' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        print("\n📊 Tables in staging schema:")
        for row in cur.fetchall():
            print(f"   {row[0]}: {row[1]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_tables()