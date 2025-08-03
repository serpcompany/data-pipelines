"""Orchestrator for extracting data from HTML."""

import logging
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

# Import all field extractors
from .page.boxer.fields import (
    name, nationality, stance,
    birth_date, birth_place, residence, height, reach,
    debut_date_pro, status_pro, wins_pro, wins_by_knockout_pro,
    losses_pro, losses_by_knockout_pro, draws_pro,
    promoters, trainers, managers, gym
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
            'date_of_birth': birth_date,
            'birth_place': birth_place,
            'residence': residence,
            'height': height,
            'reach': reach,
            'debut_date': debut_date_pro,
            'status': status_pro,
            'wins': wins_pro,
            'ko_wins': wins_by_knockout_pro,
            'losses': losses_pro,
            'ko_losses': losses_by_knockout_pro,
            'draws': draws_pro,
            'promoters': promoters,
            'trainers': trainers,
            'managers': managers,
            'gym': gym
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
            
            # Extract bouts (simplified for now)
            extracted_data['bouts'] = self.extract_bouts(soup)
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error in extraction orchestration: {e}")
            return None
    
    def extract_bouts(self, soup: BeautifulSoup) -> list:
        """Extract bout information from HTML."""
        bouts = []
        
        try:
            # Find the bouts table (this is simplified - real implementation would be more robust)
            bout_rows = soup.select('table.dataTable tbody tr')
            
            for row in bout_rows:
                cells = row.find_all('td')
                if len(cells) >= 8:  # Minimum expected columns
                    bout = {
                        'date': cells[0].get_text(strip=True),
                        'opponent': cells[1].get_text(strip=True),
                        'opponent_url': cells[1].find('a')['href'] if cells[1].find('a') else None,
                        'result': cells[2].get_text(strip=True),
                        'location': cells[4].get_text(strip=True) if len(cells) > 4 else None,
                        'rounds': cells[5].get_text(strip=True) if len(cells) > 5 else None,
                    }
                    bouts.append(bout)
        
        except Exception as e:
            logger.error(f"Error extracting bouts: {e}")
        
        return bouts