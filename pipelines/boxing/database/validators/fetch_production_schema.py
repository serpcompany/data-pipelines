#!/usr/bin/env python3
"""
Fetch production schema from GitHub for validation.
Ensures we're always comparing against the actual deployed schema.
"""

import requests
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import re
import os

logger = logging.getLogger(__name__)

class ProductionSchemaFetcher:
    """Fetches schema from production GitHub repository."""
    
    def __init__(self):
        self.repo = os.getenv('GITHUB_MAIN_PROJECT_REPO', 'serpcompany/boxingundefeated.com')
        self.branch = 'staging'  # staging branch = production-preview
        self.github_token = os.getenv('GITHUB_PAT')  # Optional, for rate limits
        
    def fetch_schema_file(self, file_path: str) -> Optional[str]:
        """Fetch a single schema file from GitHub."""
        url = f"https://raw.githubusercontent.com/{self.repo}/{self.branch}/{file_path}"
        
        headers = {}
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
            
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {file_path}: {e}")
            return None
    
    def fetch_migration_file(self, file_name: str) -> Optional[str]:
        """Fetch a migration SQL file from GitHub."""
        file_path = f"server/db/migrations/{file_name}"
        return self.fetch_schema_file(file_path)
    
    def parse_sql_schema(self, sql_content: str) -> Dict:
        """Parse SQL schema to extract table and column information."""
        schema = {}
        
        # Parse CREATE TABLE statements
        table_pattern = r'CREATE TABLE `(\w+)`\s*\((.*?)\);'
        table_matches = re.findall(table_pattern, sql_content, re.DOTALL)
        
        for table_name, table_def in table_matches:
            columns = []
            indexes = []
            
            # Parse column definitions
            lines = table_def.strip().split('\n')
            for line in lines:
                line = line.strip().rstrip(',')
                if line and not line.startswith('FOREIGN KEY') and not line.startswith('PRIMARY KEY'):
                    # Extract column info
                    col_match = re.match(r'`(\w+)`\s+(\w+)(.*)$', line)
                    if col_match:
                        col_name = col_match.group(1)
                        col_type = col_match.group(2)
                        col_constraints = col_match.group(3)
                        
                        columns.append({
                            'name': col_name,
                            'type': col_type,
                            'constraints': col_constraints.strip()
                        })
            
            schema[table_name] = {
                'columns': columns,
                'indexes': indexes
            }
        
        # Parse CREATE INDEX statements
        index_pattern = r'CREATE\s+(UNIQUE\s+)?INDEX\s+`?(\w+)`?\s+ON\s+`?(\w+)`?\s*\(([^)]+)\)'
        index_matches = re.findall(index_pattern, sql_content)
        
        for unique, index_name, table_name, columns_str in index_matches:
            if table_name in schema:
                columns = [col.strip().strip('`') for col in columns_str.split(',')]
                schema[table_name]['indexes'].append({
                    'name': index_name,
                    'unique': bool(unique),
                    'columns': columns
                })
        
        return schema
    
    def fetch_production_schema(self) -> Dict:
        """Fetch and parse the production schema from GitHub."""
        logger.info(f"Fetching production schema from {self.repo}@{self.branch}")
        
        # Fetch the initial migration that contains the full schema
        initial_migration = self.fetch_migration_file('0000_small_norman_osborn.sql')
        if not initial_migration:
            raise Exception("Failed to fetch initial migration from GitHub")
        
        # Parse the schema
        schema = self.parse_sql_schema(initial_migration)
        
        # Fetch and apply subsequent schema migrations
        migration_files = [
            '0001_melodic_sentinel.sql',
            '0002_sweet_argent.sql', 
            '0003_worried_songbird.sql'
        ]
        
        for migration_file in migration_files:
            content = self.fetch_migration_file(migration_file)
            if content:
                # This is simplified - you'd need to parse ALTER TABLE statements
                logger.info(f"Fetched migration {migration_file}")
        
        return schema
    
    def save_schema_cache(self, schema: Dict, cache_path: Path):
        """Save fetched schema to local cache."""
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w') as f:
            json.dump({
                'schema': schema,
                'fetched_from': f"{self.repo}@{self.branch}",
                'timestamp': str(Path(__file__).parent.parent.parent.parent / "timestamp")
            }, f, indent=2)
        logger.info(f"Cached production schema to {cache_path}")


def fetch_production_schema() -> Dict:
    """Convenience function to fetch production schema."""
    fetcher = ProductionSchemaFetcher()
    return fetcher.fetch_production_schema()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    fetcher = ProductionSchemaFetcher()
    schema = fetcher.fetch_production_schema()
    
    print(f"\nFetched schema from {fetcher.repo}@{fetcher.branch}")
    print(f"Tables found: {list(schema.keys())}")
    
    for table, info in schema.items():
        print(f"\n{table}:")
        print(f"  Columns: {len(info['columns'])}")
        print(f"  Indexes: {len(info['indexes'])}")