#!/usr/bin/env python3
"""
Scrape BoxRec RecentChanges to track updates.
"""

import json
import re
import requests
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)

# Zyte API configuration
ZYTE_API_KEY = os.getenv('ZYTE_API_KEY')
ZYTE_API_URL = "https://api.zyte.com/v1/extract"

class BoxRecChangeTracker:
    """Track recent changes on BoxRec wiki."""
    
    def __init__(self, inventory_path: Optional[Path] = None):
        self.inventory_path = inventory_path or Path('data/boxrec_inventory.json')
        self.changes_file = Path('data/recent_changes.json')
        self.load_inventory()
        
    def load_inventory(self):
        """Load existing inventory."""
        if self.inventory_path.exists():
            with open(self.inventory_path, 'r') as f:
                self.inventory = json.load(f)
        else:
            self.inventory = {'boxers': {}}
            
    def fetch_recent_changes_zyte(self, days: int = 7, limit: int = 500) -> Optional[str]:
        """Fetch RecentChanges page using Zyte API."""
        url = f"https://boxrec.com/wiki/index.php/Special:RecentChanges?limit={limit}&days={days}&enhanced=1&urlversion=2"
        
        if not ZYTE_API_KEY:
            logging.error("ZYTE_API_KEY not found in environment variables")
            return None
            
        try:
            response = requests.post(
                ZYTE_API_URL,
                json={
                    "url": url,
                    "httpResponseBody": True,
                    "httpResponseHeaders": True
                },
                auth=(ZYTE_API_KEY, ""),
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'httpResponseBody' in data:
                    import base64
                    html_content = base64.b64decode(data['httpResponseBody']).decode('utf-8')
                    
                    # Save for reference
                    output_dir = Path('data/raw/boxrec_wiki')
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    with open(output_dir / 'recent_changes.html', 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    return html_content
            else:
                logging.error(f"Zyte API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logging.error(f"Error fetching recent changes: {e}")
            
        return None
    
    def parse_recent_changes(self, html_content: str) -> Dict[str, List[Dict]]:
        """Parse RecentChanges HTML to extract updates."""
        soup = BeautifulSoup(html_content, 'html.parser')
        changes = {
            'boxer_updates': [],
            'event_updates': [],
            'other_updates': [],
            'parse_time': datetime.now(timezone.utc).isoformat()
        }
        
        # Find all change entries
        change_entries = soup.find_all(['li', 'tr'], class_=re.compile('mw-changeslist-line'))
        
        for entry in change_entries:
            try:
                # Extract page title and link
                title_link = entry.find('a', {'class': 'mw-changeslist-title'})
                if not title_link:
                    continue
                    
                page_title = title_link.get_text(strip=True)
                page_url = title_link.get('href', '')
                
                # Extract timestamp
                timestamp_elem = entry.find(['span', 'a'], {'class': 'mw-changeslist-date'})
                timestamp = timestamp_elem.get_text(strip=True) if timestamp_elem else None
                
                # Extract user who made the change
                user_elem = entry.find('a', {'class': ['mw-userlink', 'mw-anonuserlink']})
                user = user_elem.get_text(strip=True) if user_elem else 'Unknown'
                
                # Extract change size
                size_elem = entry.find('span', {'class': re.compile('mw-plusminus')})
                size_change = size_elem.get_text(strip=True) if size_elem else None
                
                # Categorize the change
                change_info = {
                    'title': page_title,
                    'url': f"https://boxrec.com{page_url}" if page_url.startswith('/') else page_url,
                    'timestamp': timestamp,
                    'user': user,
                    'size_change': size_change
                }
                
                # Check if it's a boxer page
                if 'Human:' in page_title or '/box-pro/' in page_url:
                    # Extract boxer ID
                    id_match = re.search(r'Human:(\d+)|box-pro/(\d+)', page_title + page_url)
                    if id_match:
                        boxer_id = id_match.group(1) or id_match.group(2)
                        change_info['boxer_id'] = boxer_id
                        changes['boxer_updates'].append(change_info)
                elif 'Event:' in page_title or '/event/' in page_url:
                    # Extract event ID
                    id_match = re.search(r'Event:(\d+)|event/(\d+)', page_title + page_url)
                    if id_match:
                        event_id = id_match.group(1) or id_match.group(2)
                        change_info['event_id'] = event_id
                        changes['event_updates'].append(change_info)
                else:
                    changes['other_updates'].append(change_info)
                    
            except Exception as e:
                logging.warning(f"Error parsing change entry: {e}")
                continue
        
        return changes
    
    def identify_needed_updates(self, changes: Dict) -> Dict[str, List]:
        """Compare recent changes with our inventory to identify needed updates."""
        needed_updates = {
            'boxers_to_rescrape': [],
            'new_boxers': [],
            'events_to_scrape': [],
            'summary': {}
        }
        
        # Check boxer updates
        updated_boxer_ids = set()
        for change in changes['boxer_updates']:
            if 'boxer_id' in change:
                updated_boxer_ids.add(change['boxer_id'])
        
        # Compare with our inventory
        our_boxer_ids = set(self.inventory.get('boxers', {}).keys())
        
        for boxer_id in updated_boxer_ids:
            if boxer_id in our_boxer_ids:
                # Check if our version is older than the update
                boxer_data = self.inventory['boxers'][boxer_id]
                last_scraped = boxer_data.get('last_scraped', {})
                
                # Get most recent scrape time
                most_recent = None
                for scrape_time in last_scraped.values():
                    if scrape_time:
                        dt = datetime.fromisoformat(scrape_time.replace('Z', '+00:00'))
                        if not most_recent or dt > most_recent:
                            most_recent = dt
                
                # If we haven't scraped in the last 7 days, mark for update
                if not most_recent or (datetime.now(timezone.utc) - most_recent) > timedelta(days=7):
                    needed_updates['boxers_to_rescrape'].append({
                        'id': boxer_id,
                        'last_scraped': most_recent.isoformat() if most_recent else None,
                        'reason': 'Recent wiki update detected'
                    })
            else:
                needed_updates['new_boxers'].append(boxer_id)
        
        # Summary
        needed_updates['summary'] = {
            'total_boxer_changes': len(updated_boxer_ids),
            'boxers_needing_rescrape': len(needed_updates['boxers_to_rescrape']),
            'new_boxers_found': len(needed_updates['new_boxers']),
            'checked_date': datetime.now(timezone.utc).isoformat()
        }
        
        return needed_updates
    
    def save_changes(self, changes: Dict):
        """Save recent changes to file."""
        self.changes_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.changes_file, 'w') as f:
            json.dump(changes, f, indent=2)


def main():
    """Check recent changes and identify needed updates."""
    tracker = BoxRecChangeTracker()
    
    print("🔍 Fetching recent changes from BoxRec...")
    html_content = tracker.fetch_recent_changes_zyte(days=7)
    
    if not html_content:
        print("❌ Failed to fetch recent changes")
        return
    
    print("📊 Parsing changes...")
    changes = tracker.parse_recent_changes(html_content)
    tracker.save_changes(changes)
    
    print(f"\n📈 Recent Changes Summary:")
    print(f"- Boxer updates: {len(changes['boxer_updates'])}")
    print(f"- Event updates: {len(changes['event_updates'])}")
    print(f"- Other updates: {len(changes['other_updates'])}")
    
    print("\n🔄 Identifying needed updates...")
    needed = tracker.identify_needed_updates(changes)
    
    print(f"\n⚡ Updates Needed:")
    print(f"- Boxers to re-scrape: {needed['summary']['boxers_needing_rescrape']}")
    print(f"- New boxers found: {needed['summary']['new_boxers_found']}")
    
    if needed['boxers_to_rescrape'][:5]:
        print(f"\nFirst 5 boxers needing update:")
        for boxer in needed['boxers_to_rescrape'][:5]:
            print(f"  - {boxer['id']}: last scraped {boxer['last_scraped'] or 'never'}")
    
    # Save needed updates
    output_file = Path('data/needed_updates.json')
    with open(output_file, 'w') as f:
        json.dump(needed, f, indent=2)
    print(f"\n💾 Needed updates saved to: {output_file}")


if __name__ == "__main__":
    main()