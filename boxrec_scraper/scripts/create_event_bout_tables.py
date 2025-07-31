#!/usr/bin/env python3
"""
Create events and bouts tables in the staging database
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
    """Create events and bouts tables in staging schema"""
    
    print("🥊 Creating events and bouts tables in staging schema...")
    
    # Connect to PostgreSQL
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    try:
        # Create events table
        print("📋 Creating events table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS "data-pipelines-staging".events (
                id SERIAL PRIMARY KEY,
                event_id VARCHAR(50) UNIQUE NOT NULL,
                url VARCHAR(500) NOT NULL,
                name VARCHAR(500),
                date DATE,
                venue_id VARCHAR(50),
                venue_name VARCHAR(500),
                location VARCHAR(500),
                promoter VARCHAR(500),
                matchmaker VARCHAR(500),
                television VARCHAR(500),
                commission VARCHAR(500),
                attendance INT,
                gate_revenue VARCHAR(100),
                event_type VARCHAR(100),
                status VARCHAR(50),
                bout_count INT,
                html_scraped BOOLEAN DEFAULT FALSE,
                data_extracted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for events
        print("📇 Creating indexes for events...")
        cur.execute('CREATE INDEX IF NOT EXISTS idx_events_date ON "data-pipelines-staging".events(date)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_events_venue_id ON "data-pipelines-staging".events(venue_id)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_events_status ON "data-pipelines-staging".events(status)')
        
        # Create bouts table
        print("📋 Creating bouts table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS "data-pipelines-staging".bouts (
                id SERIAL PRIMARY KEY,
                bout_id VARCHAR(100) UNIQUE NOT NULL,
                event_id VARCHAR(50) NOT NULL,
                bout_order INT,
                boxer1_id VARCHAR(50),
                boxer1_name VARCHAR(200),
                boxer1_record_before VARCHAR(50),
                boxer1_hometown VARCHAR(200),
                boxer1_age INT,
                boxer1_weight DECIMAL(5,2),
                boxer1_height VARCHAR(20),
                boxer1_reach VARCHAR(20),
                boxer1_stance VARCHAR(20),
                boxer2_id VARCHAR(50),
                boxer2_name VARCHAR(200),
                boxer2_record_before VARCHAR(50),
                boxer2_hometown VARCHAR(200),
                boxer2_age INT,
                boxer2_weight DECIMAL(5,2),
                boxer2_height VARCHAR(20),
                boxer2_reach VARCHAR(20),
                boxer2_stance VARCHAR(20),
                weight_class VARCHAR(100),
                scheduled_rounds INT,
                actual_rounds INT,
                result VARCHAR(500),
                winner_id VARCHAR(50),
                method VARCHAR(100),
                time VARCHAR(20),
                referee VARCHAR(200),
                judge1_name VARCHAR(200),
                judge1_score VARCHAR(50),
                judge2_name VARCHAR(200),
                judge2_score VARCHAR(50),
                judge3_name VARCHAR(200),
                judge3_score VARCHAR(50),
                titles VARCHAR(1000),
                bout_type VARCHAR(100),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for bouts
        print("📇 Creating indexes for bouts...")
        cur.execute('CREATE INDEX IF NOT EXISTS idx_bouts_event_id ON "data-pipelines-staging".bouts(event_id)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_bouts_boxer1_id ON "data-pipelines-staging".bouts(boxer1_id)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_bouts_boxer2_id ON "data-pipelines-staging".bouts(boxer2_id)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_bouts_winner_id ON "data-pipelines-staging".bouts(winner_id)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_bouts_weight_class ON "data-pipelines-staging".bouts(weight_class)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_bouts_result ON "data-pipelines-staging".bouts(result)')
        
        # Add foreign key constraint
        print("🔗 Adding foreign key constraints...")
        cur.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'bouts_event_id_fkey' 
                    AND table_schema = 'data-pipelines-staging'
                ) THEN
                    ALTER TABLE "data-pipelines-staging".bouts 
                    ADD CONSTRAINT bouts_event_id_fkey 
                    FOREIGN KEY (event_id) REFERENCES "data-pipelines-staging".events(event_id);
                END IF;
            END $$;
        """)
        
        # Create bout_rounds table
        print("📋 Creating bout_rounds table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS "data-pipelines-staging".bout_rounds (
                id SERIAL PRIMARY KEY,
                bout_id VARCHAR(100) NOT NULL,
                round_number INT NOT NULL,
                judge_name VARCHAR(200),
                boxer1_score INT,
                boxer2_score INT,
                notes VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bout_id, round_number, judge_name)
            )
        """)
        
        # Create bout_stats table
        print("📋 Creating bout_stats table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS "data-pipelines-staging".bout_stats (
                id SERIAL PRIMARY KEY,
                bout_id VARCHAR(100) UNIQUE NOT NULL,
                boxer1_punches_landed INT,
                boxer1_punches_thrown INT,
                boxer1_punch_percentage DECIMAL(5,2),
                boxer1_jabs_landed INT,
                boxer1_jabs_thrown INT,
                boxer1_power_landed INT,
                boxer1_power_thrown INT,
                boxer2_punches_landed INT,
                boxer2_punches_thrown INT,
                boxer2_punch_percentage DECIMAL(5,2),
                boxer2_jabs_landed INT,
                boxer2_jabs_thrown INT,
                boxer2_power_landed INT,
                boxer2_power_thrown INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add foreign key constraints for related tables
        print("🔗 Adding foreign key constraints for related tables...")
        cur.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'bout_rounds_bout_id_fkey' 
                    AND table_schema = 'data-pipelines-staging'
                ) THEN
                    ALTER TABLE "data-pipelines-staging".bout_rounds 
                    ADD CONSTRAINT bout_rounds_bout_id_fkey 
                    FOREIGN KEY (bout_id) REFERENCES "data-pipelines-staging".bouts(bout_id);
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'bout_stats_bout_id_fkey' 
                    AND table_schema = 'data-pipelines-staging'
                ) THEN
                    ALTER TABLE "data-pipelines-staging".bout_stats 
                    ADD CONSTRAINT bout_stats_bout_id_fkey 
                    FOREIGN KEY (bout_id) REFERENCES "data-pipelines-staging".bouts(bout_id);
                END IF;
            END $$;
        """)
        
        # Create update triggers
        print("⚡ Creating update triggers...")
        cur.execute("""
            CREATE OR REPLACE TRIGGER update_events_updated_at 
            BEFORE UPDATE ON "data-pipelines-staging".events
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """)
        
        cur.execute("""
            CREATE OR REPLACE TRIGGER update_bouts_updated_at 
            BEFORE UPDATE ON "data-pipelines-staging".bouts
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """)
        
        # Add comments
        print("📝 Adding table comments...")
        cur.execute('COMMENT ON TABLE "data-pipelines-staging".events IS \'Boxing events/fight cards containing multiple bouts\'')
        cur.execute('COMMENT ON TABLE "data-pipelines-staging".bouts IS \'Individual boxing matches between two fighters\'')
        cur.execute('COMMENT ON TABLE "data-pipelines-staging".bout_rounds IS \'Round-by-round scoring for bouts\'')
        cur.execute('COMMENT ON TABLE "data-pipelines-staging".bout_stats IS \'Punch statistics for bouts\'')
        
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