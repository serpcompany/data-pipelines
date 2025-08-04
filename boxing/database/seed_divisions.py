#!/usr/bin/env python3
"""Seed the divisions table with static boxing division data."""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from boxing.database.staging_mirror import get_connection as get_staging_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use exact data from frontend schema
DIVISIONS = [
    {"id":"bantamweight","slug":"bantamweight","name":"Bantamweight","shortName":"bantam","alternativeNames":None,"weightLimitPounds":118,"weightLimitKilograms":53.525,"weightLimitStone":"8st 6lbs"},
    {"id":"cruiserweight","slug":"cruiserweight","name":"Cruiserweight","shortName":"cruiser","alternativeNames":"Junior Heavyweight","weightLimitPounds":200,"weightLimitKilograms":90.718,"weightLimitStone":"14st 4lbs"},
    {"id":"featherweight","slug":"featherweight","name":"Featherweight","shortName":"feather","alternativeNames":None,"weightLimitPounds":126,"weightLimitKilograms":57.153,"weightLimitStone":"9st"},
    {"id":"flyweight","slug":"flyweight","name":"Flyweight","shortName":"fly","alternativeNames":None,"weightLimitPounds":112,"weightLimitKilograms":50.802,"weightLimitStone":"8st"},
    {"id":"heavyweight","slug":"heavyweight","name":"Heavyweight","shortName":"heavy","alternativeNames":None,"weightLimitPounds":201,"weightLimitKilograms":90.719,"weightLimitStone":"14st 5lbs"},
    {"id":"light-flyweight","slug":"light-flyweight","name":"Light Flyweight","shortName":"light fly","alternativeNames":"Junior Flyweight","weightLimitPounds":108,"weightLimitKilograms":48.988,"weightLimitStone":"7st 10lbs"},
    {"id":"light-heavyweight","slug":"light-heavyweight","name":"Light Heavyweight","shortName":"light heavy","alternativeNames":None,"weightLimitPounds":175,"weightLimitKilograms":79.378,"weightLimitStone":"12st 7lbs"},
    {"id":"lightweight","slug":"lightweight","name":"Lightweight","shortName":"light","alternativeNames":None,"weightLimitPounds":135,"weightLimitKilograms":61.235,"weightLimitStone":"9st 9lbs"},
    {"id":"middleweight","slug":"middleweight","name":"Middleweight","shortName":"middle","alternativeNames":None,"weightLimitPounds":160,"weightLimitKilograms":72.574,"weightLimitStone":"11st 6lbs"},
    {"id":"minimumweight","slug":"minimumweight","name":"Minimumweight","shortName":"minimum","alternativeNames":"Mini Flyweight","weightLimitPounds":105,"weightLimitKilograms":47.627,"weightLimitStone":"7st 7lbs"},
    {"id":"super-bantamweight","slug":"super-bantamweight","name":"Super Bantamweight","shortName":"super bantam","alternativeNames":"Junior Featherweight","weightLimitPounds":122,"weightLimitKilograms":55.338,"weightLimitStone":"8st 10lbs"},
    {"id":"super-featherweight","slug":"super-featherweight","name":"Super Featherweight","shortName":"super feather","alternativeNames":"Junior Lightweight","weightLimitPounds":130,"weightLimitKilograms":58.967,"weightLimitStone":"9st 4lbs"},
    {"id":"super-flyweight","slug":"super-flyweight","name":"Super Flyweight","shortName":"super fly","alternativeNames":"Junior Bantamweight","weightLimitPounds":115,"weightLimitKilograms":52.163,"weightLimitStone":"8st 3lbs"},
    {"id":"super-lightweight","slug":"super-lightweight","name":"Super Lightweight","shortName":"super light","alternativeNames":"Junior Welterweight","weightLimitPounds":140,"weightLimitKilograms":63.503,"weightLimitStone":"10st"},
    {"id":"super-middleweight","slug":"super-middleweight","name":"Super Middleweight","shortName":"super middle","alternativeNames":None,"weightLimitPounds":168,"weightLimitKilograms":76.203,"weightLimitStone":"12st"},
    {"id":"super-welterweight","slug":"super-welterweight","name":"Super Welterweight","shortName":"super welter","alternativeNames":"Junior Middleweight","weightLimitPounds":154,"weightLimitKilograms":69.85,"weightLimitStone":"11st"},
    {"id":"welterweight","slug":"welterweight","name":"Welterweight","shortName":"welter","alternativeNames":None,"weightLimitPounds":147,"weightLimitKilograms":66.678,"weightLimitStone":"10st 7lbs"}
]


def seed_divisions():
    """Seed the divisions table with static data."""
    conn = get_staging_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing data
        cursor.execute("DELETE FROM divisions")
        logger.info("Cleared existing divisions data")
        
        # Insert divisions
        now = datetime.now().isoformat()
        
        for division in DIVISIONS:
            cursor.execute("""
                INSERT INTO divisions (
                    id, slug, name, shortName, alternativeNames,
                    weightLimitPounds, weightLimitKilograms, weightLimitStone,
                    createdAt, updatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                division['id'],
                division['slug'],
                division['name'],
                division['shortName'],
                division['alternativeNames'],
                division['weightLimitPounds'],
                division['weightLimitKilograms'],
                division['weightLimitStone'],
                now,
                now
            ))
        
        conn.commit()
        logger.info(f"Successfully seeded {len(DIVISIONS)} divisions")
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM divisions")
        count = cursor.fetchone()[0]
        logger.info(f"Divisions table now contains {count} records")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error seeding divisions: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
    
    seed_divisions()