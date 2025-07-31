#!/usr/bin/env python3
"""
BoxRec URL inventory and tracking system.
Tracks what we have scraped and what needs updating.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Optional
import logging
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config.boxrec_patterns import BOXREC_ENTITIES, get_entity_by_url, get_urls_for_entity

logging.basicConfig(level=logging.INFO)

class BoxRecInventory:
    """Manages inventory of BoxRec URLs and their scrape status."""
    
    def __init__(self, project_root: Path = Path('.')):
        self.project_root = project_root
        self.inventory_file = project_root / 'data' / 'boxrec_inventory.json'
        self.inventory = self.load_inventory()
        
    def load_inventory(self) -> Dict:
        """Load existing inventory or create new one."""
        if self.inventory_file.exists():
            with open(self.inventory_file, 'r') as f:
                return json.load(f)
        return {
            'boxers': {},
            'events': {},
            'venues': {},
            'other': {},
            'last_updated': None
        }
    
    def save_inventory(self):
        """Save inventory to file."""
        self.inventory['last_updated'] = datetime.now(timezone.utc).isoformat()
        self.inventory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.inventory_file, 'w') as f:
            json.dump(self.inventory, f, indent=2)
    
    def scan_existing_files(self):
        """Scan project for existing scraped files and update inventory."""
        # Scan boxer HTML files
        boxer_html_dir = self.project_root / 'data' / 'raw' / 'boxrec_html'
        if boxer_html_dir.exists():
            for html_file in boxer_html_dir.glob('*box-pro*.html'):
                match = re.search(r'(en|es|de|fr|ru)_box-pro_(\d+)\.html', html_file.name)
                if match:
                    lang, boxrec_id = match.groups()
                    self._update_boxer_entry(boxrec_id, lang, 'profile', html_file)
        
        # Scan wiki HTML files
        wiki_dir = self.project_root / 'data' / 'raw' / 'boxrec_wiki'
        if wiki_dir.exists():
            for wiki_file in wiki_dir.glob('wiki_box-pro_*.html'):
                match = re.search(r'wiki_box-pro_(\d+)\.html', wiki_file.name)
                if match:
                    boxrec_id = match.group(1)
                    self._update_boxer_entry(boxrec_id, 'en', 'wiki', wiki_file)
        
        # Scan processed JSON files
        json_dir = self.project_root / 'data' / 'processed' / 'v2'
        if json_dir.exists():
            for json_file in json_dir.glob('*box-pro*.json'):
                match = re.search(r'(en|es|de|fr|ru)_box-pro_(\d+)\.json', json_file.name)
                if match:
                    lang, boxrec_id = match.groups()
                    self._update_boxer_entry(boxrec_id, lang, 'parsed_v2', json_file)
        
        # Scan event files
        if boxer_html_dir.exists():
            for event_file in boxer_html_dir.glob('*event*.html'):
                match = re.search(r'(en|es|de|fr|ru)_event_(\d+)\.html', event_file.name)
                if match:
                    lang, event_id = match.groups()
                    self._update_event_entry(event_id, lang, event_file)
        
        # Scan venue files
        if boxer_html_dir.exists():
            for venue_file in boxer_html_dir.glob('*venue*.html'):
                match = re.search(r'(en|es|de|fr|ru)_venue_(\d+)\.html', venue_file.name)
                if match:
                    lang, venue_id = match.groups()
                    self._update_venue_entry(venue_id, lang, venue_file)
        
        self.save_inventory()
        
    def _update_boxer_entry(self, boxrec_id: str, lang: str, file_type: str, file_path: Path):
        """Update boxer entry in inventory."""
        if boxrec_id not in self.inventory['boxers']:
            self.inventory['boxers'][boxrec_id] = {
                'id': boxrec_id,
                'urls': {},
                'files': {},
                'last_scraped': {},
                'needs_update': False
            }
        
        boxer = self.inventory['boxers'][boxrec_id]
        
        # Update URLs
        if file_type == 'profile':
            boxer['urls'][f'profile_{lang}'] = f"https://boxrec.com/{lang}/box-pro/{boxrec_id}"
        elif file_type == 'wiki':
            boxer['urls']['wiki'] = f"https://boxrec.com/wiki/index.php?title=Human:{boxrec_id}"
        
        # Update files
        boxer['files'][f'{file_type}_{lang}' if file_type != 'wiki' else 'wiki'] = str(file_path.relative_to(self.project_root))
        
        # Update last scraped time (use file modification time)
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc)
        boxer['last_scraped'][f'{file_type}_{lang}' if file_type != 'wiki' else 'wiki'] = mtime.isoformat()
        
    def _update_event_entry(self, event_id: str, lang: str, file_path: Path):
        """Update event entry in inventory."""
        if event_id not in self.inventory['events']:
            self.inventory['events'][event_id] = {
                'id': event_id,
                'urls': {},
                'files': {},
                'last_scraped': {}
            }
        
        event = self.inventory['events'][event_id]
        event['urls'][lang] = f"https://boxrec.com/{lang}/event/{event_id}"
        event['files'][lang] = str(file_path.relative_to(self.project_root))
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc)
        event['last_scraped'][lang] = mtime.isoformat()
        
    def _update_venue_entry(self, venue_id: str, lang: str, file_path: Path):
        """Update venue entry in inventory."""
        if venue_id not in self.inventory['venues']:
            self.inventory['venues'][venue_id] = {
                'id': venue_id,
                'urls': {},
                'files': {},
                'last_scraped': {}
            }
        
        venue = self.inventory['venues'][venue_id]
        venue['urls'][lang] = f"https://boxrec.com/{lang}/venue/{venue_id}"
        venue['files'][lang] = str(file_path.relative_to(self.project_root))
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc)
        venue['last_scraped'][lang] = mtime.isoformat()
    
    def get_boxrec_url_patterns(self) -> Dict[str, str]:
        """Return all BoxRec URL patterns we care about."""
        # Now using centralized configuration
        patterns = {}
        for entity_type, pattern in BOXREC_ENTITIES.items():
            patterns[entity_type] = pattern.url_pattern
        return patterns
    
    def get_missing_items(self) -> Dict[str, List]:
        """Identify what we're missing."""
        missing = {
            'wiki_pages': [],
            'other_languages': [],
            'parsed_files': []
        }
        
        for boxer_id, boxer_data in self.inventory['boxers'].items():
            # Check if we have wiki page
            if 'wiki' not in boxer_data['files']:
                missing['wiki_pages'].append(boxer_id)
            
            # Check if we have all language versions
            has_langs = set()
            for key in boxer_data['files']:
                if key.startswith('profile_'):
                    has_langs.add(key.split('_')[1])
            
            # We primarily care about English, but track what we have
            if 'en' not in has_langs and has_langs:
                missing['other_languages'].append({
                    'id': boxer_id,
                    'has': list(has_langs),
                    'missing': 'en'
                })
            
            # Check if parsed with v2
            if not any(key.startswith('parsed_v2') for key in boxer_data['files']):
                missing['parsed_files'].append(boxer_id)
        
        return missing
    
    def generate_summary(self) -> Dict:
        """Generate summary statistics."""
        summary = {
            'total_boxers': len(self.inventory['boxers']),
            'total_events': len(self.inventory['events']),
            'total_venues': len(self.inventory['venues']),
            'boxers_with_wiki': sum(1 for b in self.inventory['boxers'].values() if 'wiki' in b['files']),
            'boxers_parsed_v2': sum(1 for b in self.inventory['boxers'].values() if any(k.startswith('parsed_v2') for k in b['files'])),
            'languages': {}
        }
        
        # Count languages
        for boxer in self.inventory['boxers'].values():
            for file_key in boxer['files']:
                if file_key.startswith('profile_'):
                    lang = file_key.split('_')[1]
                    summary['languages'][lang] = summary['languages'].get(lang, 0) + 1
        
        return summary


def main():
    """Run inventory scan and generate report."""
    inventory = BoxRecInventory()
    
    print("🔍 Scanning existing files...")
    inventory.scan_existing_files()
    
    print("\n📊 Inventory Summary:")
    summary = inventory.generate_summary()
    print(json.dumps(summary, indent=2))
    
    print("\n❓ Missing Items:")
    missing = inventory.get_missing_items()
    print(f"- Wiki pages missing: {len(missing['wiki_pages'])} boxers")
    print(f"- Language variants: {len(missing['other_languages'])} boxers missing English")
    print(f"- Unparsed with v2: {len(missing['parsed_files'])} boxers")
    
    if missing['wiki_pages'][:5]:
        print(f"\nFirst 5 boxers missing wiki: {missing['wiki_pages'][:5]}")
    
    print(f"\n💾 Inventory saved to: {inventory.inventory_file}")


if __name__ == "__main__":
    main()