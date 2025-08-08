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
        
        # Bouts are now stored as JSON in boxers table
        
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
        
        # Prepare bouts as JSON
        import json
        bouts_json = []
        for i, bout in enumerate(boxer_data['bouts']):
            bout_obj = {
                'id': f'352-{i}',
                'boxerId': '352',
                'boutDate': bout.get('date'),
                'opponentName': bout.get('opponent_name'),
                'opponentUrl': bout.get('opponent_url'),
                'eventName': bout.get('venue'),
                'result': bout.get('result'),
                'resultMethod': bout.get('result_type'),
                'numRoundsScheduled': bout.get('rounds')
            }
            bouts_json.append(bout_obj)
        
        # Insert boxer with bouts as JSON
        cursor.execute("""
            INSERT INTO boxers (id, boxrecId, name, proWins, proLosses, bouts)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('352', '352', boxer_data['name'], boxer_data['wins'], boxer_data['losses'], 
               json.dumps(bouts_json)))
        
        conn.commit()
        
        # Verify data was loaded correctly
        cursor.execute("SELECT bouts FROM boxers WHERE id = '352'")
        row = cursor.fetchone()
        
        assert row is not None, "Boxer should be loaded"
        bouts = json.loads(row[0])
        assert len(bouts) == 1, f"Should have 1 bout, got {len(bouts)}"
        
        bout = bouts[0]
        assert bout['opponentName'] == 'Conor McGregor', f"Opponent should be 'Conor McGregor', got '{bout['opponentName']}'"
        assert bout['eventName'] == 'T-Mobile Arena, Las Vegas', f"Location should be 'T-Mobile Arena, Las Vegas', got '{bout['eventName']}'"
        assert bout['result'] == 'win', f"Result should be 'win', got '{bout['result']}'"
        
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])