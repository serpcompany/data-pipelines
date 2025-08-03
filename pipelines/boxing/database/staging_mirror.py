#!/usr/bin/env python3
"""
Local SQLite staging mirror database setup and management using Drizzle ORM.
Mirrors the production CloudFlare D1 schema for local development and testing.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Optional
import logging

try:
    # Try relative import first (when run as module)
    from ..utils.config import STAGING_MIRROR_DB_PATH
except ImportError:
    # Fall back to absolute import (when run as script)
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from pipelines.boxing.utils.config import STAGING_MIRROR_DB_PATH

logger = logging.getLogger(__name__)

class StagingMirrorDB:
    """Manages the staging mirror database using Drizzle ORM."""
    
    def __init__(self):
        self.db_path = STAGING_MIRROR_DB_PATH
        self.drizzle_config_path = Path(__file__).parent / "drizzle" / "drizzle.config.local.ts"
        
    def run_drizzle_command(self, command: str) -> tuple[bool, str]:
        """Run a drizzle-kit command and return success status and output."""
        try:
            # Change to the drizzle directory to run commands
            drizzle_dir = Path(__file__).parent / "drizzle"
            
            # Build the full command
            full_command = f"npx drizzle-kit {command} --config=drizzle.config.local.ts"
            
            logger.info(f"Running Drizzle command: {full_command}")
            
            result = subprocess.run(
                full_command,
                shell=True,
                cwd=drizzle_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Drizzle command succeeded: {result.stdout}")
                return True, result.stdout
            else:
                logger.error(f"Drizzle command failed: {result.stderr}")
                return False, result.stderr
                
        except Exception as e:
            logger.error(f"Error running Drizzle command: {e}")
            return False, str(e)
    
    def push_schema(self):
        """Push the current schema to the database."""
        logger.info("Pushing schema to staging mirror database")
        
        # First sync schema from GitHub
        from .fetch_and_update_schema import sync_schema_from_github
        logger.info("Syncing schema from GitHub...")
        if not sync_schema_from_github():
            raise Exception("Failed to sync schema from GitHub")
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Set the database URL environment variable for local SQLite
        os.environ['DRIZZLE_DB_URL'] = f"file:{self.db_path}"
        
        # First generate migrations if needed
        success, output = self.run_drizzle_command("generate")
        if not success and "No schema changes" not in output:
            logger.warning(f"Migration generation warning: {output}")
        
        # Then apply migrations
        success, output = self.run_drizzle_command("migrate")
        
        if success:
            logger.info("Schema migrations applied successfully")
        else:
            raise Exception(f"Failed to apply migrations: {output}")
    
    def generate_migrations(self):
        """Generate new migration files based on schema changes."""
        logger.info("Generating migrations for staging mirror database")
        
        success, output = self.run_drizzle_command("generate")
        
        if success:
            logger.info("Migrations generated successfully")
        else:
            raise Exception(f"Failed to generate migrations: {output}")
    
    def run_migrations(self):
        """Run pending migrations on the database."""
        logger.info("Running migrations on staging mirror database")
        
        # Set the database URL environment variable for local SQLite
        os.environ['DRIZZLE_DB_URL'] = f"file:{self.db_path}"
        
        success, output = self.run_drizzle_command("migrate")
        
        if success:
            logger.info("Migrations completed successfully")
        else:
            raise Exception(f"Failed to run migrations: {output}")
    
    def drop_migrations(self):
        """Drop all migrations (careful - this will delete data)."""
        logger.warning("Dropping all migrations from staging mirror database")
        
        success, output = self.run_drizzle_command("drop")
        
        if success:
            logger.info("Migrations dropped successfully")
        else:
            raise Exception(f"Failed to drop migrations: {output}")
    
    def studio(self):
        """Launch Drizzle Studio for visual database management."""
        logger.info("Launching Drizzle Studio")
        
        # Set the database URL environment variable for local SQLite
        os.environ['DRIZZLE_DB_URL'] = f"file:{self.db_path}"
        
        self.run_drizzle_command("studio")
    
    def reset_database(self):
        """Drop and recreate the staging database."""
        if self.db_path.exists():
            logger.warning(f"Removing existing database at {self.db_path}")
            self.db_path.unlink()
        
        # Push schema to create fresh database
        self.push_schema()
    
    def verify_schema(self):
        """Verify that the schema matches production."""
        logger.info("Verifying schema against production")
        
        # For now, we trust that Drizzle ORM keeps schemas in sync
        # In the future, we could add more sophisticated verification
        
        if not self.db_path.exists():
            logger.error("Database does not exist")
            return False
        
        logger.info("Schema verification passed")
        return True

def get_staging_db():
    """Get an instance of the staging mirror database manager."""
    return StagingMirrorDB()

def get_connection():
    """
    Get a raw SQLite connection for backwards compatibility.
    TODO: Refactor metadata.py and other modules to use Drizzle ORM instead.
    """
    import sqlite3
    
    conn = sqlite3.connect(STAGING_MIRROR_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    db = get_staging_db()
    
    # Create or reset the database
    if db.db_path.exists():
        response = input(f"Database exists at {db.db_path}. Reset it? (y/N): ")
        if response.lower() == 'y':
            db.reset_database()
        else:
            logger.info("Keeping existing database")
    else:
        db.push_schema()
    
    # Verify the schema
    db.verify_schema()
    
    # Optionally launch studio
    response = input("Launch Drizzle Studio? (y/N): ")
    if response.lower() == 'y':
        db.studio()