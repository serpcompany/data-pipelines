#!/usr/bin/env python3
"""
Python wrapper for TypeScript schema validation.
Ensures staging mirror DB matches production schema using Drizzle ORM.
"""

import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from .fetch_production_schema import ProductionSchemaFetcher

logger = logging.getLogger(__name__)

class SchemaValidator:
    """Validates staging mirror database schema using TypeScript/Drizzle."""
    
    def __init__(self):
        self.database_dir = Path(__file__).parent.parent
        self.validator_script = self.database_dir / "validators" / "validate-schema.ts"
        self.report_path = self.database_dir / "validators" / "schema-validation-report.json"
        
    def run_validation(self) -> Tuple[bool, List[str]]:
        """Run the TypeScript validation script and return results."""
        try:
            # Change to database directory to run npm scripts
            logger.info("Running schema validation via TypeScript/Drizzle...")
            
            # First ensure dependencies are installed
            install_result = subprocess.run(
                ["npm", "install"],
                cwd=self.database_dir,
                capture_output=True,
                text=True
            )
            
            if install_result.returncode != 0:
                logger.warning(f"npm install warning: {install_result.stderr}")
            
            # Run the validation script
            result = subprocess.run(
                ["npm", "run", "validate:schema"],
                cwd=self.database_dir,
                capture_output=True,
                text=True
            )
            
            # The script exits with code 0 if valid, 1 if not
            is_valid = result.returncode == 0
            
            # Read the JSON report for details
            differences = []
            if self.report_path.exists():
                with open(self.report_path, 'r') as f:
                    report = json.load(f)
                    differences = report.get('differences', [])
            
            if is_valid:
                logger.info("✅ Schema validation PASSED")
            else:
                logger.error("❌ Schema validation FAILED")
                logger.error(f"Output: {result.stdout}")
                if result.stderr:
                    logger.error(f"Errors: {result.stderr}")
            
            return is_valid, differences
            
        except Exception as e:
            logger.error(f"Schema validation error: {e}")
            return False, [str(e)]
    
    def validate(self) -> bool:
        """Run validation and return boolean result."""
        is_valid, _ = self.run_validation()
        return is_valid
    
    def get_report(self) -> Optional[Dict]:
        """Get the latest validation report."""
        if self.report_path.exists():
            with open(self.report_path, 'r') as f:
                return json.load(f)
        return None
    
    def ensure_dependencies(self) -> bool:
        """Ensure Node.js dependencies are installed."""
        try:
            result = subprocess.run(
                ["npm", "install"],
                cwd=self.database_dir,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False


def validate_schema() -> bool:
    """Convenience function to run schema validation."""
    validator = SchemaValidator()
    return validator.validate()


def main():
    """Run schema validation as a standalone script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    validator = SchemaValidator()
    is_valid = validator.validate()
    
    # Print report details
    report = validator.get_report()
    if report:
        print(f"\nValidation Report:")
        print(f"Timestamp: {report.get('timestamp', 'N/A')}")
        print(f"Valid: {report.get('isValid', False)}")
        if report.get('differences'):
            print("\nDifferences:")
            for diff in report['differences']:
                print(f"  - {diff}")
    
    exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()