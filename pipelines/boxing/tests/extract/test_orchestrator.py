#!/usr/bin/env python3
"""Test that orchestrator correctly extracts bout data."""

import pytest
from pathlib import Path
from pipelines.boxing.extract.orchestrator import ExtractionOrchestrator


class TestOrchestratorBouts:
    """Test orchestrator bout extraction."""
    
    def test_orchestrator_extracts_bouts(self):
        """Test that orchestrator extracts bouts with correct field names."""
        # Load sample HTML
        test_file = Path(__file__).parent.parent / "samples" / "boxer_professional_floyd.html"
        if not test_file.exists():
            pytest.skip("Sample file not found")
        
        with open(test_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Extract using orchestrator
        orchestrator = ExtractionOrchestrator()
        data = orchestrator.extract_all(html_content)
        
        # Verify bouts were extracted
        assert 'bouts' in data, "Bouts should be extracted"
        assert isinstance(data['bouts'], list), "Bouts should be a list"
        assert len(data['bouts']) > 0, "Should have extracted at least one bout"
        
        # Check first bout has correct field names
        first_bout = data['bouts'][0]
        
        # These are the field names the extractor returns
        assert 'opponent_name' in first_bout, "Should have opponent_name field"
        assert 'venue' in first_bout, "Should have venue field"
        
        # These should NOT be in the output (they're the database field names)
        assert 'opponent' not in first_bout, "Should not have 'opponent' field"
        assert 'location' not in first_bout, "Should not have 'location' field"
        
        print(f"First bout extracted: {first_bout}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])