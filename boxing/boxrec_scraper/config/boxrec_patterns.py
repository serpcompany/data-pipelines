#!/usr/bin/env python3
"""
BoxRec URL patterns and entity configuration.
Central location for defining what we track and scrape.
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class EntityPattern:
    """Configuration for a BoxRec entity type."""
    name: str
    url_pattern: str
    id_regex: str
    requires_languages: bool = True
    has_wiki: bool = False
    priority: int = 1  # 1=highest, 5=lowest
    fields_to_extract: List[str] = field(default_factory=list)
    related_entities: List[str] = field(default_factory=list)
    description: str = ""


# Define all BoxRec entity patterns we track
BOXREC_ENTITIES = {
    'boxer': EntityPattern(
        name='Boxer Profile',
        url_pattern='https://boxrec.com/{lang}/box-pro/{id}',
        id_regex=r'box-pro[/_](\d+)',
        requires_languages=True,
        has_wiki=True,
        priority=1,
        fields_to_extract=[
            'full_name', 'nickname', 'image_url', 'date_of_birth', 
            'nationality', 'division', 'stance', 'height', 'reach',
            'record', 'KOs', 'bouts', 'manager', 'trainer', 'gym'
        ],
        related_entities=['bout', 'event', 'venue'],
        description="Individual boxer profile pages containing career statistics and bout history"
    ),
    
    'boxer_wiki': EntityPattern(
        name='Boxer Wiki',
        url_pattern='https://boxrec.com/wiki/index.php?title=Human:{id}',
        id_regex=r'Human:(\d+)',
        requires_languages=False,
        has_wiki=False,  # This IS the wiki
        priority=2,
        fields_to_extract=['bio', 'trainers', 'managers', 'amateur_record'],
        related_entities=['boxer'],
        description="Wiki pages with additional biographical information about boxers"
    ),
    
    'bout': EntityPattern(
        name='Bout/Fight',
        url_pattern='https://boxrec.com/{lang}/bout/{id}',
        id_regex=r'bout[/_](\d+)',
        requires_languages=True,
        has_wiki=False,
        priority=3,
        fields_to_extract=[
            'date', 'result', 'method', 'round', 'time',
            'boxer1_id', 'boxer2_id', 'event_id', 'venue_id',
            'referee', 'judges', 'scorecards'
        ],
        related_entities=['boxer', 'event', 'venue'],
        description="Individual bout/fight pages with detailed fight information"
    ),
    
    'event': EntityPattern(
        name='Event/Card',
        url_pattern='https://boxrec.com/{lang}/event/{id}',
        id_regex=r'event[/_](\d+)',
        requires_languages=True,
        has_wiki=False,
        priority=3,
        fields_to_extract=[
            'event_name', 'date', 'venue_id', 'promoter',
            'bouts', 'attendance', 'gate_revenue'
        ],
        related_entities=['bout', 'venue', 'boxer'],
        description="Boxing event/card pages listing all fights on the card"
    ),
    
    'venue': EntityPattern(
        name='Venue',
        url_pattern='https://boxrec.com/{lang}/venue/{id}',
        id_regex=r'venue[/_](\d+)',
        requires_languages=True,
        has_wiki=False,
        priority=4,
        fields_to_extract=[
            'venue_name', 'location', 'city', 'country',
            'capacity', 'events_held'
        ],
        related_entities=['event', 'bout'],
        description="Boxing venue pages with location and event history"
    ),
    
    'ratings': EntityPattern(
        name='Ratings/Rankings',
        url_pattern='https://boxrec.com/{lang}/ratings',
        id_regex=r'ratings',
        requires_languages=True,
        has_wiki=False,
        priority=2,
        fields_to_extract=['division_rankings', 'pound_for_pound', 'date'],
        related_entities=['boxer'],
        description="Current BoxRec ratings and rankings by division"
    ),
    
    'schedule': EntityPattern(
        name='Schedule',
        url_pattern='https://boxrec.com/{lang}/schedule',
        id_regex=r'schedule',
        requires_languages=True,
        has_wiki=False,
        priority=3,
        fields_to_extract=['upcoming_events', 'dates', 'venues', 'fight_types'],
        related_entities=['event', 'bout', 'boxer'],
        description="Upcoming boxing events and fight schedule"
    ),
    
    'titles': EntityPattern(
        name='Title Fights Schedule',
        url_pattern='https://boxrec.com/{lang}/titles',
        id_regex=r'titles',
        requires_languages=True,
        has_wiki=False,
        priority=2,
        fields_to_extract=['title_fights', 'champions', 'dates', 'organizations'],
        related_entities=['boxer', 'bout', 'event'],
        description="Upcoming and recent title fights across all organizations"
    ),
    
    'clubs': EntityPattern(
        name='Gyms/Clubs',
        url_pattern='https://boxrec.com/{lang}/clubs',
        id_regex=r'clubs',
        requires_languages=True,
        has_wiki=False,
        priority=4,
        fields_to_extract=['gym_list', 'locations', 'boxer_count', 'trainers'],
        related_entities=['boxer', 'gym'],
        description="Boxing gyms and clubs directory"
    ),
    
    'gym': EntityPattern(
        name='Individual Gym',
        url_pattern='https://boxrec.com/{lang}/gym/{id}',
        id_regex=r'gym[/_](\d+)',
        requires_languages=True,
        has_wiki=False,
        priority=4,
        fields_to_extract=['gym_name', 'location', 'boxers', 'trainers', 'established'],
        related_entities=['boxer', 'trainer'],
        description="Individual gym/club pages with boxer rosters"
    ),
    
    'locations_people': EntityPattern(
        name='People by Location',
        url_pattern='https://boxrec.com/{lang}/locations/people',
        id_regex=r'locations/people',
        requires_languages=True,
        has_wiki=False,
        priority=3,
        fields_to_extract=['countries', 'regions', 'boxer_counts', 'active_boxers'],
        related_entities=['boxer', 'location'],
        description="Browse boxers and boxing people by geographic location"
    ),
    
    'location': EntityPattern(
        name='Specific Location',
        url_pattern='https://boxrec.com/{lang}/locations/people/{country}/{region}',
        id_regex=r'locations/people/([^/]+)(?:/([^/]+))?',
        requires_languages=True,
        has_wiki=False,
        priority=4,
        fields_to_extract=['boxers', 'trainers', 'managers', 'promoters'],
        related_entities=['boxer', 'trainer', 'manager', 'promoter'],
        description="People from a specific country/region"
    ),
    
    'promoter': EntityPattern(
        name='Promoter',
        url_pattern='https://boxrec.com/{lang}/promoter/{id}',
        id_regex=r'promoter[/_](\d+)',
        requires_languages=True,
        has_wiki=False,
        priority=4,
        fields_to_extract=['name', 'events', 'boxers'],
        related_entities=['event', 'boxer'],
        description="Boxing promoter pages"
    ),
    
    'manager': EntityPattern(
        name='Manager',
        url_pattern='https://boxrec.com/{lang}/manager/{id}',
        id_regex=r'manager[/_](\d+)',
        requires_languages=True,
        has_wiki=False,
        priority=5,
        fields_to_extract=['name', 'boxers_managed'],
        related_entities=['boxer'],
        description="Boxing manager pages"
    ),
    
    'referee': EntityPattern(
        name='Referee',
        url_pattern='https://boxrec.com/{lang}/referee/{id}',
        id_regex=r'referee[/_](\d+)',
        requires_languages=True,
        has_wiki=False,
        priority=5,
        fields_to_extract=['name', 'bouts_refereed'],
        related_entities=['bout'],
        description="Boxing referee pages"
    ),
    
    'judge': EntityPattern(
        name='Judge',
        url_pattern='https://boxrec.com/{lang}/judge/{id}',
        id_regex=r'judge[/_](\d+)',
        requires_languages=True,
        has_wiki=False,
        priority=5,
        fields_to_extract=['name', 'bouts_judged'],
        related_entities=['bout'],
        description="Boxing judge pages"
    )
}


# Languages we care about (in priority order)
SUPPORTED_LANGUAGES = ['en', 'es', 'fr', 'de', 'ru', 'it', 'ja', 'zh']
PRIMARY_LANGUAGE = 'en'


# Define which entities we're actively tracking
ACTIVE_ENTITIES = [
    'boxer',          # Primary focus
    'boxer_wiki',     # Secondary data source
    'bout',           # Future: individual fight details
    'event',          # Future: event/card information
    'venue',          # Future: venue information
    'ratings',        # Future: current rankings
    'schedule',       # Future: upcoming fights
    'titles',         # Future: title fight schedule
    'clubs',          # Future: gym directory
    'gym',            # Future: individual gyms
    'locations_people' # Future: geographic browsing
]


def get_entity_by_url(url: str) -> tuple[str, dict]:
    """
    Identify entity type from a BoxRec URL.
    Returns (entity_type, extracted_data) or (None, {})
    """
    import re
    
    for entity_type, pattern in BOXREC_ENTITIES.items():
        match = re.search(pattern.id_regex, url)
        if match:
            data = {'id': match.group(1) if match.lastindex else entity_type}
            
            # Extract language if present
            lang_match = re.search(r'boxrec\.com/(\w{2})/', url)
            if lang_match:
                data['language'] = lang_match.group(1)
            
            return entity_type, data
    
    return None, {}


def get_urls_for_entity(entity_type: str, entity_id: str, languages: List[str] = None) -> List[str]:
    """Generate all URLs for a given entity."""
    if entity_type not in BOXREC_ENTITIES:
        return []
    
    pattern = BOXREC_ENTITIES[entity_type]
    urls = []
    
    if pattern.requires_languages:
        langs = languages or [PRIMARY_LANGUAGE]
        for lang in langs:
            url = pattern.url_pattern.format(lang=lang, id=entity_id)
            urls.append(url)
    else:
        url = pattern.url_pattern.format(id=entity_id)
        urls.append(url)
    
    return urls


def get_priority_entities() -> List[str]:
    """Get entity types sorted by priority."""
    return sorted(
        [e for e in ACTIVE_ENTITIES if e in BOXREC_ENTITIES],
        key=lambda x: BOXREC_ENTITIES[x].priority
    )


if __name__ == "__main__":
    # Example usage
    print("📋 BoxRec Entity Configuration\n")
    
    print("Active entity types:")
    for entity in get_priority_entities():
        pattern = BOXREC_ENTITIES[entity]
        print(f"\n{pattern.priority}. {pattern.name}:")
        print(f"   Pattern: {pattern.url_pattern}")
        print(f"   Description: {pattern.description}")
        print(f"   Fields: {', '.join(pattern.fields_to_extract[:5])}...")
    
    print("\n\nExample URL parsing:")
    test_urls = [
        "https://boxrec.com/en/box-pro/628407",
        "https://boxrec.com/wiki/index.php?title=Human:628407",
        "https://boxrec.com/en/event/761409",
        "https://boxrec.com/en/venue/246558"
    ]
    
    for url in test_urls:
        entity_type, data = get_entity_by_url(url)
        print(f"\n{url}")
        print(f"  → Type: {entity_type}, Data: {data}")