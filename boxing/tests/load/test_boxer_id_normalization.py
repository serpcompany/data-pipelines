#!/usr/bin/env python3
"""Test boxer ID normalization to handle leading zeros consistently."""

import pytest
from boxing.transform import normalize_boxer_id


class TestBoxerIdNormalization:
    """Test cases for boxer ID normalization."""
    
    def test_removes_leading_zeros(self):
        """Test that leading zeros are removed."""
        assert normalize_boxer_id('000080') == '80'
        assert normalize_boxer_id('000147') == '147'
        assert normalize_boxer_id('000180') == '180'
        assert normalize_boxer_id('000269') == '269'
        assert normalize_boxer_id('000609') == '609'
        assert normalize_boxer_id('001491') == '1491'
        assert normalize_boxer_id('002224') == '2224'
        assert normalize_boxer_id('008683') == '8683'
        assert normalize_boxer_id('009010') == '9010'
        assert normalize_boxer_id('009030') == '9030'
        assert normalize_boxer_id('009032') == '9032'
        assert normalize_boxer_id('009086') == '9086'
        assert normalize_boxer_id('013019') == '13019'
        assert normalize_boxer_id('014260') == '14260'
    
    def test_preserves_ids_without_leading_zeros(self):
        """Test that IDs without leading zeros are unchanged."""
        assert normalize_boxer_id('80') == '80'
        assert normalize_boxer_id('147') == '147'
        assert normalize_boxer_id('1491') == '1491'
        assert normalize_boxer_id('272717') == '272717'
        assert normalize_boxer_id('611983') == '611983'
    
    def test_handles_zero(self):
        """Test that '0' and '000' normalize to '0'."""
        assert normalize_boxer_id('0') == '0'
        assert normalize_boxer_id('00') == '0'
        assert normalize_boxer_id('000') == '0'
        assert normalize_boxer_id('0000') == '0'
    
    def test_handles_invalid_input(self):
        """Test that invalid input is returned unchanged."""
        assert normalize_boxer_id('') == ''
        assert normalize_boxer_id(None) == None
        assert normalize_boxer_id('abc') == 'abc'
        assert normalize_boxer_id('123abc') == '123abc'
    
    def test_real_examples_from_database(self):
        """Test normalization on real examples from the database."""
        # These are the IDs from the screenshot that have leading zeros
        test_cases = [
            ('000080', '80'),
            ('000147', '147'),
            ('000180', '180'),
            ('000269', '269'),
            ('000609', '609'),
            ('001491', '1491'),
            ('002224', '2224'),
            ('008683', '8683'),
            ('008999', '8999'),
            ('009010', '9010'),
            ('009030', '9030'),
            ('009032', '9032'),
            ('009086', '9086'),
            ('013019', '13019'),
            ('014260', '14260'),
        ]
        
        for input_id, expected in test_cases:
            assert normalize_boxer_id(input_id) == expected, f"Failed for {input_id}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])