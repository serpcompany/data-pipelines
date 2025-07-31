#!/usr/bin/env python3
"""
Generate comprehensive update plan for BoxRec scraping.
Combines inventory data with recent changes to create actionable plan.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Set
import logging

logging.basicConfig(level=logging.INFO)

class UpdatePlanGenerator:
    """Generate update plans for BoxRec scraping."""
    
    def __init__(self):
        self.inventory_file = Path('data/boxrec_inventory.json')
        self.changes_file = Path('data/recent_changes.json')
        self.needed_updates_file = Path('data/needed_updates.json')
        self.update_plan_file = Path('data/update_plan.json')
        
    def load_data(self) -> tuple:
        """Load inventory and changes data."""
        inventory = {}
        changes = {}
        needed_updates = {}
        
        if self.inventory_file.exists():
            with open(self.inventory_file, 'r') as f:
                inventory = json.load(f)
                
        if self.changes_file.exists():
            with open(self.changes_file, 'r') as f:
                changes = json.load(f)
                
        if self.needed_updates_file.exists():
            with open(self.needed_updates_file, 'r') as f:
                needed_updates = json.load(f)
                
        return inventory, changes, needed_updates
    
    def generate_update_plan(self) -> Dict:
        """Generate comprehensive update plan."""
        inventory, changes, needed_updates = self.load_data()
        
        plan = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'priorities': {
                'high': [],
                'medium': [],
                'low': []
            },
            'tasks': {
                'wiki_scraping': [],
                'profile_updates': [],
                'new_boxers': [],
                'reparse_needed': []
            },
            'statistics': {},
            'execution_order': []
        }
        
        # 1. High Priority: Missing wiki pages for existing boxers
        boxers_without_wiki = []
        for boxer_id, boxer_data in inventory.get('boxers', {}).items():
            if 'wiki' not in boxer_data.get('files', {}):
                boxers_without_wiki.append({
                    'id': boxer_id,
                    'task': 'scrape_wiki',
                    'url': f"https://boxrec.com/wiki/index.php?title=Human:{boxer_id}",
                    'reason': 'Missing wiki page'
                })
        
        plan['tasks']['wiki_scraping'] = boxers_without_wiki
        plan['priorities']['high'].extend([b['id'] for b in boxers_without_wiki[:20]])  # First 20 as high priority
        
        # 2. Medium Priority: Recent updates needing rescrape
        if needed_updates:
            for boxer in needed_updates.get('boxers_to_rescrape', []):
                plan['tasks']['profile_updates'].append({
                    'id': boxer['id'],
                    'task': 'rescrape_profile',
                    'reason': boxer['reason'],
                    'last_scraped': boxer.get('last_scraped')
                })
                plan['priorities']['medium'].append(boxer['id'])
        
        # 3. Low Priority: Language variants
        for boxer_id, boxer_data in inventory.get('boxers', {}).items():
            langs = set()
            for file_key in boxer_data.get('files', {}):
                if file_key.startswith('profile_'):
                    langs.add(file_key.split('_')[1])
            
            if langs and 'en' not in langs:
                plan['priorities']['low'].append({
                    'id': boxer_id,
                    'task': 'add_english_version',
                    'has_languages': list(langs)
                })
        
        # 4. Generate execution order
        execution_steps = []
        
        # Step 1: Complete wiki scraping for high-value boxers
        if plan['tasks']['wiki_scraping']:
            execution_steps.append({
                'step': 1,
                'action': 'scrape_wiki_pages',
                'target_count': min(20, len(plan['tasks']['wiki_scraping'])),
                'boxer_ids': [b['id'] for b in plan['tasks']['wiki_scraping'][:20]],
                'estimated_time': '30-60 minutes',
                'command': 'python scripts/scrape_wiki_zyte.py'
            })
        
        # Step 2: Parse all wiki pages
        execution_steps.append({
            'step': 2,
            'action': 'parse_wiki_pages',
            'command': 'python scripts/parse_wiki.py data/raw/boxrec_wiki/',
            'estimated_time': '5 minutes'
        })
        
        # Step 3: Regenerate combined JSON with wiki data
        execution_steps.append({
            'step': 3,
            'action': 'combine_all_data',
            'command': 'python scripts/combine_boxer_json_v2.py',
            'estimated_time': '2 minutes'
        })
        
        # Step 4: Rescrape updated profiles
        if plan['tasks']['profile_updates']:
            execution_steps.append({
                'step': 4,
                'action': 'rescrape_updated_profiles',
                'target_count': len(plan['tasks']['profile_updates']),
                'boxer_ids': [b['id'] for b in plan['tasks']['profile_updates']],
                'estimated_time': '20-40 minutes'
            })
        
        plan['execution_order'] = execution_steps
        
        # 5. Generate statistics
        plan['statistics'] = {
            'total_boxers': len(inventory.get('boxers', {})),
            'boxers_with_wiki': sum(1 for b in inventory.get('boxers', {}).values() if 'wiki' in b.get('files', {})),
            'missing_wiki': len(plan['tasks']['wiki_scraping']),
            'needs_update': len(plan['tasks']['profile_updates']),
            'missing_english': len([p for p in plan['priorities']['low'] if isinstance(p, dict)]),
            'completeness_score': self._calculate_completeness(inventory)
        }
        
        return plan
    
    def _calculate_completeness(self, inventory: Dict) -> float:
        """Calculate overall completeness score."""
        if not inventory.get('boxers'):
            return 0.0
            
        total_boxers = len(inventory['boxers'])
        scores = []
        
        for boxer_data in inventory['boxers'].values():
            boxer_score = 0
            # Has profile: 40%
            if any(k.startswith('profile_') for k in boxer_data.get('files', {})):
                boxer_score += 40
            # Has English profile: +10%
            if 'profile_en' in boxer_data.get('files', {}):
                boxer_score += 10
            # Has wiki: 30%
            if 'wiki' in boxer_data.get('files', {}):
                boxer_score += 30
            # Has v2 parse: 20%
            if any(k.startswith('parsed_v2') for k in boxer_data.get('files', {})):
                boxer_score += 20
                
            scores.append(boxer_score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def save_plan(self, plan: Dict):
        """Save update plan to file."""
        self.update_plan_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.update_plan_file, 'w') as f:
            json.dump(plan, f, indent=2)
    
    def print_plan_summary(self, plan: Dict):
        """Print human-readable plan summary."""
        print("\n" + "="*60)
        print("📋 BoxRec Update Plan Summary")
        print("="*60)
        
        print(f"\n📊 Current Status:")
        stats = plan['statistics']
        print(f"  Total Boxers: {stats['total_boxers']}")
        print(f"  With Wiki: {stats['boxers_with_wiki']} ({stats['boxers_with_wiki']/stats['total_boxers']*100:.1f}%)")
        print(f"  Completeness: {stats['completeness_score']:.1f}%")
        
        print(f"\n🎯 Tasks Identified:")
        print(f"  Wiki Pages to Scrape: {stats['missing_wiki']}")
        print(f"  Profiles Needing Update: {stats['needs_update']}")
        print(f"  Missing English Versions: {stats['missing_english']}")
        
        print(f"\n📝 Execution Plan:")
        for step in plan['execution_order']:
            print(f"\n  Step {step['step']}: {step['action']}")
            if 'target_count' in step:
                print(f"    Target: {step['target_count']} items")
            if 'command' in step:
                print(f"    Command: {step['command']}")
            print(f"    Est. Time: {step['estimated_time']}")
        
        print(f"\n🚀 Next Actions:")
        if plan['execution_order']:
            first_step = plan['execution_order'][0]
            print(f"  1. Run: {first_step.get('command', 'See step details')}")
            print(f"  2. This will process {first_step.get('target_count', 'N/A')} items")
            
        print(f"\n💾 Full plan saved to: {self.update_plan_file}")
        print("="*60)


def main():
    """Generate and display update plan."""
    generator = UpdatePlanGenerator()
    
    print("🔍 Analyzing current state and generating update plan...")
    plan = generator.generate_update_plan()
    generator.save_plan(plan)
    generator.print_plan_summary(plan)
    
    # Also save a quick reference file
    quick_ref = Path('data/NEXT_STEPS.md')
    with open(quick_ref, 'w') as f:
        f.write("# BoxRec Scraper - Next Steps\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if plan['execution_order']:
            f.write("## Immediate Actions:\n\n")
            for i, step in enumerate(plan['execution_order'][:3], 1):
                f.write(f"{i}. **{step['action']}**\n")
                if 'command' in step:
                    f.write(f"   ```bash\n   {step['command']}\n   ```\n")
                f.write(f"   - Items: {step.get('target_count', 'All')}\n")
                f.write(f"   - Time: {step['estimated_time']}\n\n")
        
        f.write(f"\n## Current Status:\n")
        stats = plan['statistics']
        f.write(f"- Total Boxers: {stats['total_boxers']}\n")
        f.write(f"- Wiki Coverage: {stats['boxers_with_wiki']}/{stats['total_boxers']} ")
        f.write(f"({stats['boxers_with_wiki']/stats['total_boxers']*100:.1f}%)\n")
        f.write(f"- Completeness Score: {stats['completeness_score']:.1f}%\n")
    
    print(f"\n📄 Quick reference saved to: {quick_ref}")


if __name__ == "__main__":
    main()