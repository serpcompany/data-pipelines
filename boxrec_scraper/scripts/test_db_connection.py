#!/usr/bin/env python3
"""
Test PostgreSQL connection
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/devin/repos/projects/data-pipelines/boxing/.env')

# Show what we're trying to connect to
print("Testing PostgreSQL connection...")
print(f"Host: {os.getenv('POSTGRES_HOST')}")
print(f"Port: {os.getenv('POSTGRES_PORT')}")
print(f"User: {os.getenv('POSTGRES_USER')}")
print(f"Database: {os.getenv('POSTGRES_DEFAULT_DB')}")

try:
    # PostgreSQL connection details
    POSTGRES_CONFIG = {
        'host': os.getenv('POSTGRES_HOST'),
        'port': os.getenv('POSTGRES_PORT'),
        'user': os.getenv('POSTGRES_USER'), 
        'password': os.getenv('POSTGRES_PASSWORD'),
        'database': os.getenv('POSTGRES_DEFAULT_DB')
    }
    
    print("\nConnecting...")
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    print("✅ Connected successfully!")
    
    # Test the schema exists
    cur = conn.cursor()
    cur.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name = 'data-pipelines-staging'
    """)
    
    if cur.fetchone():
        print("✅ Schema 'data-pipelines-staging' exists")
        
        # Check if table exists
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'data-pipelines-staging' 
            AND table_name = 'boxrec_scraper'
        """)
        
        if cur.fetchone():
            print("✅ Table 'boxrec_scraper' exists")
        else:
            print("❌ Table 'boxrec_scraper' not found")
    else:
        print("❌ Schema 'data-pipelines-staging' not found")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection failed: {e}")