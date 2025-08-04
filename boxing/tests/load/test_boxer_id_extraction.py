#!/usr/bin/env python3
"""Test boxer ID extraction from filenames."""

import pytest
from boxing.load.to_data_lake import extract_boxer_id_from_filename


def is_valid_boxrec_id(boxer_id: str) -> bool:
    """Check if a string is a valid BoxRec ID (numeric only)."""
    if not boxer_id:
        return False
    return boxer_id.isdigit()


class TestBoxerIdExtraction:
    """Test cases for boxer ID extraction."""
    
    def test_standard_filename(self):
        """Test extraction from standard filename."""
        boxer_id = extract_boxer_id_from_filename('en_box-pro_123456.html')
        assert boxer_id == '123456'
        assert is_valid_boxrec_id(boxer_id)
        
        boxer_id = extract_boxer_id_from_filename('en_box-am_789012.html')
        assert boxer_id == '789012'
        assert is_valid_boxrec_id(boxer_id)
    
    def test_filename_with_dots(self):
        """Test extraction from filename with dots in boxer ID part."""
        # This is the bug case - it should extract only the numeric ID
        boxer_id = extract_boxer_id_from_filename('en_box-pro_272717.Kell+Brook+v+SenchenkoThe.html')
        assert boxer_id == '272717'
        assert is_valid_boxrec_id(boxer_id)
        
        boxer_id = extract_boxer_id_from_filename('en_box-pro_123.some.other.text.html')
        assert boxer_id == '123'
        assert is_valid_boxrec_id(boxer_id)
    
    def test_filename_with_special_characters(self):
        """Test extraction from filename with special characters."""
        boxer_id = extract_boxer_id_from_filename('en_box-pro_456+special+chars.html')
        assert boxer_id == '456'
        assert is_valid_boxrec_id(boxer_id)
        
        boxer_id = extract_boxer_id_from_filename('en_box-pro_789.with.dots.html')
        assert boxer_id == '789'
        assert is_valid_boxrec_id(boxer_id)
    
    def test_invalid_filenames(self):
        """Test that invalid filenames return None."""
        assert extract_boxer_id_from_filename('invalid.html') is None
        assert extract_boxer_id_from_filename('en_invalid_123.html') is None
        assert extract_boxer_id_from_filename('en_box-pro.html') is None
    
    def test_amateur_filenames(self):
        """Test extraction from amateur boxer filenames."""
        boxer_id = extract_boxer_id_from_filename('en_box-am_111222.html')
        assert boxer_id == '111222'
        assert is_valid_boxrec_id(boxer_id)
        
        boxer_id = extract_boxer_id_from_filename('en_box-am_333.extra.text.html')
        assert boxer_id == '333'
        assert is_valid_boxrec_id(boxer_id)
    
    def test_extracted_ids_are_valid(self):
        """Test that all extracted IDs pass validation."""
        test_cases = [
            'en_box-pro_611983.html',
            'en_box-pro_432984.html', 
            'en_box-pro_795218.html',
            'en_box-pro_479.html',
            'en_box-pro_94632.html',
            'en_box-pro_9707.html',
            'en_box-pro_742016.html',
            'en_box-pro_272717.Kell+Brook+v+SenchenkoThe.html',
            'en_box-pro_674303.html',
            'en_box-pro_509666.html'
        ]
        
        for filename in test_cases:
            boxer_id = extract_boxer_id_from_filename(filename)
            assert boxer_id is not None, f"Failed to extract ID from {filename}"
            assert is_valid_boxrec_id(boxer_id), f"Invalid BoxRec ID: {boxer_id} from {filename}"
            # BoxRec IDs should be numeric only
            assert boxer_id.isdigit(), f"BoxRec ID should be numeric only: {boxer_id}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])