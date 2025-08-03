#!/usr/bin/env python3
"""
Interactive pipeline runner for BoxRec data pipeline.
Allows running individual steps or ranges of steps.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Pipeline steps definition
PIPELINE_STEPS = [
    {
        'id': 1,
        'name': 'Scrape Boxer HTML files',
        'script': 'scripts/scrape/scrape_boxers_html.py',
        'args': ['data/5000boxers.csv'],
        'description': 'Scrapes boxer pages from BoxRec'
    },
    {
        'id': 2,
        'name': 'Scrape Wiki Pages',
        'script': 'scripts/scrape/scrape_wiki_html.py',
        'args': [],
        'description': 'Scrapes wiki pages for boxers'
    },
    {
        'id': 3,
        'name': 'Validate HTML',
        'script': 'scripts/validate/validate_scrapes.py',
        'args': [],
        'description': 'Validates scraped HTML files'
    },
    {
        'id': 4,
        'name': 'Detect and Cleanup Login Pages',
        'script': 'scripts/cleaning/cleanup_login_files.py',
        'args': [],
        'description': 'Identifies login pages and creates retry list'
    },
    {
        'id': 5,
        'name': 'Upload HTML to Database',
        'script': 'scripts/upload/upload_boxer_html_to_db.py',
        'args': [],
        'description': 'Uploads raw HTML to database'
    },
    {
        'id': 6,
        'name': 'Extract Opponent URLs',
        'script': 'scripts/extract_urls_from_raw_html/extract_opponent_urls.py',
        'args': [],
        'description': 'Extracts opponent URLs from HTML'
    },
    {
        'id': 7,
        'name': 'Extract Bout URLs',
        'script': 'scripts/extract_urls_from_raw_html/extract_bout_urls.py',
        'args': [],
        'description': 'Extracts bout URLs from HTML'
    },
    {
        'id': 8,
        'name': 'Parse Boxer HTML to JSON',
        'script': 'scripts/batch_parse_boxers.py',
        'args': [],
        'description': 'Parses HTML files to JSON with login detection'
    },
    {
        'id': 9,
        'name': 'Extract All Individual Fields',
        'script': 'scripts/extract/batch_extract_all.py',
        'args': [],
        'description': 'Runs all field extractors'
    }
]

class PipelineRunner:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        os.chdir(self.base_dir)
        
    def print_menu(self):
        """Print the pipeline menu."""
        print("\n" + "="*60)
        print("BOXREC DATA PIPELINE RUNNER")
        print("="*60)
        print("\nAvailable steps:")
        for step in PIPELINE_STEPS:
            print(f"  {step['id']:2d}. {step['name']}")
            print(f"      {step['description']}")
        print("\nOptions:")
        print("  - Enter a number to run a single step")
        print("  - Enter a range (e.g., '3-5') to run multiple steps")
        print("  - Enter 'all' to run all steps")
        print("  - Enter 'status' to check pipeline status")
        print("  - Enter 'q' to quit")
        print("="*60)
        
    def run_step(self, step):
        """Run a single pipeline step."""
        print(f"\n{'='*60}")
        print(f"Running Step {step['id']}: {step['name']}")
        print(f"Script: {step['script']}")
        print(f"{'='*60}")
        
        script_path = self.base_dir / step['script']
        if not script_path.exists():
            print(f"❌ Error: Script not found: {script_path}")
            return False
            
        cmd = ['python', str(script_path)] + step['args']
        print(f"Command: {' '.join(cmd)}")
        
        start_time = time.time()
        try:
            result = subprocess.run(cmd, check=True)
            elapsed = time.time() - start_time
            print(f"\n✅ Step {step['id']} completed successfully in {elapsed:.1f} seconds")
            return True
        except subprocess.CalledProcessError as e:
            elapsed = time.time() - start_time
            print(f"\n❌ Step {step['id']} failed after {elapsed:.1f} seconds")
            print(f"Error: {e}")
            return False
            
    def check_status(self):
        """Check the status of the pipeline."""
        print("\n" + "="*60)
        print("PIPELINE STATUS CHECK")
        print("="*60)
        
        # Check for HTML files
        html_dir = self.base_dir / 'data' / 'raw' / 'boxrec_html'
        if html_dir.exists():
            html_files = list(html_dir.glob('*.html'))
            print(f"\n✓ HTML files: {len(html_files)}")
            
            # Check for login files
            from scripts.utils.login_detector import find_login_pages
            login_files = find_login_pages(html_dir)
            print(f"  - Login pages: {len(login_files)}")
            print(f"  - Valid pages: {len(html_files) - len(login_files)}")
        else:
            print("\n✗ No HTML directory found")
            
        # Check for JSON files
        json_dir = self.base_dir / 'data' / 'processed' / 'boxrec_json'
        if json_dir.exists():
            json_files = list(json_dir.glob('*.json'))
            print(f"\n✓ JSON files: {len(json_files)}")
        else:
            print("\n✗ No JSON directory found")
            
        # Check for CSV files
        csv_files = {
            'login_blocked_urls.csv': 'Login blocked URLs',
            'opponent_urls.csv': 'Opponent URLs',
            'bout_urls.csv': 'Bout URLs'
        }
        
        print("\nCSV files:")
        for filename, description in csv_files.items():
            filepath = self.base_dir / 'data' / filename
            if filepath.exists():
                with open(filepath, 'r') as f:
                    line_count = sum(1 for line in f) - 1  # Subtract header
                print(f"  ✓ {description}: {line_count} entries")
            else:
                print(f"  ✗ {description}: Not found")
                
    def run(self):
        """Main runner loop."""
        while True:
            self.print_menu()
            choice = input("\nEnter your choice: ").strip().lower()
            
            if choice == 'q':
                print("Exiting pipeline runner.")
                break
            elif choice == 'status':
                self.check_status()
                input("\nPress Enter to continue...")
            elif choice == 'all':
                print("\nRunning all pipeline steps...")
                for step in PIPELINE_STEPS:
                    if not self.run_step(step):
                        if input("\nStep failed. Continue? (y/n): ").lower() != 'y':
                            break
            elif '-' in choice:
                # Range of steps
                try:
                    start, end = map(int, choice.split('-'))
                    for step in PIPELINE_STEPS:
                        if start <= step['id'] <= end:
                            if not self.run_step(step):
                                if input("\nStep failed. Continue? (y/n): ").lower() != 'y':
                                    break
                except ValueError:
                    print("❌ Invalid range format. Use format like '3-5'")
            else:
                # Single step
                try:
                    step_id = int(choice)
                    step = next((s for s in PIPELINE_STEPS if s['id'] == step_id), None)
                    if step:
                        self.run_step(step)
                    else:
                        print(f"❌ Invalid step number: {step_id}")
                except ValueError:
                    print("❌ Invalid input. Please enter a number, range, or command.")
                    
            if choice != 'status':
                input("\nPress Enter to continue...")

if __name__ == "__main__":
    runner = PipelineRunner()
    runner.run()