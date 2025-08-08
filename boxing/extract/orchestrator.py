"""Orchestrator for extracting data from HTML."""

import logging
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

# Import all field extractors
from .page.boxer.fields import (
    name, nationality, stance, nicknames,
    avatar_image, birth_name, gender,
    birth_date, birth_place, residence, height, reach,
    debut_date_pro, debut_date_amateur,
    division_pro, division_amateur,
    status_pro, status_amateur,
    wins_pro, wins_by_knockout_pro, wins_amateur, wins_by_knockout_amateur,
    losses_pro, losses_by_knockout_pro, losses_amateur, losses_by_knockout_amateur,
    draws_pro, draws_amateur,
    rounds_pro, rounds_amateur,
    promoters, trainers, managers, gym, bouts
)

logger = logging.getLogger(__name__)

class ExtractionOrchestrator:
    """Orchestrate extraction of all fields from boxer HTML."""
    
    def __init__(self):
        # Map field names to extractor modules
        self.extractors = {
            'name': name,
            'nationality': nationality,
            'stance': stance,
            'nicknames': nicknames,
            'avatar_image': avatar_image,
            'birth_name': birth_name,
            'gender': gender,
            'date_of_birth': birth_date,
            'birth_place': birth_place,
            'residence': residence,
            'height': height,
            'reach': reach,
            'debut_date_pro': debut_date_pro,
            'debut_date_amateur': debut_date_amateur,
            'division_pro': division_pro,
            'division_amateur': division_amateur,
            'status_pro': status_pro,
            'status_amateur': status_amateur,
            'wins_pro': wins_pro,
            'ko_wins_pro': wins_by_knockout_pro,
            'wins_amateur': wins_amateur,
            'ko_wins_amateur': wins_by_knockout_amateur,
            'losses_pro': losses_pro,
            'ko_losses_pro': losses_by_knockout_pro,
            'losses_amateur': losses_amateur,
            'ko_losses_amateur': losses_by_knockout_amateur,
            'draws_pro': draws_pro,
            'draws_amateur': draws_amateur,
            'rounds_pro': rounds_pro,
            'rounds_amateur': rounds_amateur,
            'promoters': promoters,
            'trainers': trainers,
            'managers': managers,
            'gym': gym,
            'bouts': bouts
        }
    
    def extract_field(self, field_name: str, soup: BeautifulSoup) -> Any:
        """Extract a single field from the HTML."""
        if field_name not in self.extractors:
            logger.warning(f"No extractor found for field: {field_name}")
            return None
        
        try:
            extractor_module = self.extractors[field_name]
            return extractor_module.extract(soup)
        except Exception as e:
            logger.error(f"Error extracting {field_name}: {e}")
            return None
    
    def extract_all(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract all fields from boxer HTML."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract all fields
            extracted_data = {}
            for field_name in self.extractors:
                value = self.extract_field(field_name, soup)
                if value is not None:
                    extracted_data[field_name] = value
            
            # Extract bouts using the dedicated extractor
            # Note: 'bouts' is already in self.extractors, so it's extracted above
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error in extraction orchestration: {e}")
            return None
    
