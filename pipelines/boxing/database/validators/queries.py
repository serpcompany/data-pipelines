#!/usr/bin/env python3
"""
Bulk validation queries for data quality checks.
Ensures data integrity before deployment to production.
"""

import logging
from typing import Dict, List, Tuple
from datetime import datetime

from ..staging import get_connection as get_staging_connection

logger = logging.getLogger(__name__)

class DataValidator:
    """Run validation queries on staging data."""
    
    def __init__(self):
        self.conn = get_staging_connection()
        self.validation_results = []
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def run_query(self, name: str, query: str, 
                  expected_count: int = 0, 
                  check_type: str = 'count') -> Dict:
        """
        Run a validation query and check results.
        
        Args:
            name: Name of the validation check
            query: SQL query to run
            expected_count: Expected result count (0 for checks that should return no rows)
            check_type: 'count' or 'exists'
        
        Returns:
            Dict with validation results
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        
        if check_type == 'count':
            results = cursor.fetchall()
            count = len(results)
            passed = count == expected_count
            
            result = {
                'name': name,
                'query': query,
                'expected': expected_count,
                'actual': count,
                'passed': passed,
                'severity': 'error' if not passed else 'ok',
                'details': results[:5] if not passed else []  # First 5 problematic records
            }
        
        elif check_type == 'exists':
            result = cursor.fetchone()
            passed = result is not None and result[0] > 0
            
            result = {
                'name': name,
                'query': query,
                'passed': passed,
                'severity': 'error' if not passed else 'ok',
                'details': result
            }
        
        self.validation_results.append(result)
        return result
    
    def validate_required_fields(self) -> List[Dict]:
        """Validate that required fields are not null."""
        checks = []
        
        # Boxers table required fields
        checks.append(self.run_query(
            "Boxers without ID",
            "SELECT id, name FROM boxers WHERE id IS NULL",
            expected_count=0
        ))
        
        checks.append(self.run_query(
            "Boxers without name",
            "SELECT id, boxrecId FROM boxers WHERE name IS NULL OR name = ''",
            expected_count=0
        ))
        
        checks.append(self.run_query(
            "Boxers without BoxRec ID",
            "SELECT id, name FROM boxers WHERE boxrecId IS NULL OR boxrecId = ''",
            expected_count=0
        ))
        
        checks.append(self.run_query(
            "Boxers without URL",
            "SELECT id, name FROM boxers WHERE boxrecUrl IS NULL OR boxrecUrl = ''",
            expected_count=0
        ))
        
        # Bouts table required fields
        checks.append(self.run_query(
            "Bouts without boxer reference",
            "SELECT id FROM boxerBouts WHERE boxerId IS NULL",
            expected_count=0
        ))
        
        checks.append(self.run_query(
            "Bouts without opponent",
            "SELECT id, boxerId FROM boxerBouts WHERE opponent IS NULL OR opponent = ''",
            expected_count=0
        ))
        
        return checks
    
    def validate_data_integrity(self) -> List[Dict]:
        """Validate data integrity and relationships."""
        checks = []
        
        # Check for orphaned bouts
        checks.append(self.run_query(
            "Orphaned bouts (no matching boxer)",
            """
            SELECT bb.id, bb.boxerId 
            FROM boxerBouts bb
            LEFT JOIN boxers b ON bb.boxerId = b.id
            WHERE b.id IS NULL
            """,
            expected_count=0
        ))
        
        # Check for duplicate BoxRec IDs
        checks.append(self.run_query(
            "Duplicate BoxRec IDs",
            """
            SELECT boxrecId, COUNT(*) as count
            FROM boxers
            GROUP BY boxrecId
            HAVING COUNT(*) > 1
            """,
            expected_count=0
        ))
        
        # Check for duplicate slugs
        checks.append(self.run_query(
            "Duplicate slugs",
            """
            SELECT slug, COUNT(*) as count
            FROM boxers
            GROUP BY slug
            HAVING COUNT(*) > 1
            """,
            expected_count=0
        ))
        
        # Check bout counts match
        checks.append(self.run_query(
            "Boxers with mismatched bout counts",
            """
            SELECT b.id, b.name, b.proTotalBouts, COUNT(bb.id) as actual_bouts
            FROM boxers b
            LEFT JOIN boxerBouts bb ON b.id = bb.boxerId
            WHERE b.proTotalBouts IS NOT NULL
            GROUP BY b.id, b.name, b.proTotalBouts
            HAVING b.proTotalBouts != COUNT(bb.id)
            """,
            expected_count=0
        ))
        
        return checks
    
    def validate_data_quality(self) -> List[Dict]:
        """Validate data quality and completeness."""
        checks = []
        
        # Check for boxers with no bouts
        checks.append(self.run_query(
            "Active boxers with no bouts",
            """
            SELECT b.id, b.name, b.proStatus
            FROM boxers b
            LEFT JOIN boxerBouts bb ON b.id = bb.boxerId
            WHERE b.proStatus = 'active'
            AND bb.id IS NULL
            GROUP BY b.id, b.name, b.proStatus
            """,
            expected_count=0
        ))
        
        # Check for invalid dates
        checks.append(self.run_query(
            "Bouts with invalid dates",
            """
            SELECT id, date, opponent
            FROM boxerBouts
            WHERE date IS NOT NULL 
            AND (
                LENGTH(date) < 8 
                OR date NOT LIKE '____-__-__'
                OR date > date('now')
            )
            """,
            expected_count=0
        ))
        
        # Check for invalid results
        checks.append(self.run_query(
            "Bouts with invalid results",
            """
            SELECT id, result, opponent
            FROM boxerBouts
            WHERE result NOT IN ('W', 'L', 'D', 'NC', 'DQ', 'TD', 'RTD', 'ND')
            AND result IS NOT NULL
            """,
            expected_count=0
        ))
        
        # Check win/loss/draw totals
        checks.append(self.run_query(
            "Boxers with incorrect win totals",
            """
            SELECT b.id, b.name, b.proWins, COUNT(bb.id) as actual_wins
            FROM boxers b
            JOIN boxerBouts bb ON b.id = bb.boxerId
            WHERE bb.result = 'W'
            GROUP BY b.id, b.name, b.proWins
            HAVING b.proWins != COUNT(bb.id)
            """,
            expected_count=0
        ))
        
        return checks
    
    def validate_business_rules(self) -> List[Dict]:
        """Validate business logic rules."""
        checks = []
        
        # Check for reasonable height values
        checks.append(self.run_query(
            "Boxers with invalid height",
            """
            SELECT id, name, height
            FROM boxers
            WHERE height IS NOT NULL
            AND (
                CAST(height AS INTEGER) < 120  -- Less than 4 feet
                OR CAST(height AS INTEGER) > 250  -- More than 8 feet
            )
            """,
            expected_count=0
        ))
        
        # Check for reasonable weight classes
        checks.append(self.run_query(
            "Boxers in non-existent divisions",
            """
            SELECT DISTINCT b.proDivision
            FROM boxers b
            WHERE b.proDivision IS NOT NULL
            AND b.proDivision NOT IN (
                SELECT name FROM divisions
                UNION SELECT slug FROM divisions
                UNION SELECT shortName FROM divisions
            )
            """,
            expected_count=0
        ))
        
        # Check for future debut dates
        checks.append(self.run_query(
            "Boxers with future debut dates",
            """
            SELECT id, name, proDebutDate
            FROM boxers
            WHERE proDebutDate > date('now')
            """,
            expected_count=0
        ))
        
        return checks
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics for validation report."""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total records
        cursor.execute("SELECT COUNT(*) FROM boxers")
        stats['total_boxers'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM boxerBouts")
        stats['total_bouts'] = cursor.fetchone()[0]
        
        # Completeness metrics
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN dateOfBirth IS NOT NULL THEN 1 END) as with_dob,
                COUNT(CASE WHEN nationality IS NOT NULL THEN 1 END) as with_nationality,
                COUNT(CASE WHEN height IS NOT NULL THEN 1 END) as with_height,
                COUNT(CASE WHEN stance IS NOT NULL THEN 1 END) as with_stance
            FROM boxers
        """)
        completeness = cursor.fetchone()
        stats['completeness'] = {
            'date_of_birth': f"{completeness[0]}/{stats['total_boxers']}",
            'nationality': f"{completeness[1]}/{stats['total_boxers']}",
            'height': f"{completeness[2]}/{stats['total_boxers']}",
            'stance': f"{completeness[3]}/{stats['total_boxers']}"
        }
        
        return stats
    
    def run_all_validations(self) -> Dict:
        """Run all validation checks and return summary."""
        logger.info("Running all validation checks...")
        
        self.validation_results = []
        
        # Run all validation categories
        self.validate_required_fields()
        self.validate_data_integrity()
        self.validate_data_quality()
        self.validate_business_rules()
        
        # Count results
        total_checks = len(self.validation_results)
        passed_checks = sum(1 for r in self.validation_results if r['passed'])
        failed_checks = total_checks - passed_checks
        
        # Get summary stats
        stats = self.get_summary_stats()
        
        # Build report
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_checks': total_checks,
                'passed': passed_checks,
                'failed': failed_checks,
                'pass_rate': f"{(passed_checks/total_checks)*100:.1f}%" if total_checks > 0 else "N/A"
            },
            'statistics': stats,
            'failed_checks': [r for r in self.validation_results if not r['passed']],
            'all_results': self.validation_results
        }
        
        logger.info(f"Validation complete: {passed_checks}/{total_checks} passed")
        
        return report

def run_validation() -> Dict:
    """Run validation as a standalone process."""
    validator = DataValidator()
    
    try:
        report = validator.run_all_validations()
        
        # Log summary
        logger.info(f"Validation Summary: {report['summary']}")
        
        # Log failed checks
        if report['failed_checks']:
            logger.warning(f"Failed {len(report['failed_checks'])} validation checks:")
            for check in report['failed_checks']:
                logger.warning(f"  - {check['name']}: {check.get('actual', 'failed')}")
        
        return report
        
    finally:
        validator.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Run validation
    report = run_validation()
    
    # Print summary
    print("\nValidation Report")
    print("=" * 50)
    print(f"Total Checks: {report['summary']['total_checks']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Pass Rate: {report['summary']['pass_rate']}")
    
    if report['failed_checks']:
        print("\nFailed Checks:")
        for check in report['failed_checks']:
            print(f"\n- {check['name']}")
            if check.get('details'):
                print(f"  Found {check.get('actual', 'N/A')} issues")
                print(f"  First few: {check['details'][:3]}")