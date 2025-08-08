#!/usr/bin/env python3
"""
Master script to run the complete boxing data pipeline.
Coordinates all ETL steps from scraping to production deployment.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from boxing.database.staging_mirror import get_staging_db
from boxing.database import run_change_detection
from boxing.load.to_staging_mirror_db import run_staging_load
from boxing.database.validators import run_validation
from boxing.database.deploy import deploy_to_preview

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_database():
    """Set up the staging mirror database."""
    logger.info("Setting up staging mirror database...")
    db = get_staging_db()
    db.push_schema()
    
    # Seed divisions table
    logger.info("Seeding divisions table...")
    from boxing.database.seed_divisions import seed_divisions
    seed_divisions()
    
    logger.info("Database setup complete")
    return True

def load_data(limit=None):
    """Load data from data lake to staging mirror."""
    logger.info("Loading data to staging mirror database...")
    result = run_staging_load(limit=limit)
    
    logger.info(f"Loaded {result['load_summary']['successful']} NEW records successfully")
    logger.info(f"Staging database now contains: {result['staging_stats']['total_boxers']} total boxers, "
                f"{result['staging_stats']['total_bouts']} total bouts")
    
    return result

def validate_data():
    """Run validation checks."""
    logger.info("Running data validation...")
    
    # Run data validation only (no schema validation against frontend)
    report = run_validation()
    
    if report['summary']['failed'] > 0:
        logger.warning(f"Validation found {report['summary']['failed']} issues")
        for check in report['failed_checks'][:5]:  # Show first 5
            logger.warning(f"  - {check['name']}")
    else:
        logger.info("All validation checks passed")
    
    return report

def deploy_preview():
    """Deploy to preview environment."""
    logger.info("Deploying to preview environment...")
    result = deploy_to_preview()
    
    if result['success']:
        logger.info("Preview deployment successful")
    else:
        logger.error("Preview deployment failed")
    
    return result

def check_changes():
    """Check for changes in HTML content."""
    logger.info("Checking for changes in HTML content...")
    summary = run_change_detection(limit=50)
    
    logger.info(f"Checked {summary['checked']} URLs, found {summary['changed']} changes")
    
    return summary

def main():
    """Run the pipeline based on command line arguments."""
    parser = argparse.ArgumentParser(description='Boxing Data Pipeline')
    
    parser.add_argument('command', choices=[
        'setup', 'load', 'validate', 'schema-validate', 'deploy-preview', 
        'check-changes', 'full'
    ], help='Pipeline command to run')
    
    parser.add_argument('--limit', type=int, help='Limit number of records to process')
    parser.add_argument('--force', action='store_true',
                       help='Force production deployment without approval')
    
    args = parser.parse_args()
    
    logger.info(f"Starting pipeline command: {args.command}")
    start_time = datetime.now()
    
    try:
        if args.command == 'setup':
            success = setup_database()
            
        elif args.command == 'load':
            result = load_data(limit=args.limit)
            success = result['load_summary']['successful'] > 0
            
        elif args.command == 'validate':
            report = validate_data()
            success = report['summary']['failed'] == 0
            
        elif args.command == 'schema-validate':
            validator = SchemaValidator()
            success = validator.validate()
            
        elif args.command == 'deploy-preview':
            result = deploy_preview()
            success = result['success']
            
            
        elif args.command == 'check-changes':
            summary = check_changes()
            success = True
            
        elif args.command == 'full':
            # Run full pipeline
            logger.info("Running full pipeline...")
            
            # Setup
            if not setup_database():
                logger.error("Database setup failed, aborting")
                return 1
            
            # Load
            load_result = load_data(limit=args.limit)
            if load_result['load_summary']['successful'] == 0:
                logger.error("No data loaded, aborting")
                return 1
            
            # Validate
            validation = validate_data()
            if validation['summary']['failed'] > 0:
                logger.error("Validation failed, aborting")
                return 1
            
            # Deploy to preview
            preview_result = deploy_preview()
            if not preview_result['success']:
                logger.error("Preview deployment failed, aborting")
                return 1
            
            logger.info("Full pipeline completed successfully")
            success = True
        
        else:
            logger.error(f"Unknown command: {args.command}")
            success = False
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        
        if success:
            logger.info(f"Pipeline command '{args.command}' completed successfully in {duration:.1f}s")
            return 0
        else:
            logger.error(f"Pipeline command '{args.command}' failed after {duration:.1f}s")
            return 1
            
    except Exception as e:
        logger.exception(f"Pipeline error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())