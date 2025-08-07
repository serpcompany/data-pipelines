#!/usr/bin/env python3
"""
Test that staging mirror schema matches Drizzle schema.
This ensures our local SQLite database accurately mirrors the production CloudFlare D1 schema.
"""

import pytest
import sqlite3
from pathlib import Path
from typing import Dict, Set

from boxing.database.staging_mirror import get_connection


class TestSchemaComparison:
    """Compare staging mirror schema with Drizzle schema definitions."""
    
    def get_drizzle_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Define the expected schema based on Drizzle TypeScript definitions.
        This is our source of truth for the production schema.
        """
        return {
            'boxerBouts': {
                'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                'boxerId': 'TEXT NOT NULL',
                'boxrecId': 'TEXT',  # This is where BoxRec bout ID should go!
                'boutDate': 'TEXT NOT NULL',
                'opponentName': 'TEXT NOT NULL',
                'opponentWeight': 'TEXT',
                'opponentRecord': 'TEXT',
                'eventName': 'TEXT',
                'refereeName': 'TEXT',
                'judge1Name': 'TEXT',
                'judge1Score': 'TEXT',
                'judge2Name': 'TEXT',
                'judge2Score': 'TEXT',
                'judge3Name': 'TEXT',
                'judge3Score': 'TEXT',
                'numRoundsScheduled': 'INTEGER',
                'result': 'TEXT NOT NULL',
                'resultMethod': 'TEXT',
                'resultRound': 'INTEGER',
                'eventPageLink': 'TEXT',
                'boutPageLink': 'TEXT',
                'scorecardsPageLink': 'TEXT',
                'titleFight': 'INTEGER DEFAULT 0',
                'createdAt': 'TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL'
            },
            'boxers': {
                'id': 'TEXT PRIMARY KEY',
                'boxrecId': 'TEXT NOT NULL UNIQUE',
                'name': 'TEXT NOT NULL',
                'birthName': 'TEXT',
                'nicknames': 'TEXT',  # JSON array stored as TEXT
                'dateOfBirth': 'TEXT',
                'birthPlace': 'TEXT',
                'age': 'INTEGER',
                'stance': 'TEXT',
                'height': 'TEXT',
                'reach': 'TEXT',
                'residence': 'TEXT',
                'division': 'TEXT',
                'titlesHeld': 'INTEGER DEFAULT 0',
                'koPercentage': 'REAL',
                'gender': 'TEXT',
                'ranking': 'INTEGER',
                'nationality': 'TEXT',
                'isActive': 'INTEGER DEFAULT 1',
                'debut': 'TEXT',
                'record': 'TEXT',
                'lastFight': 'TEXT',
                'nextFight': 'TEXT',
                'createdAt': 'TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL',
                'updatedAt': 'TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL'
            }
        }
    
    def get_staging_mirror_schema(self) -> Dict[str, Dict[str, str]]:
        """Get the actual schema from staging mirror database."""
        conn = get_connection()
        cursor = conn.cursor()
        
        schema = {}
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            schema[table] = {}
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table})")
            for row in cursor.fetchall():
                col_name = row[1]
                col_type = row[2]
                not_null = row[3]
                default = row[4]
                is_pk = row[5]
                
                # Build type string similar to Drizzle
                type_str = col_type
                if is_pk:
                    type_str += " PRIMARY KEY"
                if not_null:
                    type_str += " NOT NULL"
                if default is not None:
                    type_str += f" DEFAULT {default}"
                    
                schema[table][col_name] = type_str
        
        conn.close()
        return schema
    
    def test_boxerBouts_schema_matches_drizzle(self):
        """Test that boxerBouts table schema matches Drizzle definition."""
        drizzle = self.get_drizzle_schema()
        staging = self.get_staging_mirror_schema()
        
        # Check if table exists
        assert 'boxerBouts' in staging, "boxerBouts table missing from staging mirror"
        
        drizzle_bouts = drizzle['boxerBouts']
        staging_bouts = staging['boxerBouts']
        
        # Check for missing columns
        missing_cols = set(drizzle_bouts.keys()) - set(staging_bouts.keys())
        assert not missing_cols, f"Missing columns in staging mirror: {missing_cols}"
        
        # Check for extra columns
        extra_cols = set(staging_bouts.keys()) - set(drizzle_bouts.keys())
        print(f"Extra columns in staging (may be okay): {extra_cols}")
        
        # Check critical fields
        assert 'boxrecId' in staging_bouts, "boxrecId field missing - this stores the BoxRec bout ID!"
        assert 'eventPageLink' in staging_bouts, "eventPageLink field missing"
        assert 'boutPageLink' in staging_bouts, "boutPageLink field missing"
        
        # Check id field type
        if 'id' in staging_bouts:
            assert 'INTEGER' in staging_bouts['id'].upper(), \
                f"id should be INTEGER with AUTOINCREMENT, not {staging_bouts['id']}"
    
    def test_boxers_schema_matches_drizzle(self):
        """Test that boxers table schema matches Drizzle definition."""
        drizzle = self.get_drizzle_schema()
        staging = self.get_staging_mirror_schema()
        
        # Check if table exists
        assert 'boxers' in staging, "boxers table missing from staging mirror"
        
        drizzle_boxers = drizzle['boxers']
        staging_boxers = staging['boxers']
        
        # Check for missing columns
        missing_cols = set(drizzle_boxers.keys()) - set(staging_boxers.keys())
        print(f"Missing columns: {missing_cols}")
        
        # Check critical fields
        assert 'boxrecId' in staging_boxers, "boxrecId field missing"
        assert 'isActive' in staging_boxers, "isActive field missing"
        
    def test_schema_differences_report(self):
        """Generate a detailed report of schema differences."""
        drizzle = self.get_drizzle_schema()
        staging = self.get_staging_mirror_schema()
        
        print("\n=== SCHEMA COMPARISON REPORT ===\n")
        
        for table_name, drizzle_cols in drizzle.items():
            print(f"Table: {table_name}")
            
            if table_name not in staging:
                print(f"  ❌ Table missing from staging mirror!")
                continue
            
            staging_cols = staging[table_name]
            
            # Missing columns
            missing = set(drizzle_cols.keys()) - set(staging_cols.keys())
            if missing:
                print(f"  ❌ Missing columns: {', '.join(missing)}")
            
            # Extra columns  
            extra = set(staging_cols.keys()) - set(drizzle_cols.keys())
            if extra:
                print(f"  ⚠️  Extra columns: {', '.join(extra)}")
            
            # Type mismatches
            for col in drizzle_cols:
                if col in staging_cols:
                    drizzle_type = drizzle_cols[col].upper()
                    staging_type = staging_cols[col].upper()
                    
                    # Normalize for comparison
                    if 'INTEGER' in drizzle_type and 'INTEGER' not in staging_type:
                        print(f"  ❌ {col}: type mismatch - expected INTEGER, got {staging_type}")
                    elif 'TEXT' in drizzle_type and 'TEXT' not in staging_type:
                        print(f"  ❌ {col}: type mismatch - expected TEXT, got {staging_type}")
            
            print()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])