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

# Standard boxing divisions data
DIVISIONS = [
    {
        'id': 'heavyweight',
        'slug': 'heavyweight',
        'name': 'Heavyweight',
        'shortName': 'HW',
        'alternativeNames': 'Heavy',
        'weightLimitPounds': 999,  # No limit
        'weightLimitKilograms': 453.6,
        'weightLimitStone': '71st 6lb'
    },
    {
        'id': 'cruiserweight',
        'slug': 'cruiserweight',
        'name': 'Cruiserweight',
        'shortName': 'CW',
        'alternativeNames': 'Cruiser',
        'weightLimitPounds': 200,
        'weightLimitKilograms': 90.7,
        'weightLimitStone': '14st 4lb'
    },
    {
        'id': 'light-heavyweight',
        'slug': 'light-heavyweight',
        'name': 'Light Heavyweight',
        'shortName': 'LHW',
        'alternativeNames': 'Light Heavy',
        'weightLimitPounds': 175,
        'weightLimitKilograms': 79.4,
        'weightLimitStone': '12st 7lb'
    },
    {
        'id': 'super-middleweight',
        'slug': 'super-middleweight',
        'name': 'Super Middleweight',
        'shortName': 'SMW',
        'alternativeNames': 'Super Middle',
        'weightLimitPounds': 168,
        'weightLimitKilograms': 76.2,
        'weightLimitStone': '12st'
    },
    {
        'id': 'middleweight',
        'slug': 'middleweight',
        'name': 'Middleweight',
        'shortName': 'MW',
        'alternativeNames': 'Middle',
        'weightLimitPounds': 160,
        'weightLimitKilograms': 72.6,
        'weightLimitStone': '11st 6lb'
    },
    {
        'id': 'super-welterweight',
        'slug': 'super-welterweight',
        'name': 'Super Welterweight',
        'shortName': 'SWW',
        'alternativeNames': 'Light Middleweight,Junior Middleweight',
        'weightLimitPounds': 154,
        'weightLimitKilograms': 69.9,
        'weightLimitStone': '11st'
    },
    {
        'id': 'welterweight',
        'slug': 'welterweight',
        'name': 'Welterweight',
        'shortName': 'WW',
        'alternativeNames': 'Welter',
        'weightLimitPounds': 147,
        'weightLimitKilograms': 66.7,
        'weightLimitStone': '10st 7lb'
    },
    {
        'id': 'super-lightweight',
        'slug': 'super-lightweight',
        'name': 'Super Lightweight',
        'shortName': 'SLW',
        'alternativeNames': 'Light Welterweight,Junior Welterweight',
        'weightLimitPounds': 140,
        'weightLimitKilograms': 63.5,
        'weightLimitStone': '10st'
    },
    {
        'id': 'lightweight',
        'slug': 'lightweight',
        'name': 'Lightweight',
        'shortName': 'LW',
        'alternativeNames': 'Light',
        'weightLimitPounds': 135,
        'weightLimitKilograms': 61.2,
        'weightLimitStone': '9st 9lb'
    },
    {
        'id': 'super-featherweight',
        'slug': 'super-featherweight',
        'name': 'Super Featherweight',
        'shortName': 'SFW',
        'alternativeNames': 'Junior Lightweight',
        'weightLimitPounds': 130,
        'weightLimitKilograms': 59.0,
        'weightLimitStone': '9st 4lb'
    },
    {
        'id': 'featherweight',
        'slug': 'featherweight',
        'name': 'Featherweight',
        'shortName': 'FW',
        'alternativeNames': 'Feather',
        'weightLimitPounds': 126,
        'weightLimitKilograms': 57.2,
        'weightLimitStone': '9st'
    },
    {
        'id': 'super-bantamweight',
        'slug': 'super-bantamweight',
        'name': 'Super Bantamweight',
        'shortName': 'SBW',
        'alternativeNames': 'Junior Featherweight',
        'weightLimitPounds': 122,
        'weightLimitKilograms': 55.3,
        'weightLimitStone': '8st 10lb'
    },
    {
        'id': 'bantamweight',
        'slug': 'bantamweight',
        'name': 'Bantamweight',
        'shortName': 'BW',
        'alternativeNames': 'Bantam',
        'weightLimitPounds': 118,
        'weightLimitKilograms': 53.5,
        'weightLimitStone': '8st 6lb'
    },
    {
        'id': 'super-flyweight',
        'slug': 'super-flyweight',
        'name': 'Super Flyweight',
        'shortName': 'SFly',
        'alternativeNames': 'Light Flyweight,Junior Bantamweight',
        'weightLimitPounds': 115,
        'weightLimitKilograms': 52.2,
        'weightLimitStone': '8st 3lb'
    },
    {
        'id': 'flyweight',
        'slug': 'flyweight',
        'name': 'Flyweight',
        'shortName': 'Fly',
        'alternativeNames': 'Fly',
        'weightLimitPounds': 112,
        'weightLimitKilograms': 50.8,
        'weightLimitStone': '8st'
    },
    {
        'id': 'light-flyweight',
        'slug': 'light-flyweight',
        'name': 'Light Flyweight',
        'shortName': 'LFly',
        'alternativeNames': 'Junior Flyweight',
        'weightLimitPounds': 108,
        'weightLimitKilograms': 49.0,
        'weightLimitStone': '7st 10lb'
    },
    {
        'id': 'minimumweight',
        'slug': 'minimumweight',
        'name': 'Minimumweight',
        'shortName': 'Min',
        'alternativeNames': 'Strawweight,Mini Flyweight',
        'weightLimitPounds': 105,
        'weightLimitKilograms': 47.6,
        'weightLimitStone': '7st 7lb'
    }
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
                division.get('alternativeNames', ''),
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