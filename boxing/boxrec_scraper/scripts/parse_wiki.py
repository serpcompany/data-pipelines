#!/usr/bin/env python3
"""
Parse BoxRec wiki pages to extract additional boxer information.
"""

import json
import re
import sys
import logging
from pathlib import Path
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def clean_text(text):
    """Clean and normalize text."""
    if not text:
        return None
    # Remove excessive whitespace and newlines
    text = ' '.join(text.split())
    # Remove wiki reference markers like [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)
    return text.strip()

def extract_trainers(soup):
    """Extract trainer information from wiki page."""
    trainers = []
    
    # Look for trainer info in lists
    for li in soup.find_all('li'):
        text = li.get_text()
        if 'Trainer' in text and ':' in text:
            # Extract everything after "Trainer:" or "Trainers:"
            trainer_text = text.split(':', 1)[1]
            # Clean up and split by common separators
            trainer_text = clean_text(trainer_text)
            if trainer_text:
                # Handle multiple trainers separated by commas or parentheses
                trainer_parts = re.split(r'[,()]', trainer_text)
                for part in trainer_parts:
                    part = part.strip()
                    # Skip date ranges
                    if part and not re.match(r'^\d{4}-\d{4}$', part):
                        trainers.append(part)
    
    return list(set(trainers))  # Remove duplicates

def extract_managers(soup):
    """Extract manager information from wiki page."""
    managers = []
    
    for li in soup.find_all('li'):
        text = li.get_text()
        if 'Manager' in text and ':' in text:
            manager_text = text.split(':', 1)[1]
            manager_text = clean_text(manager_text)
            if manager_text:
                manager_parts = re.split(r'[,()]', manager_text)
                for part in manager_parts:
                    part = part.strip()
                    if part and not re.match(r'^\d{4}-\d{4}$', part):
                        managers.append(part)
    
    return list(set(managers))

def extract_bio_section(soup):
    """Extract biography or career summary text."""
    bio_text = []
    
    # Look for specific sections
    section_headers = ['Biography', 'Early life', 'Career', 'Professional career', 'Amateur career']
    
    for header in section_headers:
        # Find h2 or h3 with this header
        header_elem = None
        for h in soup.find_all(['h2', 'h3']):
            if header.lower() in h.get_text().lower():
                header_elem = h
                break
        
        if header_elem:
            # Get paragraphs following this header until next header
            current = header_elem.find_next_sibling()
            while current and current.name not in ['h2', 'h3']:
                if current.name == 'p':
                    text = clean_text(current.get_text())
                    if text and len(text) > 50:  # Skip very short paragraphs
                        bio_text.append(text)
                current = current.find_next_sibling()
    
    # Join paragraphs
    return ' '.join(bio_text[:3]) if bio_text else None  # Limit to first 3 paragraphs

def extract_additional_info(soup):
    """Extract other useful information from wiki page."""
    info = {}
    
    # Look for structured data in the wiki infobox-style content
    for p in soup.find_all('p'):
        text = p.get_text()
        
        # Birth date pattern
        birth_match = re.search(r'Born:\s*(\d{4}-\d{2}-\d{2})', text)
        if birth_match:
            info['date_of_birth'] = birth_match.group(1)
        
        # Gym pattern
        if 'Gym:' in text:
            gym_text = text.split('Gym:', 1)[1].split('\n')[0]
            info['gym'] = clean_text(gym_text)
    
    # Extract amateur record if present
    amateur_link = soup.find('a', href=re.compile(r'/box-am/\d+'))
    if amateur_link:
        info['has_amateur_record'] = True
    
    return info

def parse_wiki_file(wiki_path):
    """Parse a single wiki HTML file."""
    try:
        with open(wiki_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Extract BoxRec ID from filename
        boxrec_id = re.search(r'wiki_box-pro_(\d+)\.html', str(wiki_path))
        if not boxrec_id:
            return None
        
        boxrec_id = boxrec_id.group(1)
        
        # Extract data
        data = {
            'boxrec_id': boxrec_id,
            'wiki_data': {
                'trainers': extract_trainers(soup),
                'managers': extract_managers(soup),
                'bio': extract_bio_section(soup),
                'additional_info': extract_additional_info(soup)
            }
        }
        
        # Clean up empty fields
        if not data['wiki_data']['trainers']:
            data['wiki_data']['trainers'] = None
        if not data['wiki_data']['managers']:
            data['wiki_data']['managers'] = None
        
        return data
        
    except Exception as e:
        logging.error(f"Error parsing {wiki_path}: {e}")
        return None

def merge_wiki_data(boxer_data, wiki_data):
    """Merge wiki data into existing boxer data."""
    if not wiki_data:
        return boxer_data
    
    # Update fields if wiki has better data
    wiki_info = wiki_data.get('wiki_data', {})
    
    # Trainers
    if wiki_info.get('trainers') and not boxer_data.get('trainer'):
        # Take the first trainer as primary
        boxer_data['trainer'] = wiki_info['trainers'][0]
    
    # Managers
    if wiki_info.get('managers') and not boxer_data.get('manager'):
        boxer_data['manager'] = wiki_info['managers'][0]
    
    # Bio
    if wiki_info.get('bio') and not boxer_data.get('bio'):
        boxer_data['bio'] = wiki_info['bio']
    
    # Additional info
    additional = wiki_info.get('additional_info', {})
    if additional.get('date_of_birth') and not boxer_data.get('date_of_birth'):
        boxer_data['date_of_birth'] = additional['date_of_birth']
    if additional.get('gym') and not boxer_data.get('gym'):
        boxer_data['gym'] = additional['gym']
    
    # Add wiki_scraped flag
    boxer_data['wiki_scraped'] = True
    
    return boxer_data

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_wiki.py <wiki_dir> [boxer_json_file]")
        print("\nExamples:")
        print("  Parse all wiki files: python parse_wiki.py data/raw/boxrec_wiki/")
        print("  Merge with boxer data: python parse_wiki.py data/raw/boxrec_wiki/ outputs/combined_boxers.json")
        sys.exit(1)
    
    wiki_dir = Path(sys.argv[1])
    boxer_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    # Parse all wiki files
    wiki_files = list(wiki_dir.glob('wiki_box-pro_*.html'))
    logging.info(f"Found {len(wiki_files)} wiki files to parse")
    
    wiki_data_map = {}
    successful = 0
    
    for wiki_file in wiki_files:
        data = parse_wiki_file(wiki_file)
        if data:
            wiki_data_map[data['boxrec_id']] = data
            successful += 1
            logging.info(f"✅ Parsed {wiki_file.name}")
    
    logging.info(f"\nParsed {successful}/{len(wiki_files)} wiki files successfully")
    
    # If boxer file provided, merge the data
    if boxer_file and boxer_file.exists():
        logging.info(f"\nMerging with boxer data from {boxer_file}")
        
        with open(boxer_file, 'r') as f:
            content = f.read()
            
        # Handle metadata + array format
        if content.startswith('{'):
            parts = content.split('},\n[', 1)
            if len(parts) == 2:
                metadata = json.loads(parts[0] + '}')
                boxers = json.loads('[' + parts[1])
            else:
                data = json.loads(content)
                metadata = data.get('_metadata', {})
                boxers = data.get('boxers', [])
        else:
            metadata = {}
            boxers = json.loads(content)
        
        # Merge wiki data
        updated = 0
        for boxer in boxers:
            boxrec_id = boxer.get('boxrec_id')
            if boxrec_id and boxrec_id in wiki_data_map:
                merge_wiki_data(boxer, wiki_data_map[boxrec_id])
                updated += 1
        
        # Update metadata
        metadata['wiki_scraped'] = True
        metadata['wiki_update_date'] = datetime.now(timezone.utc).isoformat()
        
        # Save updated file
        output_file = boxer_file.parent / f"{boxer_file.stem}_with_wiki.json"
        with open(output_file, 'w') as f:
            json.dump(metadata, f, indent=2)
            f.write(',\n')
            json.dump(boxers, f, indent=2)
        
        logging.info(f"✅ Updated {updated} boxers with wiki data")
        logging.info(f"💾 Saved to: {output_file}")
    
    else:
        # Just save parsed wiki data
        output_file = wiki_dir / 'parsed_wiki_data.json'
        with open(output_file, 'w') as f:
            json.dump(list(wiki_data_map.values()), f, indent=2)
        
        logging.info(f"\n💾 Wiki data saved to: {output_file}")

if __name__ == "__main__":
    from datetime import datetime, timezone
    main()