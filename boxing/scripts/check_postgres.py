#!/usr/bin/env python3
"""Check existing Postgres schema for data lake."""

import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)

# Database connection parameters
conn_params = {
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'database': os.getenv('POSTGRES_DEFAULT_DB')
}

def check_existing_schema():
    """Check what tables exist in the database."""
    try:
        # Connect to database
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        print(f"Connected to PostgreSQL at {conn_params['host']}:{conn_params['port']}")
        print(f"Database: {conn_params['database']}\n")
        
        # Get all tables
        cur.execute("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schemaname, tablename;
        """)
        
        tables = cur.fetchall()
        
        if tables:
            print("Existing tables:")
            current_schema = None
            for schema, table in tables:
                if schema != current_schema:
                    current_schema = schema
                    print(f"\nSchema: {schema}")
                print(f"  - {table}")
                
                # Get column info for tables that might be for HTML storage
                if 'html' in table.lower() or 'raw' in table.lower() or 'scrape' in table.lower():
                    cur.execute("""
                        SELECT column_name, data_type, character_maximum_length
                        FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = %s
                        ORDER BY ordinal_position;
                    """, (schema, table))
                    
                    columns = cur.fetchall()
                    print(f"    Columns:")
                    for col_name, data_type, max_length in columns:
                        length_info = f"({max_length})" if max_length else ""
                        print(f"      • {col_name}: {data_type}{length_info}")
        else:
            print("No tables found in the database.")
        
        # Check database size
        cur.execute("""
            SELECT pg_database_size(%s) as size_bytes,
                   pg_size_pretty(pg_database_size(%s)) as size_pretty;
        """, (conn_params['database'], conn_params['database']))
        
        size_bytes, size_pretty = cur.fetchone()
        print(f"\nDatabase size: {size_pretty}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error connecting to database: {e}")

if __name__ == "__main__":
    check_existing_schema()