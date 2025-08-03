#!/usr/bin/env python3
"""
Master script to run the complete boxing data pipeline.
Coordinates all ETL steps from scraping to production deployment.
"""

import argparse
import logging
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from boxing.database.staging_mirror import get_staging_db
from boxing.database import run_change_detection
from boxing.load.to_staging_mirror_db import run_staging_load
from boxing.database.validators import run_validation
from boxing.database.validators.schema_validator import SchemaValidator
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
    
    # Validate schema matches production
    validator = SchemaValidator()
    if validator.validate():
        logger.info("Database setup complete and schema validated")
        return True
    else:
        logger.error("Database setup failed or schema validation failed")
        return False

def load_data(limit=None):
    """Load data from data lake to staging mirror."""
    logger.info("Loading data to staging mirror database...")
    result = run_staging_load(limit=limit)
    
    logger.info(f"Loaded {result['load_summary']['successful']} records successfully")
    logger.info(f"Staging stats: {result['staging_stats']['total_boxers']} boxers, "
                f"{result['staging_stats']['total_bouts']} bouts")
    
    return result

def run_tests(test_path=None, watch=False):
    """Run pytest tests for the pipeline."""
    logger.info("Running tests...")
    
    cmd = ["python", "-m", "pytest"]
    
    if test_path:
        cmd.append(test_path)
    else:
        cmd.append("tests/")
    
    cmd.extend(["-v", "--tb=short"])
    
    if watch:
        # Add pytest-watch for continuous testing
        cmd = ["python", "-m", "pytest-watch"] + cmd[3:]  # Skip 'python -m pytest'
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("All tests passed")
            return True
        else:
            logger.error(f"Tests failed:\n{result.stdout}")
            if result.stderr:
                logger.error(f"Errors:\n{result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run tests: {e}")
        return False

def validate_data():
    """Run validation checks."""
    logger.info("Running data validation...")
    
    # First validate schema
    logger.info("Validating database schema...")
    validator = SchemaValidator()
    schema_valid = validator.validate()
    
    if not schema_valid:
        logger.error("Schema validation failed - database schema does not match production")
        return {
            'summary': {'passed': 0, 'failed': 1, 'total': 1},
            'failed_checks': [{'name': 'Schema validation', 'error': 'Schema does not match production'}]
        }
    
    # Then run data validation
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
        'setup', 'load', 'test', 'validate', 'schema-validate', 'deploy-preview', 
        'check-changes', 'full', 'test-watch'
    ], help='Pipeline command to run')
    
    parser.add_argument('--limit', type=int, help='Limit number of records to process')
    parser.add_argument('--skip-validation', action='store_true', 
                       help='Skip validation checks during deployment')
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
            
        elif args.command == 'test':
            success = run_tests()
            
        elif args.command == 'test-watch':
            success = run_tests(watch=True)
            
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
            
            # Run tests after loading
            if not run_tests():
                logger.error("Tests failed after loading data")
                if not args.force:
                    return 1
            
            # Validate
            validation = validate_data()
            if validation['summary']['failed'] > 0 and not args.skip_validation:
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