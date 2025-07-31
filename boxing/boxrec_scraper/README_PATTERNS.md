# BoxRec URL Patterns and Entity Configuration

The main configuration for BoxRec URL patterns and entity types is located in:

**`config/boxrec_patterns.py`**

## Entity Types We Track

### Currently Active:
1. **Boxer Profiles** (`/box-pro/{id}`) - Primary focus
2. **Boxer Wiki** (`/wiki/Human:{id}`) - Additional biographical data

### Future Entities (Defined but not yet scraped):
3. **Bouts** (`/bout/{id}`) - Individual fight details
4. **Events** (`/event/{id}`) - Event/card information
5. **Venues** (`/venue/{id}`) - Venue information
6. **Ratings** (`/ratings`) - Current rankings by division
7. **Schedule** (`/schedule`) - Upcoming boxing events
8. **Title Fights** (`/titles`) - Title fight schedule
9. **Gyms/Clubs** (`/clubs`) - Gym directory
10. **Individual Gyms** (`/gym/{id}`) - Specific gym pages
11. **People by Location** (`/locations/people`) - Geographic browsing

### Also Defined (lower priority):
- Promoters (`/promoter/{id}`)
- Managers (`/manager/{id}`)
- Referees (`/referee/{id}`)
- Judges (`/judge/{id}`)
- Specific Locations (`/locations/people/{country}/{region}`)

## How It Works

The configuration defines:
- URL patterns for each entity type
- What fields to extract from each page type
- Priority levels (1=highest)
- Language requirements
- Related entities for cross-linking

## Usage

```python
from config.boxrec_patterns import get_entity_by_url, get_urls_for_entity

# Parse a URL to identify its type
entity_type, data = get_entity_by_url("https://boxrec.com/en/box-pro/628407")
# Returns: ('boxer', {'id': '628407', 'language': 'en'})

# Generate URLs for an entity
urls = get_urls_for_entity('boxer', '628407', ['en', 'es'])
# Returns: ['https://boxrec.com/en/box-pro/628407', 'https://boxrec.com/es/box-pro/628407']
```

## Adding New Entity Types

To track a new entity type, add it to `BOXREC_ENTITIES` in the config file and include it in `ACTIVE_ENTITIES` when ready to start scraping.