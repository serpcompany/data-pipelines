#!/usr/bin/env python3
"""
Test the fix for bout field mapping.
"""

import pytest


def map_bout_fields(bout_data):
    """
    Map bout extractor fields to staging database fields.
    This function handles the field name differences between what the extractor
    returns and what the staging database expects.
    """
    return {
        'date': bout_data.get('date'),
        'opponent': bout_data.get('opponent_name'),  # Map opponent_name -> opponent
        'opponent_url': bout_data.get('opponent_url'),
        'location': bout_data.get('venue'),  # Map venue -> location
        'result': bout_data.get('result'),
        'result_type': bout_data.get('result_type'),
        'rounds': bout_data.get('rounds'),
        'time': bout_data.get('time'),
        'division': bout_data.get('division'),
        'titles': bout_data.get('titles'),
        'first_boxer_weight': bout_data.get('first_boxer_weight'),
        'second_boxer_weight': bout_data.get('second_boxer_weight'),
        'referee': bout_data.get('referee'),
        'judges': bout_data.get('judges'),
        'event_link': bout_data.get('event_link'),
        'bout_link': bout_data.get('bout_link')
    }


class TestFieldMappingFix:
    """Test that our field mapping fix works correctly."""
    
    def test_map_opponent_name_to_opponent(self):
        """Test opponent_name is mapped to opponent."""
        extractor_output = {
            'opponent_name': 'Conor McGregor',
            'venue': 'T-Mobile Arena, Las Vegas',
            'date': 'Aug 17',
            'result': 'win'
        }
        
        mapped = map_bout_fields(extractor_output)
        
        assert mapped['opponent'] == 'Conor McGregor'
        assert mapped['location'] == 'T-Mobile Arena, Las Vegas'
        assert 'opponent_name' not in mapped  # Original field not in output
        assert 'venue' not in mapped  # Original field not in output
    
    def test_all_fields_mapped(self):
        """Test that all fields are properly mapped."""
        full_bout_data = {
            'date': 'Aug 17',
            'opponent_name': 'Conor McGregor',
            'opponent_id': '802658',
            'opponent_url': 'https://boxrec.com/en/box-pro/802658',
            'venue': 'T-Mobile Arena, Las Vegas',
            'result': 'win',
            'event_link': 'https://boxrec.com/en/event/752960',
            'bout_link': 'https://boxrec.com/en/event/752960/2169292'
        }
        
        mapped = map_bout_fields(full_bout_data)
        
        # Check critical mappings
        assert mapped['opponent'] == 'Conor McGregor'
        assert mapped['location'] == 'T-Mobile Arena, Las Vegas'
        assert mapped['date'] == 'Aug 17'
        assert mapped['result'] == 'win'
        assert mapped['opponent_url'] == 'https://boxrec.com/en/box-pro/802658'
        assert mapped['event_link'] == 'https://boxrec.com/en/event/752960'
        assert mapped['bout_link'] == 'https://boxrec.com/en/event/752960/2169292'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])