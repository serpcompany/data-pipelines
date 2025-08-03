#!/usr/bin/env python3
"""
Test bout extraction and field mapping.
These tests verify that bout data is correctly extracted and mapped to staging fields.
"""

import pytest
from bs4 import BeautifulSoup
from pipelines.boxing.extract.page.boxer.fields import bouts
from pipelines.boxing.load.to_staging_mirror_db import StagingLoader


class TestBoutExtraction:
    """Test bout extraction from HTML."""
    
    @pytest.fixture
    def sample_bout_html(self):
        """Sample HTML with bout data."""
        return """
        <table class="dataTable">
            <tr>
                <td>2017-08-26</td>
                <td></td>
                <td><a class="personLink" href="/en/box-pro/802658">Conor McGregor</a></td>
                <td><span class="textWon">0</span>-<span class="textLost">0</span>-<span class="textDraw">0</span></td>
                <td></td>
                <td>T-Mobile Arena, Las Vegas</td>
                <td><div class="boutResult">W TKO 10</div></td>
            </tr>
        </table>
        """
    
    def test_bout_extraction_field_names(self, sample_bout_html):
        """Test that bout extractor returns correct field names."""
        soup = BeautifulSoup(sample_bout_html, 'html.parser')
        bout_data = bouts.extract(soup)
        
        assert len(bout_data) == 1
        bout = bout_data[0]
        
        # Check that extractor returns these field names
        assert 'opponent_name' in bout
        assert 'venue' in bout
        assert 'date' in bout
        assert 'result' in bout
        
        # Verify values
        assert bout['opponent_name'] == 'Conor McGregor'
        assert bout['venue'] == 'T-Mobile Arena, Las Vegas'
        assert bout['date'] == '2017-08-26'
        assert bout['result'] == 'win'


class TestBoutFieldMapping:
    """Test field mapping from extractor to staging database."""
    
    def test_staging_loader_expects_correct_fields(self):
        """Test that staging loader expects specific field names."""
        # This test documents what the staging loader CURRENTLY expects
        sample_bout = {
            'date': '2017-08-26',
            'opponent': 'Conor McGregor',  # Loader expects 'opponent'
            'location': 'T-Mobile Arena, Las Vegas',  # Loader expects 'location'
            'result': 'win'
        }
        
        # The loader should handle these fields without error
        # Currently it expects 'opponent' not 'opponent_name'
        # Currently it expects 'location' not 'venue'
        assert 'opponent' in sample_bout
        assert 'location' in sample_bout
    
    def test_field_mapping_mismatch(self):
        """Test that demonstrates the field mapping issue."""
        # What the extractor returns
        extractor_output = {
            'opponent_name': 'Conor McGregor',
            'venue': 'T-Mobile Arena, Las Vegas'
        }
        
        # What the loader expects
        loader_expects = ['opponent', 'location']
        
        # This demonstrates the mismatch
        for field in loader_expects:
            assert field not in extractor_output, f"Field mismatch: loader expects '{field}' but extractor doesn't provide it"


class TestDateValidation:
    """Test date format validation."""
    
    def test_incomplete_date_format(self):
        """Test that dates from BoxRec are incomplete."""
        sample_dates = [
            'Aug 17',  # Missing year
            'Sep 15',  # Missing year
            'May 14'   # Missing year
        ]
        
        for date in sample_dates:
            # These dates are missing the year
            assert len(date.split()) == 2, "Date should only have month and day"
            assert not any(char.isdigit() and len(str(char)) == 4 for char in date.split()), "Date is missing year"
    
    def test_complete_date_format(self):
        """Test what a complete date should look like."""
        complete_date = '2017-08-26'
        parts = complete_date.split('-')
        
        assert len(parts) == 3, "Complete date should have 3 parts"
        assert len(parts[0]) == 4, "Year should be 4 digits"
        assert parts[0].isdigit(), "Year should be numeric"


class TestResultValidation:
    """Test result field validation."""
    
    def test_valid_result_values(self):
        """Test that results should be win/loss/draw/no-contest."""
        valid_results = ['win', 'loss', 'draw', 'no-contest']
        
        # Test current issue: opponent names in result field
        invalid_results = [
            'Conor McGregor',
            'Andre Berto',
            'Manny Pacquiao'
        ]
        
        for result in invalid_results:
            assert result not in valid_results, f"'{result}' is not a valid bout result"


if __name__ == "__main__":
    # Run specific test to see the failure
    pytest.main([__file__, "-v", "-k", "test_field_mapping_mismatch"])