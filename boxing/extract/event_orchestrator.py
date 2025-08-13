"""Orchestrator for extracting data from Event HTML."""

import logging
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

# Import all event field extractors
from .page.event.fields import (
    location,
    commission,
    event_name,
    promoter,
    matchmaker,
    inspector,
    doctor,
    watch_link,
    bouts,
)

# Import all bout field extractors
from .page.bout.fields import (
    boxer_a_side,
    boxer_b_side,
    bout_division,
    bout_rounds_scheduled,
    titles,
    bout_result,
    bout_result_method,
    bout_rounds_actual,
    scorecards,
    referee,
    judges,
    stoppage_reason,
    boxer_a_side_rating,
    boxer_a_side_record,
    boxer_a_side_age,
    boxer_a_side_stance,
    boxer_a_side_height,
    boxer_a_side_reach,
    boxer_b_side_rating,
    boxer_b_side_record,
    boxer_b_side_age,
    boxer_b_side_stance,
    boxer_b_side_height,
    boxer_b_side_reach,
    competition_level,
)

logger = logging.getLogger(__name__)


class EventExtractionOrchestrator:
    """Orchestrate extraction of all fields from event HTML."""

    def __init__(self):
        # Map field names to event extractor modules
        self.event_extractors = {
            "location": location,
            "commission": commission,
            "event_name": event_name,
            "promoter": promoter,
            "matchmaker": matchmaker,
            "inspector": inspector,
            "doctor": doctor,
            "watch_link": watch_link,
            "bouts": bouts,
        }

        # Map field names to bout extractor modules
        self.bout_extractors = {
            "boxer_a_side": boxer_a_side,
            "boxer_b_side": boxer_b_side,
            "bout_division": bout_division,
            "bout_rounds_scheduled": bout_rounds_scheduled,
            "titles": titles,
            "bout_result": bout_result,
            "bout_result_method": bout_result_method,
            "bout_rounds_actual": bout_rounds_actual,
            "scorecards": scorecards,
            "referee": referee,
            "judges": judges,
            "doctor": doctor,
            "inspector": inspector,
            "matchmaker": matchmaker,
            "promoter": promoter,
            "stoppage_reason": stoppage_reason,
            "boxer_a_side_rating": boxer_a_side_rating,
            "boxer_a_side_record": boxer_a_side_record,
            "boxer_a_side_age": boxer_a_side_age,
            "boxer_a_side_stance": boxer_a_side_stance,
            "boxer_a_side_height": boxer_a_side_height,
            "boxer_a_side_reach": boxer_a_side_reach,
            "boxer_b_side_rating": boxer_b_side_rating,
            "boxer_b_side_record": boxer_b_side_record,
            "boxer_b_side_age": boxer_b_side_age,
            "boxer_b_side_stance": boxer_b_side_stance,
            "boxer_b_side_height": boxer_b_side_height,
            "boxer_b_side_reach": boxer_b_side_reach,
            "competition_level": competition_level,
        }

    def extract_event_data(self, html_content: str) -> Dict[str, Any]:
        """
        Extract all event fields from HTML content.

        Args:
            html_content: Raw HTML string

        Returns:
            dict: Extracted event data
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            data = {}

            # Extract all event fields
            for field_name, extractor in self.event_extractors.items():
                try:
                    value = extractor.extract(soup)
                    data[field_name] = value
                    logger.debug(f"Extracted {field_name}: {value}")
                except Exception as e:
                    logger.error(f"Error extracting {field_name}: {e}")
                    data[field_name] = None

            return data

        except Exception as e:
            logger.error(f"Error parsing HTML for event extraction: {e}")
            return {}

    def extract_bout_data(
        self, html_content: str, event_id: str, bout_id: str
    ) -> Dict[str, Any]:
        """
        Extract all bout fields from HTML content.

        Args:
            html_content: Raw HTML string
            event_id: Event ID
            bout_id: Bout ID

        Returns:
            dict: Extracted bout data
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            data = {"boxrec_event_id": event_id, "boxrec_bout_id": bout_id}

            # Extract all bout fields
            for field_name, extractor in self.bout_extractors.items():
                try:
                    value = extractor.extract(soup)
                    data[field_name] = value
                    logger.debug(f"Extracted {field_name}: {value}")
                except Exception as e:
                    logger.error(f"Error extracting {field_name}: {e}")
                    data[field_name] = None

            return data

        except Exception as e:
            logger.error(f"Error parsing HTML for bout extraction: {e}")
            return {"boxrec_event_id": event_id, "boxrec_bout_id": bout_id}
