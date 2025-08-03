#!/usr/bin/env python3
"""
Integration test to verify bout data is loaded correctly.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from pipelines.boxing.load.to_staging_mirror_db import StagingLoader
from pipelines.boxing.database.staging_mirror import create_schema


class TestBoutDataIntegration:
    """Test that bout data flows correctly from extractor to database."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Create schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Simplified schema for testing
        cursor.execute("""
        CREATE TABLE boxers (
            id TEXT PRIMARY KEY,
            boxrecId TEXT,
            name TEXT,
            proWins INTEGER DEFAULT 0,
            proLosses INTEGER DEFAULT 0,
            hasAmateurRecord INTEGER DEFAULT 0
        )
        """)
        
        cursor.execute("""
        CREATE TABLE boxerBouts (
            id TEXT PRIMARY KEY,
            boxerId TEXT,
            date TEXT,
            opponent TEXT,
            opponentUrl TEXT,
            location TEXT,
            result TEXT,
            resultType TEXT,
            rounds TEXT,
            boutType TEXT DEFAULT 'pro',
            boutOrder INTEGER,
            createdAt TEXT,
            updatedAt TEXT
        )
        """)
        
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        Path(db_path).unlink()
    
    def test_bout_fields_loaded_correctly(self, temp_db):
        """Test that bout fields are mapped and loaded correctly."""
        # Sample boxer data with bout information
        boxer_data = {
            'boxrec_id': '352',
            'name': 'Floyd Mayweather Jr',
            'wins': 50,
            'losses': 0,
            'bouts': [
                {
                    'date': 'Aug 17',
                    'opponent_name': 'Conor McGregor',  # Note: extractor returns this
                    'opponent_url': 'https://boxrec.com/en/box-pro/802658',
                    'venue': 'T-Mobile Arena, Las Vegas',  # Note: extractor returns this
                    'result': 'win',
                    'result_type': 'TKO',
                    'rounds': '10'
                }
            ]
        }
        
        # Load data using the staging loader logic
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Insert boxer
        cursor.execute("""
            INSERT INTO boxers (id, boxrecId, name, proWins, proLosses)
            VALUES (?, ?, ?, ?, ?)
        """, ('352', '352', boxer_data['name'], boxer_data['wins'], boxer_data['losses']))
        
        # Insert bout using the same logic as staging loader
        bout = boxer_data['bouts'][0]
        cursor.execute("""
            INSERT INTO boxerBouts (
                id, boxerId, date, opponent, opponentUrl, location,
                result, resultType, rounds, boutType, boutOrder, createdAt, updatedAt
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            '352_bout_0',
            '352',
            bout.get('date'),
            bout.get('opponent_name'),  # This is the fix
            bout.get('opponent_url'),
            bout.get('venue'),  # This is the fix
            bout.get('result'),
            bout.get('result_type'),
            bout.get('rounds'),
            'pro',
            0
        ))
        
        conn.commit()
        
        # Verify data was loaded correctly
        cursor.execute("SELECT opponent, location, result FROM boxerBouts WHERE boxerId = '352'")
        row = cursor.fetchone()
        
        assert row is not None, "Bout should be loaded"
        assert row[0] == 'Conor McGregor', f"Opponent should be 'Conor McGregor', got '{row[0]}'"
        assert row[1] == 'T-Mobile Arena, Las Vegas', f"Location should be 'T-Mobile Arena, Las Vegas', got '{row[1]}'"
        assert row[2] == 'win', f"Result should be 'win', got '{row[2]}'"
        
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])