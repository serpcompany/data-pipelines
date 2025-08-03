#!/usr/bin/env python3
"""
Local SQLite staging mirror database setup and management.
Mirrors the production CloudFlare D1 schema for local development and testing.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

from ..utils.config import STAGING_MIRROR_DB_PATH

logger = logging.getLogger(__name__)

def get_connection() -> sqlite3.Connection:
    """Get a connection to the staging mirror database."""
    conn = sqlite3.connect(STAGING_MIRROR_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_schema():
    """Create the staging mirror database schema matching CloudFlare D1."""
    logger.info(f"Creating staging mirror database at {STAGING_MIRROR_DB_PATH}")
    
    # Ensure data directory exists
    STAGING_MIRROR_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Create divisions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS divisions (
            id TEXT PRIMARY KEY NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            alternativeNames TEXT,
            weightLimitPounds REAL NOT NULL,
            weightLimitKilograms REAL NOT NULL,
            weightLimitStone TEXT,
            shortName TEXT,
            createdAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updatedAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS divisionsSlugIdx ON divisions(slug)")
        cursor.execute("CREATE INDEX IF NOT EXISTS divisionsShortNameIdx ON divisions(shortName)")
        
        # Create boxers table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS boxers (
            id TEXT PRIMARY KEY NOT NULL,
            boxrecId TEXT NOT NULL UNIQUE,
            boxrecUrl TEXT NOT NULL UNIQUE,
            boxrecWikiUrl TEXT,
            slug TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            birthName TEXT,
            nicknames TEXT,
            avatarImage TEXT,
            residence TEXT,
            birthPlace TEXT,
            dateOfBirth TEXT,
            gender TEXT,
            nationality TEXT,
            height TEXT,
            reach TEXT,
            stance TEXT,
            bio TEXT,
            promoters TEXT,
            trainers TEXT,
            managers TEXT,
            gym TEXT,
            proDebutDate TEXT,
            proDivision TEXT,
            proWins INTEGER NOT NULL DEFAULT 0,
            proWinsByKnockout INTEGER NOT NULL DEFAULT 0,
            proLosses INTEGER NOT NULL DEFAULT 0,
            proLossesByKnockout INTEGER NOT NULL DEFAULT 0,
            proDraws INTEGER NOT NULL DEFAULT 0,
            proStatus TEXT,
            proTotalBouts INTEGER,
            proTotalRounds INTEGER,
            amateurDebutDate TEXT,
            amateurDivision TEXT,
            amateurWins INTEGER,
            amateurWinsByKnockout INTEGER,
            amateurLosses INTEGER,
            amateurLossesByKnockout INTEGER,
            amateurDraws INTEGER,
            amateurStatus TEXT,
            amateurTotalBouts INTEGER,
            amateurTotalRounds INTEGER,
            hasAmateurRecord INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updatedAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create indexes for boxers
        cursor.execute("CREATE INDEX IF NOT EXISTS boxersSlugIdx ON boxers(slug)")
        cursor.execute("CREATE INDEX IF NOT EXISTS boxersBoxrecIdIdx ON boxers(boxrecId)")
        cursor.execute("CREATE INDEX IF NOT EXISTS boxersNationalityIdx ON boxers(nationality)")
        cursor.execute("CREATE INDEX IF NOT EXISTS boxersDivisionIdx ON boxers(proDivision)")
        cursor.execute("CREATE INDEX IF NOT EXISTS boxersStatusIdx ON boxers(proStatus)")
        
        # Create boxerBouts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS boxerBouts (
            id TEXT PRIMARY KEY NOT NULL,
            boxerId TEXT NOT NULL REFERENCES boxers(id),
            date TEXT,
            opponent TEXT,
            opponentUrl TEXT,
            location TEXT,
            result TEXT,
            resultType TEXT,
            rounds INTEGER,
            time TEXT,
            division TEXT,
            titles TEXT,
            firstBoxerWeight TEXT,
            secondBoxerWeight TEXT,
            referee TEXT,
            judges TEXT,
            boutType TEXT,
            boutOrder INTEGER,
            createdAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updatedAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create indexes for bouts
        cursor.execute("CREATE INDEX IF NOT EXISTS boutsBoxerIdx ON boxerBouts(boxerId)")
        cursor.execute("CREATE INDEX IF NOT EXISTS boutsDateIdx ON boxerBouts(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS boutsResultIdx ON boxerBouts(result)")
        
        # Create metadata tracking table for data lake
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_lake_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            boxrec_url TEXT NOT NULL UNIQUE,
            boxrec_id TEXT NOT NULL,
            html_hash TEXT NOT NULL,
            scraped_at TIMESTAMP NOT NULL,
            extracted_at TIMESTAMP,
            last_checked_at TIMESTAMP,
            change_detected BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS metadataUrlIdx ON data_lake_metadata(boxrec_url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS metadataHashIdx ON data_lake_metadata(html_hash)")
        
        conn.commit()
        logger.info("Staging mirror database schema created successfully")
        
    except Exception as e:
        logger.error(f"Error creating schema: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def reset_database():
    """Drop and recreate the staging database."""
    if STAGING_DB_PATH.exists():
        logger.warning(f"Removing existing database at {STAGING_DB_PATH}")
        STAGING_DB_PATH.unlink()
    
    create_schema()

def get_table_info(table_name: str) -> list:
    """Get column information for a table."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    conn.close()
    return columns

def verify_schema():
    """Verify that all expected tables and columns exist."""
    expected_tables = ['divisions', 'boxers', 'boxerBouts', 'data_lake_metadata']
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    missing_tables = set(expected_tables) - set(tables)
    if missing_tables:
        logger.error(f"Missing tables: {missing_tables}")
        return False
    
    logger.info("All expected tables exist")
    
    # Check some key columns
    checks = [
        ('boxers', ['id', 'boxrecId', 'slug', 'name']),
        ('boxerBouts', ['id', 'boxerId', 'opponent', 'result']),
        ('divisions', ['id', 'slug', 'name', 'shortName']),
    ]
    
    for table, expected_cols in checks:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        
        missing_cols = set(expected_cols) - set(columns)
        if missing_cols:
            logger.error(f"Table {table} missing columns: {missing_cols}")
            return False
    
    conn.close()
    logger.info("Schema verification passed")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create or reset the database
    if STAGING_DB_PATH.exists():
        response = input(f"Database exists at {STAGING_DB_PATH}. Reset it? (y/N): ")
        if response.lower() == 'y':
            reset_database()
        else:
            logger.info("Keeping existing database")
    else:
        create_schema()
    
    # Verify the schema
    verify_schema()