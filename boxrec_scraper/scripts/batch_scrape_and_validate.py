#!/usr/bin/env python3
"""
Batch script to run scraping and validation pipeline steps 1-4:
1. Scrape Boxer HTML files
2. Scrape Wiki Pages  
3. Validate HTML
4. Detect and cleanup login pages
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_scrape_and_validate.log'),
        logging.StreamHandler()
    ]
)

def run_command(cmd, description):
    """Run a command and handle errors."""
    logging.info(f"\n{'='*60}")
    logging.info(f"Starting: {description}")
    logging.info(f"Command: {' '.join(cmd)}")
    logging.info(f"{'='*60}")
    
    start_time = time.time()
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        elapsed = time.time() - start_time
        
        logging.info(f"✅ Completed: {description}")
        logging.info(f"Time taken: {elapsed:.1f} seconds")
        
        if result.stdout:
            logging.info(f"Output:\n{result.stdout}")
            
        return True
        
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        logging.error(f"❌ Failed: {description}")
        logging.error(f"Time taken: {elapsed:.1f} seconds")
        logging.error(f"Error code: {e.returncode}")
        
        if e.stdout:
            logging.error(f"Output:\n{e.stdout}")
        if e.stderr:
            logging.error(f"Error:\n{e.stderr}")
            
        return False

def main():
    """Run all scraping and validation steps."""
    # Change to project directory
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    os.chdir(project_dir)
    
    logging.info(f"Starting batch scrape and validate pipeline")
    logging.info(f"Working directory: {os.getcwd()}")
    logging.info(f"Start time: {datetime.now()}")
    
    # Define the pipeline steps
    steps = [
        {
            'description': 'Step 1: Scrape Boxer HTML files',
            'cmd': ['python', 'scripts/scrape/scrape_boxers_html.py', 'data/5000boxers.csv'],
            'critical': True
        },
        {
            'description': 'Step 2: Scrape Wiki Pages',
            'cmd': ['python', 'scripts/scrape/scrape_wiki_html.py'],
            'critical': False  # Wiki scraping can fail without blocking pipeline
        },
        {
            'description': 'Step 3: Validate HTML',
            'cmd': ['python', 'scripts/validate/validate_scrapes.py'],
            'critical': False
        },
        {
            'description': 'Step 4: Detect and cleanup login pages',
            'cmd': ['python', 'scripts/cleaning/cleanup_login_files.py'],
            'critical': True
        }
    ]
    
    # Track results
    results = []
    total_start = time.time()
    
    # Run each step
    for i, step in enumerate(steps, 1):
        success = run_command(step['cmd'], step['description'])
        results.append({
            'step': i,
            'description': step['description'],
            'success': success
        })
        
        # Stop if critical step fails
        if not success and step['critical']:
            logging.error(f"Critical step failed. Stopping pipeline.")
            break
            
        # Small delay between steps
        if i < len(steps):
            time.sleep(2)
    
    # Summary
    total_elapsed = time.time() - total_start
    logging.info(f"\n{'='*60}")
    logging.info("PIPELINE SUMMARY")
    logging.info(f"{'='*60}")
    logging.info(f"Total time: {total_elapsed/60:.1f} minutes")
    logging.info(f"Steps completed: {len(results)}/{len(steps)}")
    
    for result in results:
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        logging.info(f"{result['step']}. {result['description']}: {status}")
    
    # Check for login blocked URLs
    login_blocked_file = Path('data/login_blocked_urls.csv')
    if login_blocked_file.exists():
        with open(login_blocked_file, 'r') as f:
            line_count = sum(1 for line in f) - 1  # Subtract header
        logging.info(f"\n⚠️  Found {line_count} login-blocked URLs")
        logging.info(f"To re-scrape these URLs, run:")
        logging.info(f"python scripts/scrape/scrape_boxers_html.py {login_blocked_file}")
    
    # Return exit code based on results
    all_success = all(r['success'] for r in results)
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())