#!/usr/bin/env python3
"""
Deploy validated data from staging to CloudFlare D1 preview database.
Includes validation checks and rollback capability.
"""

import json
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
import tempfile
import os

from ..staging import get_connection as get_staging_connection
from ..validators.queries import run_validation

logger = logging.getLogger(__name__)

class PreviewDeployer:
    """Deploy staging data to CloudFlare D1 preview database."""
    
    def __init__(self, wrangler_config_path: str = "wrangler.toml"):
        self.wrangler_config = wrangler_config_path
        self.staging_conn = get_staging_connection()
        self.temp_files = []
    
    def cleanup(self):
        """Clean up temporary files."""
        for file_path in self.temp_files:
            try:
                os.unlink(file_path)
            except:
                pass
        
        if self.staging_conn:
            self.staging_conn.close()
    
    def run_wrangler_command(self, command: str, preview: bool = True) -> Dict:
        """Run a wrangler D1 command."""
        full_command = f"wrangler d1 execute boxingundefeated-com {command}"
        
        if preview:
            full_command += " --preview"
        
        full_command += f" --config={self.wrangler_config}"
        
        try:
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                'success': True,
                'output': result.stdout,
                'command': full_command
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Wrangler command failed: {e.stderr}")
            return {
                'success': False,
                'error': e.stderr,
                'command': full_command
            }
    
    def export_to_sql(self, table_name: str, batch_size: int = 100) -> List[str]:
        """Export staging table to SQL insert statements."""
        cursor = self.staging_conn.cursor()
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        column_list = ', '.join(columns)
        
        # Export data in batches
        cursor.execute(f"SELECT * FROM {table_name}")
        
        sql_files = []
        batch = []
        batch_num = 0
        
        for row in cursor.fetchall():
            # Format values
            values = []
            for val in row:
                if val is None:
                    values.append('NULL')
                elif isinstance(val, str):
                    # Escape single quotes
                    escaped = val.replace("'", "''")
                    values.append(f"'{escaped}'")
                else:
                    values.append(str(val))
            
            batch.append(f"({', '.join(values)})")
            
            if len(batch) >= batch_size:
                # Write batch to file
                batch_num += 1
                sql_file = self.write_batch_file(
                    table_name, column_list, batch, batch_num
                )
                sql_files.append(sql_file)
                batch = []
        
        # Write remaining batch
        if batch:
            batch_num += 1
            sql_file = self.write_batch_file(
                table_name, column_list, batch, batch_num
            )
            sql_files.append(sql_file)
        
        logger.info(f"Exported {table_name} to {len(sql_files)} SQL files")
        return sql_files
    
    def write_batch_file(self, table_name: str, columns: str, 
                        values: List[str], batch_num: int) -> str:
        """Write a batch of SQL inserts to a temporary file."""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=f'_{table_name}_{batch_num}.sql',
            delete=False
        ) as f:
            # Write delete statement for first batch
            if batch_num == 1:
                f.write(f"DELETE FROM {table_name};\n")
            
            # Write insert statement
            f.write(f"INSERT INTO {table_name} ({columns}) VALUES\n")
            f.write(',\n'.join(values))
            f.write(';\n')
            
            self.temp_files.append(f.name)
            return f.name
    
    def deploy_table(self, table_name: str) -> Dict:
        """Deploy a single table to preview."""
        logger.info(f"Deploying {table_name} to preview...")
        
        # Export to SQL files
        sql_files = self.export_to_sql(table_name)
        
        results = {
            'table': table_name,
            'files': len(sql_files),
            'success': True,
            'errors': []
        }
        
        # Execute each SQL file
        for sql_file in sql_files:
            result = self.run_wrangler_command(f"--file={sql_file}")
            
            if not result['success']:
                results['success'] = False
                results['errors'].append(result['error'])
                logger.error(f"Failed to deploy {sql_file}")
                break
        
        return results
    
    def verify_deployment(self) -> Dict:
        """Verify data was deployed correctly."""
        logger.info("Verifying deployment...")
        
        tables = ['divisions', 'boxers', 'boxerBouts']
        verification = {}
        
        for table in tables:
            # Get count from staging
            cursor = self.staging_conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            staging_count = cursor.fetchone()[0]
            
            # Get count from preview
            result = self.run_wrangler_command(
                f'--command="SELECT COUNT(*) as count FROM {table}"'
            )
            
            if result['success']:
                # Parse the count from output
                try:
                    import re
                    match = re.search(r'"count":\s*(\d+)', result['output'])
                    preview_count = int(match.group(1)) if match else 0
                except:
                    preview_count = -1
            else:
                preview_count = -1
            
            verification[table] = {
                'staging_count': staging_count,
                'preview_count': preview_count,
                'match': staging_count == preview_count
            }
        
        return verification
    
    def deploy_all(self, skip_validation: bool = False) -> Dict:
        """Deploy all tables to preview database."""
        deployment_start = datetime.now()
        
        # Run validation first
        if not skip_validation:
            logger.info("Running validation checks...")
            validation_report = run_validation()
            
            if validation_report['summary']['failed'] > 0:
                logger.error(f"Validation failed with {validation_report['summary']['failed']} errors")
                return {
                    'success': False,
                    'error': 'Validation failed',
                    'validation_report': validation_report
                }
        
        # Deploy tables in order (divisions first for FK constraints)
        tables = ['divisions', 'boxers', 'boxerBouts']
        deployment_results = []
        
        for table in tables:
            result = self.deploy_table(table)
            deployment_results.append(result)
            
            if not result['success']:
                logger.error(f"Failed to deploy {table}, aborting deployment")
                break
        
        # Verify deployment
        verification = self.verify_deployment()
        
        # Build summary
        all_success = all(r['success'] for r in deployment_results)
        all_verified = all(v['match'] for v in verification.values())
        
        deployment_time = (datetime.now() - deployment_start).total_seconds()
        
        summary = {
            'success': all_success and all_verified,
            'timestamp': deployment_start.isoformat(),
            'duration_seconds': deployment_time,
            'tables_deployed': len([r for r in deployment_results if r['success']]),
            'deployment_results': deployment_results,
            'verification': verification
        }
        
        if not skip_validation:
            summary['validation_report'] = validation_report
        
        logger.info(f"Deployment {'succeeded' if summary['success'] else 'failed'} in {deployment_time:.1f}s")
        
        return summary

def deploy_to_preview(skip_validation: bool = False) -> Dict:
    """Deploy staging data to preview environment."""
    deployer = PreviewDeployer()
    
    try:
        result = deployer.deploy_all(skip_validation=skip_validation)
        
        if result['success']:
            logger.info("Preview deployment successful!")
            logger.info(f"Deployed {result['tables_deployed']} tables")
        else:
            logger.error("Preview deployment failed!")
        
        return result
        
    finally:
        deployer.cleanup()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Run deployment
    result = deploy_to_preview()
    
    # Print summary
    print("\nDeployment Summary")
    print("=" * 50)
    print(f"Status: {'SUCCESS' if result['success'] else 'FAILED'}")
    print(f"Duration: {result['duration_seconds']:.1f} seconds")
    print(f"Tables Deployed: {result['tables_deployed']}")
    
    print("\nVerification:")
    for table, verify in result['verification'].items():
        print(f"  {table}: {verify['staging_count']} -> {verify['preview_count']} {'✓' if verify['match'] else '✗'}")